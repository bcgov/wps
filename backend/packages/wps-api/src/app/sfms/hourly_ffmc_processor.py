import logging
import os
import tempfile
from datetime import datetime, timedelta
from osgeo import gdal
from typing import List, cast

from wps_shared.sfms.rdps_filename_marshaller import model_run_for_hour

from wps_shared.geospatial.wps_dataset import WPSDataset
from app.jobs.rdps_sfms import MAX_MODEL_RUN_HOUR
from app.sfms.daily_fwi_processor import MultiDatasetContext
from app.sfms.fwi_processor import calculate_ffmc
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.utils.s3_client import S3Client


logger = logging.getLogger(__name__)


class HourlyFFMCProcessor:
    """
    Class for calculating/generating forecasted hourly FFMC rasters.
    """

    def __init__(self, start_datetime: datetime, addresser: RasterKeyAddresser):
        self.start_datetime = start_datetime
        self.addresser = addresser

    async def process(
        self,
        s3_client: S3Client,
        input_dataset_context: MultiDatasetContext,
        hours_to_process: int = MAX_MODEL_RUN_HOUR,
    ):
        set_s3_gdal_config()

        # hFFMC general process
        # 1. Cron job kicks off the job and we use current UTC time as start time
        # 2. Create HourlyFFMCProcessor with the start time and begin processing
        # 3. Use job start time to determine most recent RDPS model run start time (date and 00z or 12z)
        # 4. Use most recent RDPS model run start time to determine most recent hFFMC key to use as source which is always one hour before the RDPS start time (04 or 16 PDT)
        # 5. Start calculating hFFMC from model run hour 0 through to 47. Save the calculated hFFMCs to S3. Most recently calculated hFFMC is used as input to the next hour's hFFMC calculation.
        # 6. hFFMC rasters are saved to S3 with UTC based keys.

        # Determine most recent RDPS model run
        rdps_model_run_hour = model_run_for_hour(self.start_datetime.hour)
        rdps_model_run_start = datetime(
            year=self.start_datetime.year,
            month=self.start_datetime.month,
            day=self.start_datetime.day,
            hour=rdps_model_run_hour,
            tzinfo=self.start_datetime.tzinfo,
        )

        # Determine key to the initial/seed hFFMC from SFMS and check if it exists. Initial hffmc will be a 04 or 16 hour hffmc from SFMS.
        hffmc_key = self.addresser.get_uploaded_hffmc_key(rdps_model_run_start)
        hffmc_key_exists = await s3_client.all_objects_exist(hffmc_key)
        if not hffmc_key_exists:
            logger.warning(
                f"Missing initial hFFMC raster from SFMS for date {self.start_datetime}. Missing key is {hffmc_key}."
            )
            return

        for hour in range(0, hours_to_process):
            with tempfile.TemporaryDirectory() as temp_dir:
                # Get and check existence of weather s3 keys
                temp_key, rh_key, wind_speed_key, precip_key = (
                    self.addresser.get_weather_data_keys_hffmc(rdps_model_run_start, hour)
                )
                weather_keys_exist = await s3_client.all_objects_exist(
                    temp_key, rh_key, wind_speed_key, precip_key
                )
                if not weather_keys_exist:
                    logging.warning(
                        f"Missing weather keys for model run: {rdps_model_run_start} and hour {hour}"
                    )
                    break

                # Prefix our S3 keys for access via gdal
                temp_key, rh_key, wind_speed_key, precip_key, hffmc_key = (
                    self.addresser.gdal_prefix_keys(
                        temp_key, rh_key, wind_speed_key, precip_key, hffmc_key
                    )
                )
                with input_dataset_context(
                    [temp_key, rh_key, wind_speed_key, precip_key, hffmc_key]
                ) as input_datasets:
                    input_datasets = cast(
                        List[WPSDataset], input_datasets
                    )  # Ensure correct type inference
                    temp_ds, rh_ds, wind_speed_ds, precip_ds, hffmc_ds = input_datasets
                    # Warp weather datasets to match hffmc
                    warped_temp_ds = temp_ds.warp_to_match(
                        hffmc_ds,
                        f"{temp_dir}/{os.path.basename(temp_key)}.tif",
                        GDALResamplingMethod.BILINEAR,
                    )
                    warped_rh_ds = rh_ds.warp_to_match(
                        hffmc_ds,
                        f"{temp_dir}/{os.path.basename(rh_key)}.tif",
                        GDALResamplingMethod.BILINEAR,
                        max_value=100,
                    )
                    warped_wind_speed_ds = wind_speed_ds.warp_to_match(
                        hffmc_ds,
                        f"{temp_dir}/{os.path.basename(wind_speed_key)}.tif",
                        GDALResamplingMethod.BILINEAR,
                    )
                    warped_precip_ds = precip_ds.warp_to_match(
                        hffmc_ds,
                        f"{temp_dir}/{os.path.basename(precip_key)}.tif",
                        GDALResamplingMethod.BILINEAR,
                    )

                    # Create and store new hFFMC dataset
                    hffmc_values, hffmc_no_data_value = calculate_ffmc(
                        hffmc_ds,
                        warped_temp_ds,
                        warped_rh_ds,
                        warped_precip_ds,
                        warped_wind_speed_ds,
                    )
                    new_hffmc_datetime = rdps_model_run_start + timedelta(hours=hour)
                    hffmc_key = self.addresser.get_calculated_hffmc_index_key(new_hffmc_datetime)
                    hhfmc_cog_key = self.addresser.get_cog_key(hffmc_key)
                    geotransform = hffmc_ds.as_gdal_ds().GetGeoTransform()
                    projection = hffmc_ds.as_gdal_ds().GetProjection()
                    hffmc_ds.close()
                    await s3_client.persist_raster_data(
                        temp_dir,
                        hffmc_key,
                        hhfmc_cog_key,
                        geotransform,
                        projection,
                        hffmc_values,
                        hffmc_no_data_value,
                    )
                    # Clear gdal virtual file system cache of S3 metadata in order to allow newly uploaded hffmc rasters to be opened immediately.
                    gdal.VSICurlClearCache()
