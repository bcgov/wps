import asyncio
import logging
import os
from contextlib import ExitStack
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

import numpy as np
from aiobotocore.client import AioBaseClient

from app import configure_logging
from app.geospatial.wps_dataset import WPSDataset
from app.sfms.raster_addresser import FWIParameter, RasterKeyAddresser
from app.sfms.raster_processor import calculate_bui, calculate_dc, calculate_dmc
from app.utils.geospatial import GDALResamplingMethod, export_to_geotiff
from app.utils.s3 import all_objects_exist, get_client, set_s3_gdal_config
from app.utils.time import get_utc_now

logger = logging.getLogger(__name__)


class BUIDateRangeProcessor:
    """
    Encapsulates logic for iterating over a date range and performing some unit of work.
    """

    def __init__(self, start_datetime: datetime, days: int):
        self.start_datetime = start_datetime
        self.days = days

    async def process_bui(self):
        raster_addresser = RasterKeyAddresser()
        set_s3_gdal_config()

        async with get_client() as (client, bucket):
            for day in range(self.days):
                datetime_to_calculate_utc = self.start_datetime.replace(hour=20, minute=0, second=0, microsecond=0) + timedelta(days=day)
                previous_fwi_datetime = datetime_to_calculate_utc - timedelta(days=1)
                prediction_hour = 20 + (day * 24)
                logger.info(f"Calculating DMC/DC/BUI for {datetime_to_calculate_utc.isoformat()}")

                temp_key, rh_key, _, precip_key = raster_addresser.get_weather_data_keys(self.start_datetime, datetime_to_calculate_utc, prediction_hour)

                weather_keys_exist = await all_objects_exist(temp_key, rh_key, precip_key)

                if not weather_keys_exist:
                    break

                dc_key = raster_addresser.get_calculated_index_key(previous_fwi_datetime, FWIParameter.DC)
                dmc_key = raster_addresser.get_calculated_index_key(previous_fwi_datetime, FWIParameter.DMC)

                fwi_keys_exist = await all_objects_exist(dc_key, dmc_key)

                if not fwi_keys_exist:
                    dc_key = raster_addresser.get_uploaded_index_key(self.start_datetime, FWIParameter.DC)
                    dmc_key = raster_addresser.get_uploaded_index_key(self.start_datetime, FWIParameter.DMC)

                    fwi_keys_exist = await all_objects_exist(dc_key, dmc_key)

                    if not fwi_keys_exist:
                        break

                temp_key, rh_key, precip_key = raster_addresser.gdal_prefix_keys(temp_key, rh_key, precip_key)
                dc_key, dmc_key = raster_addresser.gdal_prefix_keys(dc_key, dmc_key)

                with ExitStack() as stack:
                    temp_dir = stack.enter_context(TemporaryDirectory())
                    # Open datasets within the context manager
                    temp_ds = stack.enter_context(WPSDataset(temp_key))
                    rh_ds = stack.enter_context(WPSDataset(rh_key))
                    precip_ds = stack.enter_context(WPSDataset(precip_key))
                    dc_ds = stack.enter_context(WPSDataset(dc_key))
                    dmc_ds = stack.enter_context(WPSDataset(dmc_key))

                    # Warp datasets
                    warped_temp_ds = stack.enter_context(temp_ds.warp_to_match(dmc_ds, f"{temp_dir}/{os.path.basename(temp_key)}", GDALResamplingMethod.BILINEAR))
                    warped_rh_ds = stack.enter_context(rh_ds.warp_to_match(dmc_ds, f"{temp_dir}/{os.path.basename(rh_key)}", GDALResamplingMethod.BILINEAR))
                    warped_precip_ds = stack.enter_context(precip_ds.warp_to_match(dmc_ds, f"{temp_dir}/{os.path.basename(precip_key)}", GDALResamplingMethod.BILINEAR))

                    latitude_array = dmc_ds.generate_latitude_array()
                    month_array = np.full(latitude_array.shape, datetime_to_calculate_utc.month)

                    dc_values, dc_nodata_value = calculate_dc(dc_ds, warped_temp_ds, warped_rh_ds, warped_precip_ds, latitude_array, month_array)
                    dmc_values, dmc_nodata_value = calculate_dmc(dmc_ds, warped_temp_ds, warped_rh_ds, warped_precip_ds, latitude_array, month_array)

                    # Create and store DMC dataset
                    new_dmc_key = raster_addresser.get_calculated_index_key(datetime_to_calculate_utc, FWIParameter.DMC)
                    new_dmc_path = await self.create_and_store_dataset(
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
                    new_dc_key = raster_addresser.get_calculated_index_key(datetime_to_calculate_utc, FWIParameter.DC)
                    new_dc_path = await self.create_and_store_dataset(
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
                    new_bui_key = raster_addresser.get_calculated_index_key(datetime_to_calculate_utc, FWIParameter.BUI)

                    new_dmc_ds = stack.enter_context(WPSDataset(new_dmc_path))
                    new_dc_ds = stack.enter_context(WPSDataset(new_dc_path))

                    bui_values, nodata = calculate_bui(new_dmc_ds, new_dc_ds)

                    # Store the new BUI dataset
                    await self.create_and_store_dataset(
                        temp_dir,
                        client,
                        bucket,
                        new_bui_key,
                        dmc_ds.as_gdal_ds().GetGeoTransform(),
                        dmc_ds.as_gdal_ds().GetProjection(),
                        bui_values,
                        nodata,
                    )

    async def create_and_store_dataset(self, temp_dir: str, client: AioBaseClient, bucket: str, key: str, transform, projection, values, no_data_value):
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
