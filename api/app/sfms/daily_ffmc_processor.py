import os
import logging
import tempfile
from typing import Callable, List, Iterator, cast
from datetime import datetime, timedelta
from app.auto_spatial_advisory.run_type import RunType
from app.geospatial.wps_dataset import WPSDataset
from app.sfms.fwi_processor import calculate_ffmc
from app.sfms.raster_addresser import RasterKeyAddresser, WeatherParameter
from app.utils.geospatial import GDALResamplingMethod
from app.utils.s3_client import S3Client

logger = logging.getLogger(__name__)

DAILY_FFMC_DAYS = 2

MultiDatasetContext = Callable[[List[str]], Iterator[List["WPSDataset"]]]


class DailyFFMCProcessor:
    """
    Class for calculating/generating forecasted daily FFMC rasters for a date range
    """

    def __init__(self, start_datetime: datetime, addresser: RasterKeyAddresser):
        self.start_datetime = start_datetime
        self.addresser = addresser

    async def process_daily_ffmc(self, s3_client: S3Client, input_dataset_context: MultiDatasetContext):
        for day in range(DAILY_FFMC_DAYS):
            current_day = self.start_datetime + timedelta(days=day)
            yesterday = current_day - timedelta(days=1)
            yesterday_ffmc_key = self.addresser.get_daily_ffmc(yesterday, RunType.ACTUAL)
            if s3_client.all_objects_exist(yesterday_ffmc_key) == False:
                yesterday_ffmc_key = self.addresser.get_calculated_daily_ffmc(yesterday)

            if s3_client.all_objects_exist(yesterday_ffmc_key) == False:
                logging.warning(f"No ffmc objects found for key: {yesterday_ffmc_key}")
                return

            temp_forecast_key = self.addresser.get_daily_model_data_key(current_day, RunType.FORECAST, WeatherParameter.TEMP)
            rh_forecast_key = self.addresser.get_daily_model_data_key(current_day, RunType.FORECAST, WeatherParameter.RH)
            precip_forecast_key = self.addresser.get_daily_model_data_key(current_day, RunType.FORECAST, WeatherParameter.PRECIP)
            wind_speed_forecast_key = self.addresser.get_daily_model_data_key(current_day, RunType.FORECAST, WeatherParameter.WIND_SPEED)

            with tempfile.TemporaryDirectory() as temp_dir:
                with input_dataset_context([yesterday_ffmc_key, temp_forecast_key, rh_forecast_key, precip_forecast_key, wind_speed_forecast_key]) as input_datasets:
                    input_datasets = cast(List[WPSDataset], input_datasets)  # Ensure correct type inference
                    yesterday_ffmc_ds, temp_forecast_ds, rh_forecast_ds, precip_forecast_ds, wind_speed_forecast_ds = input_datasets

                    # Warp weather datasets to match ffmc
                    warped_temp_ds = temp_forecast_ds.warp_to_match(yesterday_ffmc_ds, f"{temp_dir}/{os.path.basename(temp_forecast_key)}", GDALResamplingMethod.BILINEAR)
                    warped_rh_ds = rh_forecast_ds.warp_to_match(yesterday_ffmc_ds, f"{temp_dir}/{os.path.basename(rh_forecast_key)}", GDALResamplingMethod.BILINEAR)
                    warped_precip_ds = yesterday_ffmc_ds.warp_to_match(precip_forecast_ds, f"{temp_dir}/{os.path.basename(precip_forecast_key)}", GDALResamplingMethod.BILINEAR)
                    warped_wind_speed_ds = yesterday_ffmc_ds.warp_to_match(
                        wind_speed_forecast_ds, f"{temp_dir}/{os.path.basename(wind_speed_forecast_key)}", GDALResamplingMethod.BILINEAR
                    )

                    temp_forecast_ds.close()
                    rh_forecast_ds.close()
                    precip_forecast_ds.close()
                    wind_speed_forecast_ds.close()

                    ffmc_values, ffmc_no_data_value = calculate_ffmc(yesterday_ffmc_ds, warped_temp_ds, warped_rh_ds, warped_precip_ds, warped_wind_speed_ds)

                    today_ffmc_key = self.addresser.get_calculated_daily_ffmc(current_day)
                    s3_client.persist_raster_data(
                        temp_dir, today_ffmc_key, yesterday_ffmc_ds.as_gdal_ds().GetGeoTransform(), yesterday_ffmc_ds.as_gdal_ds().GetProjection(), ffmc_values, ffmc_no_data_value
                    )
