import enum
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple

from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import (
    BaseRasterAddresser,
    FWIParameter,
    SFMSInterpolatedWeatherParameter,
)
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import assert_all_utc, convert_to_sfms_timezone, convert_utc_to_pdt
from wps_shared.weather_models import ModelEnum
from wps_shared.weather_models.rdps import RDPSKeyAddresser

logger = logging.getLogger(__name__)


class WeatherParameter(enum.Enum):
    TEMP = "temp"
    RH = "rh"
    WIND_SPEED = "wind_speed"


class RasterKeyAddresser(BaseRasterAddresser):
    """
    Encapsulates logic for addressing model and weather data rasters stored in object storage.
    """

    def __init__(self):
        super().__init__()
        self.rdps = RDPSKeyAddresser()
        self.sfms_calculated_prefix = "sfms/calculated"
        self.sfms_hourly_upload_prefix = "sfms/uploads/hourlies"
        self.sfms_daily_upload_prefix = "sfms/uploads/actual"
        self.weather_model_prefix = f"weather_models/{ModelEnum.RDPS.lower()}"

    def get_uploaded_index_key(self, datetime: datetime, fwi_param: FWIParameter):
        sfms_datetime = convert_to_sfms_timezone(datetime)
        iso_date = sfms_datetime.date().isoformat()
        return f"{self.sfms_daily_upload_prefix}/{iso_date}/{fwi_param.value}{iso_date.replace('-', '')}.tif"

    def get_calculated_index_key(
        self, datetime_utc: datetime, fwi_param: FWIParameter, run_type: RunType = RunType.FORECAST
    ):
        """
        Generates the calculated fire weather index key that points to the associated raster artifact in the object store.

        :param datetime_utc: UTC datetime the calculated raster is for
        :param fwi_param: the fire weather index caller is interested in
        :param run_type: RunType.FORECAST for RDPS-based forecasts, RunType.ACTUAL for station-interpolated actuals
        :return: the key to the raster artifact in object storage
        """
        assert_all_utc(datetime_utc)
        return f"{self.sfms_calculated_prefix}/{run_type.value}/{datetime_utc.date().isoformat()}/{fwi_param.value}{datetime_utc.date().isoformat().replace('-', '')}.tif"

    def get_model_data_key(
        self, start_time_utc: datetime, prediction_hour: int, weather_param: WeatherParameter
    ):
        """
        Generates the model data key that points to the associated raster artifact in the object store.
        The model is always assumed to be RDPS.

        :param start_time_utc: UTC date time when the model run started
        :param prediction_hour: the prediction hour offset from the start time
        """
        assert_all_utc(start_time_utc)
        weather_model_date_prefix = (
            f"{self.weather_model_prefix}/{start_time_utc.date().isoformat()}/"
        )
        return os.path.join(
            weather_model_date_prefix,
            self.rdps.compose_rdps_key(
                start_time_utc, start_time_utc.hour, prediction_hour, weather_param.value
            ),
        )

    def get_calculated_precip_key(self, datetime_to_calculate_utc: datetime):
        """
        Generates the calculated precip key that points to the associated raster artifact in the object store.
        The model is always assumed to be RDPS.

        :param datetime_to_calculate_utc: UTC datetime the calculated raster is for
        :return: the calculated precip key to the raster artifact in object storage
        """
        assert_all_utc(datetime_to_calculate_utc)
        calculated_weather_prefix = (
            f"{self.weather_model_prefix}/{datetime_to_calculate_utc.date().isoformat()}/"
        )
        return os.path.join(
            calculated_weather_prefix, self.rdps.compose_computed_precip_rdps_key(datetime_to_calculate_utc)
        )

    def get_weather_data_keys(
        self, start_time_utc: datetime, datetime_to_calculate_utc: datetime, prediction_hour: int
    ):
        """
        Generates all model data keys that point to their associated raster artifacts in the object store.

        :param start_time_utc: UTC date time when the model run started
        :param datetime_to_calculate_utc: UTC datetime the calculated raster is for
        :param prediction_hour: the prediction hour offset from the start time
        :return: temp, rh, wind speed and precip model data key
        """
        assert_all_utc(start_time_utc, datetime_to_calculate_utc)
        non_precip_keys = tuple(
            [
                self.get_model_data_key(start_time_utc, prediction_hour, param)
                for param in WeatherParameter
            ]
        )
        precip_key = self.get_calculated_precip_key(datetime_to_calculate_utc)
        all_weather_data_keys = non_precip_keys + (precip_key,)

        return all_weather_data_keys

    def get_weather_data_keys_legacy(self, start_time_utc: datetime, prediction_hour: int):
        """Legacy-format weather keys for S3 fallback during 7-day transition."""
        assert_all_utc(start_time_utc)
        weather_model_date_prefix = (
            f"{self.weather_model_prefix}/{start_time_utc.date().isoformat()}/"
        )
        return tuple(
            os.path.join(
                weather_model_date_prefix,
                self.rdps.compose_rdps_key_legacy(
                    start_time_utc, start_time_utc.hour, prediction_hour, param.value
                ),
            )
            for param in WeatherParameter
        )

    def get_uploaded_hffmc_key(self, datetime_utc: datetime):
        """
        Given the start time of an RDPS model run, return a key to the most recent hFFMC raster which will be
        equivalent to RDPS model run start time minus one hour in PDT. Note that the hFFMC rasters are stored according
        to PDT times. hFFMC keys will end with 04 or 16 for their hour.

        :param datetime_utc: The RDPS model run start date and time.
        :return: A key to the most recent hFFMC raster.
        """
        assert_all_utc(datetime_utc)

        # Convert utc into pdt and substract one hour to get hFFMC source raster time. sfms only produces hFFMC from Apr - Oct which is always PDT
        datetime_pdt = convert_utc_to_pdt(datetime_utc) - timedelta(hours=1)
        iso_date = datetime_pdt.date().isoformat()
        return f"{self.sfms_hourly_upload_prefix}/{iso_date}/fine_fuel_moisture_code{iso_date.replace('-', '')}{datetime_pdt.hour:02d}.tif"

    def get_weather_data_keys_hffmc(self, rdps_model_run_start: datetime, offset_hour):
        """
        Gets temp, rh, wind speed and calculated accumulated precip for the specified RDPS model run start date and hour.

        :param rdps_model_run_start: The RDPS model run start date and time.
        :param offset_hour: The hour offset from the RDPS model run start hour.
        :return: Keys to rasters in S3 storage for temp, rh, wind speed and calculated precip rasters.
        """
        assert_all_utc(rdps_model_run_start)
        non_precip_keys = tuple(
            self.get_model_data_key_hffmc(rdps_model_run_start, offset_hour, param)
            for param in WeatherParameter
        )
        datetime_to_calculate_utc = rdps_model_run_start + timedelta(hours=offset_hour)
        precip_key = self.get_calculated_precip_key(datetime_to_calculate_utc)
        all_weather_data_keys = non_precip_keys + (precip_key,)
        return all_weather_data_keys

    def get_weather_data_keys_hffmc_legacy(self, rdps_model_run_start: datetime, offset_hour: int):
        """Legacy-format hffmc weather keys for S3 fallback during 7-day transition."""
        assert_all_utc(rdps_model_run_start)
        weather_model_date_prefix = (
            f"{self.weather_model_prefix}/{rdps_model_run_start.date().isoformat()}/"
        )
        return tuple(
            os.path.join(
                weather_model_date_prefix,
                self.rdps.compose_rdps_key_hffmc_legacy(rdps_model_run_start, offset_hour, param.value),
            )
            for param in WeatherParameter
        )

    def get_model_data_key_hffmc(
        self, rdps_model_run_start: datetime, offset_hour: int, weather_param: WeatherParameter
    ):
        """
        Gets a S3 key for the weather parameter of interest for the specified RDPS model run start date and time at the provided offset.

        :param rdps_model_run_start: The RDPS model run start date and time.
        :param offset_hour: The hour offset from the RDPS model run start hour.
        :param weather_param: The weather parameter of interest (temp, rh, or wind speed).
        :return: A key to a raster in S3 storage.
        """
        assert_all_utc(rdps_model_run_start)
        weather_model_date_prefix = (
            f"{self.weather_model_prefix}/{rdps_model_run_start.date().isoformat()}/"
        )
        return os.path.join(
            weather_model_date_prefix,
            self.rdps.compose_rdps_key_hffmc(rdps_model_run_start, offset_hour, weather_param.value),
        )

    def get_calculated_hffmc_index_key(self, datetime_utc: datetime):
        """
        Given a UTC datetime return a calculated key based on PDT time as hFFMC rasters are named according to PDT.

        :param datetime_utc: A UTC datetime.
        :return: An S3 key for hFFMC using PDT time.
        """
        assert_all_utc(datetime_utc)
        iso_date = datetime_utc.date().isoformat()
        weather_param_prefix = "fine_fuel_moisture_code"
        return f"{self.sfms_calculated_prefix}/hourlies/{iso_date}/{weather_param_prefix}{iso_date.replace('-', '')}{datetime_utc.hour:02d}.tif"

    def get_interpolated_key(
        self, datetime_utc: datetime, weather_param: SFMSInterpolatedWeatherParameter
    ):
        """
        Generate S3 key for interpolated weather parameter raster with hierarchical date structure.

        Format: sfms/interpolated/{param}/YYYY/MM/DD/{param}_YYYYMMDD.tif

        :param datetime_utc: UTC datetime for the raster
        :param weather_param: Weather parameter (TEMP, RH, WIND_SPEED, PRECIP)
        :return: S3 key path
        """
        assert_all_utc(datetime_utc)
        date = datetime_utc.date()
        year = date.year
        month = date.month
        day = date.day
        date_str = date.isoformat().replace("-", "")
        param_value = weather_param.value

        return f"sfms/interpolated/{param_value}/{year:04d}/{month:02d}/{day:02d}/{param_value}_{date_str}.tif"

    async def resolve_weather_data_keys(
        self,
        s3_client: S3Client,
        start_time_utc: datetime,
        datetime_to_calculate_utc: datetime,
        prediction_hour: int,
    ) -> Optional[Tuple[str, str, str, str]]:
        """
        Return (temp_key, rh_key, wind_speed_key, precip_key) using new-format keys if present in S3,
        falling back to legacy CMC_reg keys for temp/rh/wind_speed. precip_key is always the
        computed .tif, which is unaffected by the filename migration.

        Returns None if neither new nor legacy weather keys exist.
        """
        temp_key, rh_key, wind_speed_key, precip_key = self.get_weather_data_keys(
            start_time_utc, datetime_to_calculate_utc, prediction_hour
        )
        if await s3_client.all_objects_exist(temp_key, rh_key, wind_speed_key, precip_key):
            logger.info("All weather data keys exist from new RDPS service")
            return temp_key, rh_key, wind_speed_key, precip_key

        logger.info("Falling back to legacy weather data keys")
        legacy_keys = self.get_weather_data_keys_legacy(start_time_utc, prediction_hour)
        if await s3_client.all_objects_exist(*legacy_keys):
            temp_key, rh_key, wind_speed_key = legacy_keys
            return temp_key, rh_key, wind_speed_key, precip_key

        logger.error("Weather data keys are missing")
        return None

    async def resolve_weather_data_keys_hffmc(
        self,
        s3_client: S3Client,
        rdps_model_run_start: datetime,
        offset_hour: int,
    ) -> Optional[Tuple[str, str, str, str]]:
        """
        Return (temp_key, rh_key, wind_speed_key, precip_key) using new-format hffmc keys if present
        in S3, falling back to legacy CMC_reg keys for temp/rh/wind_speed. precip_key is always the
        computed .tif, which is unaffected by the filename migration.

        Returns None if neither new nor legacy weather keys exist.
        """
        temp_key, rh_key, wind_speed_key, precip_key = self.get_weather_data_keys_hffmc(
            rdps_model_run_start, offset_hour
        )
        if await s3_client.all_objects_exist(temp_key, rh_key, wind_speed_key, precip_key):
            return temp_key, rh_key, wind_speed_key, precip_key

        legacy_keys = self.get_weather_data_keys_hffmc_legacy(rdps_model_run_start, offset_hour)
        if await s3_client.all_objects_exist(*legacy_keys):
            temp_key, rh_key, wind_speed_key = legacy_keys
            return temp_key, rh_key, wind_speed_key, precip_key

        return None
