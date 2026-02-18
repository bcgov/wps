import os
import enum
from datetime import datetime, timedelta
from wps_shared import config
from wps_shared.utils.time import convert_to_sfms_timezone, convert_utc_to_pdt
from wps_shared.utils.time import assert_all_utc
from wps_shared.weather_models import ModelEnum
from wps_shared.sfms.rdps_filename_marshaller import (
    compose_computed_precip_rdps_key,
    compose_rdps_key,
    compose_rdps_key_hffmc,
)


class SFMSInterpolatedWeatherParameter(enum.Enum):
    TEMP = "temp"
    RH = "rh"
    WIND_SPEED = "wind_speed"
    PRECIP = "precip"
    FFMC = "ffmc"
    DMC = "dmc"
    DC = "dc"


class WeatherParameter(enum.Enum):
    TEMP = "temp"
    RH = "rh"
    WIND_SPEED = "wind_speed"


class FWIParameter(enum.Enum):
    DC = "dc"
    DMC = "dmc"
    BUI = "bui"
    FFMC = "ffmc"
    ISI = "isi"
    FWI = "fwi"


class RasterKeyAddresser:
    """
    Encapsulates logic for addressing model and weather data rasters stored in object storage.
    """

    def __init__(self):
        self.sfms_calculated_prefix = "sfms/calculated"
        self.s3_prefix = f"/vsis3/{config.get('OBJECT_STORE_BUCKET')}"
        self.sfms_hourly_upload_prefix = "sfms/uploads/hourlies"
        self.sfms_daily_upload_prefix = "sfms/uploads/actual"
        self.sfms_fuel_raster_prefix = "sfms/static/fuel"
        self.weather_model_prefix = f"weather_models/{ModelEnum.RDPS.lower()}"

    def get_fuel_raster_key(self, datetime_utc: datetime, version: int):
        """
        returns fuel raster object storage key based on format:
            sfms/static/yyyy/fbpyyyy_v{x}.tif

            where
                bucket: the object storage bucket
                yyyy: the year
                x: the raster tif version number

        :param datetime_utc: the current UTC datetime
        :param version: the version of the fuel raster file desired
        :return: the fuel raster key
        """
        assert_all_utc(datetime_utc)
        year = datetime_utc.year
        return f"{self.sfms_fuel_raster_prefix}/{year}/fbp{year}_v{version}.tif"

    def get_unprocessed_fuel_raster_key(self, object_name: str):
        """
        returns the unprocessed fuel raster object storage key based on format:
            sfms/static/{object_name}

        :param object_name: the object file name including extension
        :return: the unprocessed fuel raster key at sfms/static
        """
        return f"sfms/static/{object_name}"

    def get_uploaded_index_key(self, datetime: datetime, fwi_param: FWIParameter):
        sfms_datetime = convert_to_sfms_timezone(datetime)
        iso_date = sfms_datetime.date().isoformat()
        return f"{self.sfms_daily_upload_prefix}/{iso_date}/{fwi_param.value}{iso_date.replace('-', '')}.tif"

    def get_calculated_index_key(self, datetime_utc: datetime, fwi_param: FWIParameter, run_type: str = "forecast"):
        """
        Generates the calculated fire weather index key that points to the associated raster artifact in the object store.

        :param datetime_utc: UTC datetime the calculated raster is for
        :param fwi_param: the fire weather index caller is interested in
        :param run_type: "forecast" for RDPS-based forecasts, "actual" for station-interpolated actuals
        :return: the key to the raster artifact in object storage
        """
        assert_all_utc(datetime_utc)
        return f"{self.sfms_calculated_prefix}/{run_type}/{datetime_utc.date().isoformat()}/{fwi_param.value}{datetime_utc.date().isoformat().replace('-', '')}.tif"

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
            compose_rdps_key(
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
            calculated_weather_prefix, compose_computed_precip_rdps_key(datetime_to_calculate_utc)
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

    def gdal_prefix_keys(self, *keys):
        """
        Prefix keys with vsis3/{bucket} for reading from s3 with gdal. GDAL s3 config must be setup for these
        paths to work with GDAL. Can be set using app/utils/s3.set_s3_gdal_config()

        :return: A tuple of all strings provided, prefixed with vsis3/{bucket}
        """
        return tuple(f"{self.s3_prefix}/{key}" for key in keys)

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
            compose_rdps_key_hffmc(rdps_model_run_start, offset_hour, weather_param.value),
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

    def get_cog_key(self, key: str):
        """
        Given an existing key, replace extension with _cog.tif and prefix with vsis3 for gdal

        :param key: a key with a .tif extension
        """
        assert key.endswith(".tif"), f"Expected .tif file path, got {key}"
        cog_key = self.s3_prefix + "/" + key.removesuffix(".tif") + "_cog.tif"
        return cog_key

    def get_interpolated_key(
        self, datetime_utc: datetime, weather_param: SFMSInterpolatedWeatherParameter
    ):
        """
        Generate S3 key for interpolated weather parameter raster with hierarchical date structure.

        Format: sfms/interpolated/{param}/YYYY/MM/DD/{param}_YYYYMMDD.tif

        Examples:
            - Temperature: sfms/interpolated/temp/2024/01/15/temp_20240115.tif
            - Relative Humidity: sfms/interpolated/rh/2024/01/15/rh_20240115.tif
            - Wind Speed: sfms/interpolated/wind_speed/2024/01/15/wind_speed_20240115.tif

        :param datetime_utc: UTC datetime for the raster
        :param weather_param: Weather parameter (TEMP, RH, WIND_SPEED. PRECIP)
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

    def get_dem_key(self) -> str:
        """
        Get the GDAL virtual file system path to the DEM raster.

        :return: GDAL virtual file system path to DEM
        """
        return f"{self.s3_prefix}/sfms/static/bc_elevation.tif"

    def get_mask_key(self) -> str:
        """
        Get the GDAL virtual file system path to the BC mask raster.

        :return: GDAL virtual file system path to BC mask
        """
        return f"{self.s3_prefix}/sfms/static/bc_mask.tif"
