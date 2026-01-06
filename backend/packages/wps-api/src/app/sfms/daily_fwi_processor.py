import logging
import os
import tempfile
from datetime import datetime, timedelta
from typing import Callable, Iterator, List, Tuple, cast

import numpy as np

from wps_shared.geospatial.wps_dataset import WPSDataset
from app.sfms.fwi_processor import (
    calculate_bui,
    calculate_dc,
    calculate_dmc,
    calculate_ffmc,
    calculate_fwi,
    calculate_isi,
)
from wps_shared.geospatial.cog import warp_to_cog
from wps_shared.sfms.raster_addresser import FWIParameter, RasterKeyAddresser
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client
from wps_shared.sfms.rdps_filename_marshaller import model_run_for_hour

logger = logging.getLogger(__name__)

# Type alias for clarity: the context manager function signature
MultiDatasetContext = Callable[[List[str]], Iterator[List["WPSDataset"]]]


class DailyFWIProcessor:
    """
    Class for calculating/generating forecasted daily FWI rasters for a date range
    """

    def __init__(self, start_datetime: datetime, days: int, addresser: RasterKeyAddresser):
        self.start_datetime = start_datetime
        self.days = days
        self.addresser = addresser

    async def process(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        new_dmc_dc_context: MultiDatasetContext,
        new_ffmc_context: MultiDatasetContext,
        new_isi_bui_context: MultiDatasetContext,
        new_fwi_context: MultiDatasetContext,
    ):
        set_s3_gdal_config()

        for day in range(self.days):
            datetime_to_calculate_utc, previous_fwi_datetime, prediction_hour = (
                self._get_calculate_dates(day)
            )
            logger.info(
                f"Calculating daily FWI rasters for {datetime_to_calculate_utc.isoformat()}"
            )

            # Get and check existence of weather s3 keys
            temp_key, rh_key, wind_speed_key, precip_key = self.addresser.get_weather_data_keys(
                self.start_datetime, datetime_to_calculate_utc, prediction_hour
            )
            weather_keys_exist = await s3_client.all_objects_exist(
                temp_key, rh_key, wind_speed_key, precip_key
            )
            if not weather_keys_exist:
                logging.warning(
                    f"Missing weather keys for {model_run_for_hour(self.start_datetime.hour):02} model run"
                )
                break
            logger.info(
                f"Found weather keys: {'\n'.join([temp_key, rh_key, wind_speed_key, precip_key])}"
            )

            # get and check existence of fwi s3 keys
            dc_key, dmc_key, ffmc_key = self._get_previous_fwi_keys(day, previous_fwi_datetime)
            fwi_keys_exist = await s3_client.all_objects_exist(dc_key, dmc_key)
            if not fwi_keys_exist:
                logging.warning(
                    f"No previous DMC/DC/FFMC keys found for {previous_fwi_datetime.date().isoformat()}"
                )
                break
            logger.info(f"Found FWI keys: {'\n'.join([dc_key, dmc_key, ffmc_key])}")

            temp_key, rh_key, wind_speed_key, precip_key, ffmc_key = (
                self.addresser.gdal_prefix_keys(
                    temp_key, rh_key, wind_speed_key, precip_key, ffmc_key
                )
            )
            dc_key, dmc_key = self.addresser.gdal_prefix_keys(dc_key, dmc_key)

            with tempfile.TemporaryDirectory() as temp_dir:
                with input_dataset_context(
                    [temp_key, rh_key, wind_speed_key, precip_key, dc_key, dmc_key, ffmc_key]
                ) as input_datasets:
                    input_datasets = cast(
                        List[WPSDataset], input_datasets
                    )  # Ensure correct type inference
                    temp_ds, rh_ds, wind_speed_ds, precip_ds, dc_ds, dmc_ds, ffmc_ds = (
                        input_datasets
                    )

                    # Warp weather datasets to match fwi
                    warped_temp_ds = temp_ds.warp_to_match(
                        dmc_ds,
                        f"{temp_dir}/{os.path.basename(temp_key)}.tif",
                        GDALResamplingMethod.BILINEAR,
                    )
                    warped_rh_ds = rh_ds.warp_to_match(
                        dmc_ds,
                        f"{temp_dir}/{os.path.basename(rh_key)}.tif",
                        GDALResamplingMethod.BILINEAR,
                        max_value=100,
                    )
                    warped_wind_speed_ds = wind_speed_ds.warp_to_match(
                        dmc_ds,
                        f"{temp_dir}/{os.path.basename(wind_speed_key)}.tif",
                        GDALResamplingMethod.BILINEAR,
                    )
                    warped_precip_ds = precip_ds.warp_to_match(
                        dmc_ds,
                        f"{temp_dir}/{os.path.basename(precip_key)}.tif",
                        GDALResamplingMethod.BILINEAR,
                    )

                    # close unneeded datasets to reduce memory usage
                    precip_ds.close()
                    rh_ds.close()
                    temp_ds.close()
                    wind_speed_ds.close()
                    # Create latitude and month arrays needed for calculations
                    latitude_array = dmc_ds.generate_latitude_array()
                    month_array = np.full(latitude_array.shape, datetime_to_calculate_utc.month)

                    # Create and store DMC dataset
                    dmc_values, dmc_nodata_value = calculate_dmc(
                        dmc_ds,
                        warped_temp_ds,
                        warped_rh_ds,
                        warped_precip_ds,
                        latitude_array,
                        month_array,
                    )
                    new_dmc_key = self.addresser.get_calculated_index_key(
                        datetime_to_calculate_utc, FWIParameter.DMC
                    )
                    new_dmc_cog_key = self.addresser.get_cog_key(new_dmc_key)
                    new_dmc_path = await s3_client.persist_raster_data(
                        temp_dir,
                        new_dmc_key,
                        dmc_ds.as_gdal_ds().GetGeoTransform(),
                        dmc_ds.as_gdal_ds().GetProjection(),
                        dmc_values,
                        dmc_nodata_value,
                    )
                    # new_dmc_cog_key has vsis3 prefix so gdal stores it for us
                    warp_to_cog(src_ds=dmc_ds.as_gdal_ds(), output_path=new_dmc_cog_key)

                    # Create and store DC dataset
                    dc_values, dc_nodata_value = calculate_dc(
                        dc_ds,
                        warped_temp_ds,
                        warped_rh_ds,
                        warped_precip_ds,
                        latitude_array,
                        month_array,
                    )
                    new_dc_key = self.addresser.get_calculated_index_key(
                        datetime_to_calculate_utc, FWIParameter.DC
                    )
                    new_dc_cog_key = self.addresser.get_cog_key(new_dc_key)
                    new_dc_path = await s3_client.persist_raster_data(
                        temp_dir,
                        new_dc_key,
                        dc_ds.as_gdal_ds().GetGeoTransform(),
                        dc_ds.as_gdal_ds().GetProjection(),
                        dc_values,
                        dc_nodata_value,
                    )
                    # new_dc_cog_key has vsis3 prefix so gdal stores it for us
                    warp_to_cog(src_ds=dc_ds.as_gdal_ds(), output_path=new_dc_cog_key)

                    # Create and store FFMC dataset
                    ffmc_values, ffmc_no_data_value = calculate_ffmc(
                        ffmc_ds,
                        warped_temp_ds,
                        warped_rh_ds,
                        warped_precip_ds,
                        warped_wind_speed_ds,
                    )
                    new_ffmc_key = self.addresser.get_calculated_index_key(
                        datetime_to_calculate_utc, FWIParameter.FFMC
                    )
                    new_ffmc_cog_key = self.addresser.get_cog_key(new_ffmc_key)
                    new_ffmc_path = await s3_client.persist_raster_data(
                        temp_dir,
                        new_ffmc_key,
                        dc_ds.as_gdal_ds().GetGeoTransform(),
                        dc_ds.as_gdal_ds().GetProjection(),
                        ffmc_values,
                        ffmc_no_data_value,
                    )

                    # new_ffmc_cog_key has vsis3 prefix so gdal stores it for us
                    warp_to_cog(src_ds=ffmc_ds.as_gdal_ds(), output_path=new_ffmc_cog_key)

                    # Open new DMC and DC datasets and calculate BUI
                    new_bui_key = self.addresser.get_calculated_index_key(
                        datetime_to_calculate_utc, FWIParameter.BUI
                    )
                    new_bui_cog_key = self.addresser.get_cog_key(new_bui_key)
                    with new_dmc_dc_context([new_dmc_path, new_dc_path]) as new_dmc_dc_datasets:
                        new_ds = cast(
                            List[WPSDataset], new_dmc_dc_datasets
                        )  # Ensure correct type inference
                        new_dmc_ds, new_dc_ds = new_ds
                        bui_values, bui_nodata = calculate_bui(new_dmc_ds, new_dc_ds)

                        # Store the new BUI dataset
                        new_bui_path = await s3_client.persist_raster_data(
                            temp_dir,
                            new_bui_key,
                            dmc_ds.as_gdal_ds().GetGeoTransform(),
                            dmc_ds.as_gdal_ds().GetProjection(),
                            bui_values,
                            bui_nodata,
                        )

                    # Open new FFMC dataset and calculate ISI
                    new_isi_key = self.addresser.get_calculated_index_key(
                        datetime_to_calculate_utc, FWIParameter.ISI
                    )
                    new_isi_cog_key = self.addresser.get_cog_key(new_isi_key)
                    with new_ffmc_context([new_ffmc_path]) as new_ffmc_dataset_context:
                        new_ffmc_ds = cast(List[WPSDataset], new_ffmc_dataset_context)[
                            0
                        ]  # Ensure correct type inference

                        isi_values, isi_nodata = calculate_isi(new_ffmc_ds, warped_wind_speed_ds)

                        # Store the new ISI dataset
                        new_isi_path = await s3_client.persist_raster_data(
                            temp_dir,
                            new_isi_key,
                            new_ffmc_ds.as_gdal_ds().GetGeoTransform(),
                            new_ffmc_ds.as_gdal_ds().GetProjection(),
                            isi_values,
                            isi_nodata,
                        )

                    # Open new ISI and BUI datasets to calculate FWI
                    new_fwi_key = self.addresser.get_calculated_index_key(
                        datetime_to_calculate_utc, FWIParameter.FWI
                    )
                    new_fwi_cog_key = self.addresser.get_cog_key(new_fwi_key)
                    with new_isi_bui_context([new_isi_path, new_bui_path]) as new_isi_bui_datasets:
                        new_ds = cast(
                            List[WPSDataset], new_isi_bui_datasets
                        )  # Ensure correct type inference
                        new_isi_ds, new_bui_ds = new_ds

                        fwi_values, fwi_nodata = calculate_fwi(new_isi_ds, new_bui_ds)

                        new_fwi_path = await s3_client.persist_raster_data(
                            temp_dir,
                            new_fwi_key,
                            new_isi_ds.as_gdal_ds().GetGeoTransform(),
                            new_isi_ds.as_gdal_ds().GetProjection(),
                            fwi_values,
                            fwi_nodata,
                        )

                        # warp and store new bui and isi datasets since they're open now
                        warp_to_cog(src_ds=new_bui_ds.as_gdal_ds(), output_path=new_bui_cog_key)
                        warp_to_cog(src_ds=new_isi_ds.as_gdal_ds(), output_path=new_isi_cog_key)
                        with new_fwi_context([new_fwi_path]) as new_fwi_dataset_context:
                            new_fwi_ds = cast(List[WPSDataset], new_fwi_dataset_context)[
                                0
                            ]  # Ensure correct type inference
                            warp_to_cog(src_ds=new_fwi_ds.as_gdal_ds(), output_path=new_fwi_cog_key)

    def _get_calculate_dates(self, day: int):
        """
        Calculate the UTC date and times based on the provided day offset.

        :param day: The day offset from the start date
        :return: Tuple of (datetime_to_calculate_utc, previous_fwi_datetime, prediction_hour)
        """
        datetime_to_calculate_utc = self.start_datetime.replace(
            hour=20, minute=0, second=0, microsecond=0
        ) + timedelta(days=day)
        previous_fwi_datetime = datetime_to_calculate_utc - timedelta(days=1)
        prediction_hour = 20 + (day * 24)
        return datetime_to_calculate_utc, previous_fwi_datetime, prediction_hour

    def _get_previous_fwi_keys(
        self, day_to_calculate: int, previous_fwi_datetime: datetime
    ) -> Tuple[str, str]:
        """
        Based on the day being calculated, decide whether to use previously uploaded actuals from sfms or
        calculated indices from the previous day's calculations.

        :param day_to_calculate: day of the calculation loop
        :param previous_fwi_datetime: the datetime previous to the datetime being calculated
        :return: s3 keys for dc and dmc
        """
        if (
            day_to_calculate == 0
        ):  # if we're running the first day of the calculation, use previously uploaded actuals
            dc_key = self.addresser.get_uploaded_index_key(previous_fwi_datetime, FWIParameter.DC)
            dmc_key = self.addresser.get_uploaded_index_key(previous_fwi_datetime, FWIParameter.DMC)
            ffmc_key = self.addresser.get_uploaded_index_key(
                previous_fwi_datetime, FWIParameter.FFMC
            )
        else:  # otherwise use the last calculated key
            dc_key = self.addresser.get_calculated_index_key(previous_fwi_datetime, FWIParameter.DC)
            dmc_key = self.addresser.get_calculated_index_key(
                previous_fwi_datetime, FWIParameter.DMC
            )
            ffmc_key = self.addresser.get_calculated_index_key(
                previous_fwi_datetime, FWIParameter.FFMC
            )

        return dc_key, dmc_key, ffmc_key
