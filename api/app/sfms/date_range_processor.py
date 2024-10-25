import asyncio
import logging
import os
from contextlib import ExitStack
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory
from typing import Tuple

import numpy as np
from aiobotocore.client import AioBaseClient

from app import configure_logging
from app.geospatial.wps_dataset import WPSDataset
from app.sfms.raster_addresser import FWIParameter, RasterKeyAddresser
from app.sfms.fwi_processor import calculate_bui, calculate_dc, calculate_dmc
from app.utils.geospatial import GDALResamplingMethod, export_to_geotiff
from app.utils.s3 import all_objects_exist, get_client, set_s3_gdal_config
from app.utils.time import get_utc_now
from app.weather_models.rdps_filename_marshaller import model_run_for_hour

logger = logging.getLogger(__name__)


class BUIDateRangeProcessor:
    """
    Class for calculating/generating forecasted DMC/DC/BUI rasters for a date range
    """

    def __init__(self, start_datetime: datetime, days: int):
        self.start_datetime = start_datetime
        self.days = days
        self.addresser = RasterKeyAddresser()

    async def process_bui(self):
        set_s3_gdal_config()

        async with get_client() as (client, bucket):
            for day in range(self.days):
                datetime_to_calculate_utc = self.start_datetime.replace(hour=20, minute=0, second=0, microsecond=0) + timedelta(days=day)
                previous_fwi_datetime = datetime_to_calculate_utc - timedelta(days=1)
                prediction_hour = 20 + (day * 24)
                logger.info(f"Calculating DMC/DC/BUI for {datetime_to_calculate_utc.isoformat()}")

                # Get and check existence of weather s3 keys
                temp_key, rh_key, _, precip_key = self.addresser.get_weather_data_keys(self.start_datetime, datetime_to_calculate_utc, prediction_hour)
                weather_keys_exist = await all_objects_exist(temp_key, rh_key, precip_key)
                if not weather_keys_exist:
                    logging.warning(f"No weather keys found for {model_run_for_hour(self.start_datetime.hour):02} model run")
                    break

                # get and check existence of fwi s3 keys
                dc_key, dmc_key = self._get_previous_fwi_keys(day, previous_fwi_datetime)
                fwi_keys_exist = await all_objects_exist(dc_key, dmc_key)
                if not fwi_keys_exist:
                    logging.warning(f"No previous DMC/DC keys found for {previous_fwi_datetime.date().isoformat()}")
                    break

                temp_key, rh_key, precip_key = self.addresser.gdal_prefix_keys(temp_key, rh_key, precip_key)
                dc_key, dmc_key = self.addresser.gdal_prefix_keys(dc_key, dmc_key)

                with ExitStack() as stack:
                    temp_dir = stack.enter_context(TemporaryDirectory())
                    # Open datasets within the context manager
                    dc_ds, dmc_ds, warped_temp_ds, warped_rh_ds, warped_precip_ds = self._open_and_warp_bui_datasets(stack, temp_dir, dc_key, dmc_key, temp_key, rh_key, precip_key)

                    # Create latitude and month arrays needed for calculations
                    latitude_array = dmc_ds.generate_latitude_array()
                    month_array = np.full(latitude_array.shape, datetime_to_calculate_utc.month)

                    # Create and store DMC dataset
                    dmc_values, dmc_nodata_value = calculate_dmc(dmc_ds, warped_temp_ds, warped_rh_ds, warped_precip_ds, latitude_array, month_array)
                    new_dmc_key = self.addresser.get_calculated_index_key(datetime_to_calculate_utc, FWIParameter.DMC)
                    new_dmc_path = await self._create_and_store_dataset(
                        temp_dir,
                        client,
                        bucket,
                        new_dmc_key,
                        dmc_ds.as_gdal_ds().GetGeoTransform(),
                        dmc_ds.as_gdal_ds().GetProjection(),
                        dmc_values,
                        dmc_nodata_value,
                    )

                    # Create and store DC dataset
                    dc_values, dc_nodata_value = calculate_dc(dc_ds, warped_temp_ds, warped_rh_ds, warped_precip_ds, latitude_array, month_array)
                    new_dc_key = self.addresser.get_calculated_index_key(datetime_to_calculate_utc, FWIParameter.DC)
                    new_dc_path = await self._create_and_store_dataset(
                        temp_dir,
                        client,
                        bucket,
                        new_dc_key,
                        dc_ds.as_gdal_ds().GetGeoTransform(),
                        dc_ds.as_gdal_ds().GetProjection(),
                        dc_values,
                        dc_nodata_value,
                    )

                    # Open new DMC and DC datasets and calculate BUI
                    new_bui_key = self.addresser.get_calculated_index_key(datetime_to_calculate_utc, FWIParameter.BUI)
                    new_dmc_ds = stack.enter_context(WPSDataset(new_dmc_path))
                    new_dc_ds = stack.enter_context(WPSDataset(new_dc_path))

                    bui_values, nodata = calculate_bui(new_dmc_ds, new_dc_ds)

                    # Store the new BUI dataset
                    await self._create_and_store_dataset(
                        temp_dir,
                        client,
                        bucket,
                        new_bui_key,
                        dmc_ds.as_gdal_ds().GetGeoTransform(),
                        dmc_ds.as_gdal_ds().GetProjection(),
                        bui_values,
                        nodata,
                    )

    def _get_previous_fwi_keys(self, day_to_calculate: int, previous_fwi_datetime: datetime) -> Tuple[str, str]:
        """
        Based on the day being calculated, decide whether to use previously uploaded actuals from sfms or
        calculated indices from the previous day's calculations.

        :param day_to_calculate: day of the calculation loop
        :param previous_fwi_datetime: the datetime previous to the datetime being calculated
        :return: s3 keys for dc and dmc
        """
        if day_to_calculate == 0:  # if we're running the first day of the calculation, use previously uploaded actuals
            dc_key = self.addresser.get_uploaded_index_key(previous_fwi_datetime, FWIParameter.DC)
            dmc_key = self.addresser.get_uploaded_index_key(previous_fwi_datetime, FWIParameter.DMC)
        else:  # otherwise use the last calculated key
            dc_key = self.addresser.get_calculated_index_key(previous_fwi_datetime, FWIParameter.DC)
            dmc_key = self.addresser.get_calculated_index_key(previous_fwi_datetime, FWIParameter.DMC)
        return dc_key, dmc_key

    def _open_and_warp_bui_datasets(self, stack: ExitStack, temp_dir: TemporaryDirectory, dc_key: str, dmc_key: str, temp_key: str, rh_key: str, precip_key: str):
        """
        Open WPSDatasets used to calculate BUI within a context manager, while transforming weather datasets to match the fwi indices datasets

        :param stack: context manager ExitStack
        :param temp_dir: a temporary directory to store warped datasets in
        :param dc_key: key to tif file in s3
        :param dmc_key: key to tif file in s3
        :param temp_key: key to tif file in s3
        :param rh_key: key to tif file in s3
        :param precip_key: key to tif file in s3
        :return: Opened WPSDatasets (DC, DMC, Temp, RH, Precip)
        """
        temp_ds = stack.enter_context(WPSDataset(temp_key))
        rh_ds = stack.enter_context(WPSDataset(rh_key))
        precip_ds = stack.enter_context(WPSDataset(precip_key))
        dc_ds = stack.enter_context(WPSDataset(dc_key))
        dmc_ds = stack.enter_context(WPSDataset(dmc_key))

        # Warp weather datasets to match fwi
        warped_temp_ds = stack.enter_context(temp_ds.warp_to_match(dmc_ds, f"{temp_dir}/{os.path.basename(temp_key)}", GDALResamplingMethod.BILINEAR))
        warped_rh_ds = stack.enter_context(rh_ds.warp_to_match(dmc_ds, f"{temp_dir}/{os.path.basename(rh_key)}", GDALResamplingMethod.BILINEAR))
        warped_precip_ds = stack.enter_context(precip_ds.warp_to_match(dmc_ds, f"{temp_dir}/{os.path.basename(precip_key)}", GDALResamplingMethod.BILINEAR))

        # close unneeded datasets to reduce memory usage
        precip_ds.close()
        rh_ds.close()
        temp_ds.close()

        return dc_ds, dmc_ds, warped_temp_ds, warped_rh_ds, warped_precip_ds

    async def _create_and_store_dataset(self, temp_dir: str, client: AioBaseClient, bucket: str, key: str, transform, projection, values, no_data_value) -> str:
        """
        Creates a geotiff to temporarily store and write to s3.

        :param temp_dir: temporary directory to write geotiff
        :param client: async s3 client
        :param bucket: s3 bucket name
        :param key: s3 key to store output dataset
        :param transform: gdal geotransform
        :param projection: gdal projection
        :param values: array of values
        :param no_data_value: array no data value
        :return: path to temporary written geotiff file
        """
        temp_geotiff = os.path.join(temp_dir, os.path.basename(key))
        export_to_geotiff(values, temp_geotiff, transform, projection, no_data_value)

        logger.info(f"Writing to s3 -- {key}")
        await client.put_object(Bucket=bucket, Key=key, Body=open(temp_geotiff, "rb"))

        return temp_geotiff


async def main():
    start_time = get_utc_now()
    days = 2

    processor = BUIDateRangeProcessor(start_time, days)
    await processor.process_bui()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(main())
