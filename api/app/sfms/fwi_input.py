import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

from osgeo import gdal
from zoneinfo import ZoneInfo

from app import config
from app.utils.geospatial import warp_to_match_raster, GDALResamplingMethod
from app.utils.s3 import all_objects_exist
from app.weather_models import ModelEnum
from app.weather_models.rdps_filename_marshaller import compose_computed_precip_rdps_key, compose_rdps_key, model_run_for_hour

gdal.UseExceptions()
logger = logging.getLogger(__name__)

BUCKET = config.get("OBJECT_STORE_BUCKET")


class FWIKeyFetcher:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.sfms_upload_prefix = "sfms/uploads/actual/"

    def determine_last_fwi_date(self, datetime: datetime):
        local_datetime = datetime.astimezone(ZoneInfo("America/Vancouver"))  # sfms is currently uploaded according to local time
        day_of_last_actual = (local_datetime - timedelta(days=1)).date()

        if local_datetime.hour > 18:  # if the local time is after 6:00pm, we should have today's actuals
            day_of_last_actual = local_datetime.date()

        return day_of_last_actual

    def get_previous_dmc_key(self, date: datetime):
        day_of_last_actual = self.determine_last_fwi_date(date)

        dmc_key = os.path.join(self.sfms_upload_prefix, f"{day_of_last_actual}/dmc{day_of_last_actual.isoformat().replace('-', '')}.tif")

        return dmc_key

    def get_previous_dc_key(self, date: datetime):
        day_of_last_actual = self.determine_last_fwi_date(date)

        dc_key = os.path.join(self.sfms_upload_prefix, f"{day_of_last_actual}/dc{day_of_last_actual.isoformat().replace('-', '')}.tif")

        return dc_key

    def get_weather_data_keys(self, model_start_time_utc: datetime, datetime_to_calculate_utc: datetime, prediction_hour: int):
        temp_key, rh_key, wind_spd_key = self.get_model_data_keys(model_start_time_utc, prediction_hour)
        precip_key = self.get_calculated_precip_key(datetime_to_calculate_utc)

        return temp_key, rh_key, wind_spd_key, precip_key

    def get_model_data_keys(self, model_start_time_utc: datetime, prediction_hour: int):
        weather_model_prefix = f"weather_models/{ModelEnum.RDPS.lower()}/{model_start_time_utc.date().isoformat()}/"

        temp_key = os.path.join(weather_model_prefix, compose_rdps_key(model_start_time_utc, model_start_time_utc.hour, prediction_hour, "temp"))
        rh_key = os.path.join(weather_model_prefix, compose_rdps_key(model_start_time_utc, model_start_time_utc.hour, prediction_hour, "rh"))
        wind_spd_key = os.path.join(weather_model_prefix, compose_rdps_key(model_start_time_utc, model_start_time_utc.hour, prediction_hour, "wind_speed"))

        return temp_key, rh_key, wind_spd_key

    def get_calculated_precip_key(self, datetime_to_calculate_utc: datetime):
        calculated_weather_prefix = f"weather_models/{ModelEnum.RDPS.lower()}/{datetime_to_calculate_utc.date().isoformat()}/"

        precip_key = os.path.join(calculated_weather_prefix, compose_computed_precip_rdps_key(datetime_to_calculate_utc))

        return precip_key


@dataclass
class FWIInput:
    start_time_utc: datetime
    prediction_hour: int = 20
    datetime_to_calculate_utc: datetime = field(init=False)
    model_run_hour: int = field(init=False)
    dmc_key: str = field(init=False)
    dc_key: str = field(init=False)
    # ffmc_key: str = field(init=False) # TODO
    temp_key: str = field(init=False)
    rh_key: str = field(init=False)
    wind_spd_key: str = field(init=False)
    precip_key: str = field(init=False)
    s3_keys_exist: bool = field(init=False, default=False)
    s3_key_fetcher: FWIKeyFetcher = field(init=False)

    def __post_init__(self):
        self.datetime_to_calculate_utc = self.start_time_utc.replace(hour=20)
        self.model_run_hour = model_run_for_hour(self.start_time_utc.hour)

        self.s3_key_fetcher = FWIKeyFetcher(BUCKET)

        self._initialize_fwi_keys()
        self._set_weather_model_keys()

    def _set_weather_model_keys(self):
        """Set all weather S3 keys."""
        self.temp_key, self.rh_key, self.wind_spd_key = self.s3_key_fetcher.get_model_data_keys(self.start_time_utc, self.prediction_hour)
        self.precip_key = self.s3_key_fetcher.get_calculated_precip_key(self.datetime_to_calculate_utc)

    def _initialize_fwi_keys(self):
        self.dmc_key = self.s3_key_fetcher.get_previous_dmc_key(self.start_time_utc)
        self.dc_key = self.s3_key_fetcher.get_previous_dc_key(self.start_time_utc)

    def increment_day(self, previously_calculated_dmc: str, previously_calculated_dc: str):
        """Move to the next day and update keys accordingly."""
        self.dmc_key = previously_calculated_dmc
        self.dc_key = previously_calculated_dc

        self.datetime_to_calculate_utc += timedelta(days=1)
        self.prediction_hour += 24
        self._set_weather_model_keys()

    async def check_keys_exist(self):
        """Asynchronously check if all keys exist."""
        self.s3_keys_exist = await all_objects_exist(self.dmc_key, self.dc_key, self.temp_key, self.rh_key, self.wind_spd_key, self.precip_key)
        return self.s3_keys_exist

    def _get_gdal_s3_paths(self):
        """Generate the S3 paths for all relevant weather data."""
        s3_prefix = f"/vsis3/{BUCKET}"
        dmc_s3 = os.path.join(s3_prefix, self.dmc_key)
        dc_s3 = os.path.join(s3_prefix, self.dc_key)
        temp_s3 = os.path.join(s3_prefix, self.temp_key)
        rh_s3 = os.path.join(s3_prefix, self.rh_key)
        precip_s3 = os.path.join(s3_prefix, self.precip_key)
        return dmc_s3, dc_s3, temp_s3, rh_s3, precip_s3

    def _open_weather_gdal_datasets(self):
        """Open the GDAL datasets for all required weather data."""
        _, _, temp_s3, rh_s3, precip_s3 = self._get_gdal_s3_paths()

        temp_ds = gdal.Open(temp_s3)
        rh_ds = gdal.Open(rh_s3)
        precip_ds = gdal.Open(precip_s3)

        return temp_ds, rh_ds, precip_ds

    def open_fwi_datasets(self) -> tuple[gdal.Dataset, gdal.Dataset]:
        dmc_s3, dc_s3, *_ = self._get_gdal_s3_paths()

        prev_dmc_ds = gdal.Open(dmc_s3)
        prev_dc_ds = gdal.Open(dc_s3)

        return prev_dmc_ds, prev_dc_ds

    def warp_weather_to_match_fwi(self, fwi_dataset: gdal.Dataset):
        """Process and warp the datasets to match the reference dataset."""
        with TemporaryDirectory() as tempdir:
            temp_ds, rh_ds, precip_ds = self._open_weather_gdal_datasets()

            warped_temp_path = os.path.join(tempdir, f"warp_{os.path.basename(self.temp_key)}")
            warped_rh_path = os.path.join(tempdir, f"warp_{os.path.basename(self.rh_key)}")
            warped_precip_path = os.path.join(tempdir, f"warp_{os.path.basename(self.precip_key)}")

            transformed_temp_ds = warp_to_match_raster(temp_ds, fwi_dataset, warped_temp_path, GDALResamplingMethod.BILINEAR)
            transformed_rh_ds = warp_to_match_raster(rh_ds, fwi_dataset, warped_rh_path, GDALResamplingMethod.BILINEAR)
            transformed_precip_ds = warp_to_match_raster(precip_ds, fwi_dataset, warped_precip_path, GDALResamplingMethod.BILINEAR)

            temp_ds = None
            rh_ds = None
            precip_ds = None

            return transformed_temp_ds, transformed_rh_ds, transformed_precip_ds
