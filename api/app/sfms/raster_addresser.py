import os
import enum
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from app import config
from app.weather_models import ModelEnum
from app.weather_models.rdps_filename_marshaller import compose_computed_precip_rdps_key, compose_rdps_key, model_run_for_hour


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


def assert_all_utc(*datetimes: datetime):
    for dt in datetimes:
        assert dt.tzinfo is not None, f"{dt} must be timezone-aware."
        assert dt.tzinfo == timezone.utc or dt.tzinfo == ZoneInfo("UTC"), f"{dt} is not in UTC."


class RasterKeyAddresser:
    """
    Encapsulates logic for addressing model and weather data rasters stored in object storage.
    """

    def __init__(self):
        self.sfms_calculated_prefix = "sfms/calculated"
        self.s3_prefix = f"/vsis3/{config.get('OBJECT_STORE_BUCKET')}"
        self.sfms_upload_prefix = "sfms/uploads/actual"
        self.weather_model_prefix = f"weather_models/{ModelEnum.RDPS.lower()}"

    def get_uploaded_index_key(self, datetime_utc: datetime, fwi_param: FWIParameter):
        assert_all_utc(datetime_utc)
        iso_date = datetime_utc.date().isoformat()

        return f"{self.sfms_upload_prefix}/{iso_date}/{fwi_param.value}{iso_date.replace('-', '')}.tif"

    def get_calculated_index_key(self, datetime_utc: datetime, fwi_param: FWIParameter):
        """
        Generates the calculated fire weather index key that points to the associated raster artifact in the object store.
        A calculated index is always generated for a future date, so always considered to be a forecast.

        :param datetime_utc: UTC datetime the calculated raster is for
        :param index: the fire weather index caller is interested in
        :return: the key to the raster artifact in object storage
        """
        assert_all_utc(datetime_utc)
        return f"{self.sfms_calculated_prefix}/forecast/{datetime_utc.date().isoformat()}/{fwi_param.value}{datetime_utc.date().isoformat().replace('-', '')}.tif"

    def get_model_data_key(self, start_time_utc: datetime, prediction_hour: int, weather_param: WeatherParameter):
        """
        Generates the model data key that points to the associated raster artifact in the object store.
        The model is always assumed to be RDPS.

        :param start_time_utc: UTC date time when the model run started
        :param prediction_hour: the prediction hour offset from the start time
        """
        assert_all_utc(start_time_utc)
        weather_model_date_prefix = f"{self.weather_model_prefix}/{start_time_utc.date().isoformat()}/"
        return os.path.join(weather_model_date_prefix, compose_rdps_key(start_time_utc, start_time_utc.hour, prediction_hour, weather_param.value))

    def get_calculated_precip_key(self, datetime_to_calculate_utc: datetime):
        """
        Generates the calculated precip key that points to the associated raster artifact in the object store.
        The model is always assumed to be RDPS.

        :param datetime_to_calculate_utc: UTC datetime the calculated raster is for
        :return: the calculated precip key to the raster artifact in object storage
        """
        assert_all_utc(datetime_to_calculate_utc)
        calculated_weather_prefix = f"{self.weather_model_prefix}/{datetime_to_calculate_utc.date().isoformat()}/"
        return os.path.join(calculated_weather_prefix, compose_computed_precip_rdps_key(datetime_to_calculate_utc))

    def get_weather_data_keys(self, start_time_utc: datetime, datetime_to_calculate_utc: datetime, prediction_hour: int):
        """
        Generates all model data keys that point to their associated raster artifacts in the object store.

        :param start_time_utc: UTC date time when the model run started
        :param datetime_to_calculate_utc: UTC datetime the calculated raster is for
        :param prediction_hour: the prediction hour offset from the start time
        :return: temp, rh, wind speed and precip model data key
        """
        assert_all_utc(start_time_utc, datetime_to_calculate_utc)
        non_precip_keys = tuple([self.get_model_data_key(start_time_utc, prediction_hour, param) for param in WeatherParameter])
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