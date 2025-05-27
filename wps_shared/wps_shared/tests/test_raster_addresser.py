from datetime import datetime, timezone
import pytest
from zoneinfo import ZoneInfo
from wps_shared.sfms.raster_addresser import FWIParameter, RasterKeyAddresser, WeatherParameter

sfms_timezone = ZoneInfo("America/Vancouver")

TEST_DATETIME_1 = datetime(2024, 10, 10, 6, tzinfo=timezone.utc)
TEST_DATE_1_ISO = TEST_DATETIME_1.date().isoformat()

TEST_DATETIME_1_LOCAL = datetime(2024, 10, 10, 6, tzinfo=sfms_timezone)

TEST_DATETIME_2 = datetime(2024, 10, 10, 11, tzinfo=timezone.utc)
TEST_DATE_2_ISO = TEST_DATETIME_2.date().isoformat()

TEST_DATETIME_TO_CALC = TEST_DATETIME_1.replace(hour=20)

RDPS_MODEL_RUN_HOUR = 0
RDPS_MODEL_RUN_00_START = datetime(2024, 10, 10, 0, tzinfo=timezone.utc)
RDPS_MODEL_RUN_12_START = datetime(2024, 10, 10, 12, tzinfo=timezone.utc)
HOUR_OFFSET = 3
HFFMC_DATETIME = datetime(2024, 10, 10, 5, tzinfo=timezone.utc)
HFFMC_DATETIME_ISO = HFFMC_DATETIME.date().isoformat()


@pytest.fixture
def raster_key_addresser():
    return RasterKeyAddresser()


def test_get_uploaded_index_key(raster_key_addresser):
    result_from_utc = raster_key_addresser.get_uploaded_index_key(TEST_DATETIME_1, FWIParameter.DMC)
    assert result_from_utc == "sfms/uploads/actual/2024-10-09/dmc20241009.tif"  # should be the datetime in the SFMS timezone (PDT/PST)

    result_from_local = raster_key_addresser.get_uploaded_index_key(TEST_DATETIME_1_LOCAL, FWIParameter.DMC)
    assert result_from_local == "sfms/uploads/actual/2024-10-10/dmc20241010.tif"  # should be the datetime in the SFMS timezone (PDT/PST)


def test_get_calculated_index_key(raster_key_addresser):
    result = raster_key_addresser.get_calculated_index_key(TEST_DATETIME_1, FWIParameter.DC)
    assert result == f"sfms/calculated/forecast/{TEST_DATE_1_ISO}/dc{TEST_DATE_1_ISO.replace('-', '')}.tif"


def test_get_weather_data_keys(raster_key_addresser):
    result = raster_key_addresser.get_weather_data_keys(TEST_DATETIME_1, TEST_DATETIME_TO_CALC, 20)

    assert len(result) == 4


def test_get_uploaded_hffmc_key_00_hour(raster_key_addresser):
    result = raster_key_addresser.get_uploaded_hffmc_key(RDPS_MODEL_RUN_00_START)
    assert result == "sfms/uploads/hourlies/2024-10-09/fine_fuel_moisture_code2024100916.tif"


def test_get_uploaded_hffmc_key_afternoon(raster_key_addresser):
    result = raster_key_addresser.get_uploaded_hffmc_key(RDPS_MODEL_RUN_12_START)
    assert result == "sfms/uploads/hourlies/2024-10-10/fine_fuel_moisture_code2024101004.tif"


def test_get_weather_data_keys_hffmc(raster_key_addresser: RasterKeyAddresser):
    result = raster_key_addresser.get_weather_data_keys_hffmc(RDPS_MODEL_RUN_00_START, HOUR_OFFSET)
    assert len(result) == 4
    assert result[0] == "weather_models/rdps/2024-10-10/00/temp/CMC_reg_TMP_TGL_2_ps10km_2024101000_P003.grib2"
    assert result[1] == "weather_models/rdps/2024-10-10/00/rh/CMC_reg_RH_TGL_2_ps10km_2024101000_P003.grib2"
    assert result[2] == "weather_models/rdps/2024-10-10/00/wind_speed/CMC_reg_WIND_TGL_10_ps10km_2024101000_P003.grib2"
    assert result[3] == "weather_models/rdps/2024-10-10/00/precip/COMPUTED_reg_APCP_SFC_0_ps10km_20241010_03z.tif"


def test_get_model_data_key_hffmc(raster_key_addresser):
    weather_param = WeatherParameter.TEMP
    result = raster_key_addresser.get_model_data_key_hffmc(RDPS_MODEL_RUN_00_START, HOUR_OFFSET, weather_param)
    assert result == "weather_models/rdps/2024-10-10/00/temp/CMC_reg_TMP_TGL_2_ps10km_2024101000_P003.grib2"


def test_get_calculated_hffmc_index_key(raster_key_addresser: RasterKeyAddresser):
    result = raster_key_addresser.get_calculated_hffmc_index_key(HFFMC_DATETIME)
    assert result == f"sfms/calculated/hourlies/{HFFMC_DATETIME_ISO}/fine_fuel_moisture_code{HFFMC_DATETIME_ISO.replace('-', '')}{HFFMC_DATETIME.hour:02d}.tif"


def test_get_fuel_raster_key(raster_key_addresser: RasterKeyAddresser):
    result = raster_key_addresser.get_fuel_raster_key(TEST_DATETIME_1, 1)
    assert result == f"{raster_key_addresser.sfms_fuel_raster_prefix}/{TEST_DATETIME_1.year}/fbp{TEST_DATETIME_1.year}_v{1}.tif"


def test_get_unprocessed_raster_key(raster_key_addresser: RasterKeyAddresser):
    tif_object = "test.tif"
    result = raster_key_addresser.get_unprocessed_fuel_raster_key(tif_object)
    assert result == f"sfms/static/{tif_object}"
