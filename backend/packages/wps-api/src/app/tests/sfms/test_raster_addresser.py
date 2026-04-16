from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest
from pytest_mock import MockerFixture

from app.sfms.raster_addresser import RasterKeyAddresser, WeatherParameter
from wps_shared.sfms.raster_addresser import FWIParameter, SFMSInterpolatedWeatherParameter

sfms_timezone = ZoneInfo("America/Vancouver")

TEST_DATETIME_1 = datetime(2024, 10, 10, 6, tzinfo=timezone.utc)
TEST_DATE_1_ISO = TEST_DATETIME_1.date().isoformat()

TEST_DATETIME_1_LOCAL = datetime(2024, 10, 10, 6, tzinfo=sfms_timezone)

TEST_DATETIME_TO_CALC = TEST_DATETIME_1.replace(hour=20)

RDPS_MODEL_RUN_00_START = datetime(2024, 10, 10, 0, tzinfo=timezone.utc)
RDPS_MODEL_RUN_12_START = datetime(2024, 10, 10, 12, tzinfo=timezone.utc)
HOUR_OFFSET = 3
HFFMC_DATETIME = datetime(2024, 10, 10, 5, tzinfo=timezone.utc)
HFFMC_DATETIME_ISO = HFFMC_DATETIME.date().isoformat()


@pytest.fixture
def addresser():
    return RasterKeyAddresser()


def test_get_uploaded_index_key(addresser: RasterKeyAddresser):
    result_from_utc = addresser.get_uploaded_index_key(TEST_DATETIME_1, FWIParameter.DMC)
    assert result_from_utc == "sfms/uploads/actual/2024-10-09/dmc20241009.tif"

    result_from_local = addresser.get_uploaded_index_key(TEST_DATETIME_1_LOCAL, FWIParameter.DMC)
    assert result_from_local == "sfms/uploads/actual/2024-10-10/dmc20241010.tif"


def test_get_calculated_index_key(addresser: RasterKeyAddresser):
    result = addresser.get_calculated_index_key(TEST_DATETIME_1, FWIParameter.DC)
    assert (
        result
        == f"sfms/calculated/forecast/{TEST_DATE_1_ISO}/dc{TEST_DATE_1_ISO.replace('-', '')}.tif"
    )


def test_get_weather_data_keys(addresser: RasterKeyAddresser):
    result = addresser.get_weather_data_keys(TEST_DATETIME_1, TEST_DATETIME_TO_CALC, 20)
    assert len(result) == 4
    temp_key, rh_key, wind_speed_key, precip_key = result
    assert temp_key == "weather_models/rdps/2024-10-10/00/temp/20241010T00Z_MSC_RDPS_AirTemp_AGL-2m_RLatLon0.09_PT020H.grib2"
    assert rh_key == "weather_models/rdps/2024-10-10/00/rh/20241010T00Z_MSC_RDPS_RelativeHumidity_AGL-2m_RLatLon0.09_PT020H.grib2"
    assert wind_speed_key == "weather_models/rdps/2024-10-10/00/wind_speed/20241010T00Z_MSC_RDPS_WindSpeed_AGL-10m_RLatLon0.09_PT020H.grib2"
    assert precip_key == "weather_models/rdps/2024-10-10/12/precip/COMPUTED_reg_APCP_SFC_0_ps10km_20241010_20z.tif"


def test_get_weather_data_keys_legacy(addresser: RasterKeyAddresser):
    result = addresser.get_weather_data_keys_legacy(TEST_DATETIME_1, 20)
    assert len(result) == 3
    temp_key, rh_key, wind_speed_key = result
    assert temp_key == "weather_models/rdps/2024-10-10/00/temp/CMC_reg_TMP_TGL_2_ps10km_2024101000_P020.grib2"
    assert rh_key == "weather_models/rdps/2024-10-10/00/rh/CMC_reg_RH_TGL_2_ps10km_2024101000_P020.grib2"
    assert wind_speed_key == "weather_models/rdps/2024-10-10/00/wind_speed/CMC_reg_WIND_TGL_10_ps10km_2024101000_P020.grib2"


def test_get_weather_data_keys_hffmc_legacy(addresser: RasterKeyAddresser):
    result = addresser.get_weather_data_keys_hffmc_legacy(RDPS_MODEL_RUN_00_START, HOUR_OFFSET)
    assert len(result) == 3
    temp_key, rh_key, wind_speed_key = result
    assert temp_key == "weather_models/rdps/2024-10-10/00/temp/CMC_reg_TMP_TGL_2_ps10km_2024101000_P003.grib2"
    assert rh_key == "weather_models/rdps/2024-10-10/00/rh/CMC_reg_RH_TGL_2_ps10km_2024101000_P003.grib2"
    assert wind_speed_key == "weather_models/rdps/2024-10-10/00/wind_speed/CMC_reg_WIND_TGL_10_ps10km_2024101000_P003.grib2"


def test_get_uploaded_hffmc_key_00_hour(addresser: RasterKeyAddresser):
    result = addresser.get_uploaded_hffmc_key(RDPS_MODEL_RUN_00_START)
    assert result == "sfms/uploads/hourlies/2024-10-09/fine_fuel_moisture_code2024100916.tif"


def test_get_uploaded_hffmc_key_afternoon(addresser: RasterKeyAddresser):
    result = addresser.get_uploaded_hffmc_key(RDPS_MODEL_RUN_12_START)
    assert result == "sfms/uploads/hourlies/2024-10-10/fine_fuel_moisture_code2024101004.tif"


def test_get_weather_data_keys_hffmc(addresser: RasterKeyAddresser):
    result = addresser.get_weather_data_keys_hffmc(RDPS_MODEL_RUN_00_START, HOUR_OFFSET)
    assert len(result) == 4
    assert (
        result[0]
        == "weather_models/rdps/2024-10-10/00/temp/20241010T00Z_MSC_RDPS_AirTemp_AGL-2m_RLatLon0.09_PT003H.grib2"
    )
    assert (
        result[1]
        == "weather_models/rdps/2024-10-10/00/rh/20241010T00Z_MSC_RDPS_RelativeHumidity_AGL-2m_RLatLon0.09_PT003H.grib2"
    )
    assert (
        result[2]
        == "weather_models/rdps/2024-10-10/00/wind_speed/20241010T00Z_MSC_RDPS_WindSpeed_AGL-10m_RLatLon0.09_PT003H.grib2"
    )
    assert (
        result[3]
        == "weather_models/rdps/2024-10-10/00/precip/COMPUTED_reg_APCP_SFC_0_ps10km_20241010_03z.tif"
    )


def test_get_model_data_key_hffmc(addresser: RasterKeyAddresser):
    result = addresser.get_model_data_key_hffmc(RDPS_MODEL_RUN_00_START, HOUR_OFFSET, WeatherParameter.TEMP)
    assert (
        result
        == "weather_models/rdps/2024-10-10/00/temp/20241010T00Z_MSC_RDPS_AirTemp_AGL-2m_RLatLon0.09_PT003H.grib2"
    )


def test_get_calculated_hffmc_index_key(addresser: RasterKeyAddresser):
    result = addresser.get_calculated_hffmc_index_key(HFFMC_DATETIME)
    assert (
        result
        == f"sfms/calculated/hourlies/{HFFMC_DATETIME_ISO}/fine_fuel_moisture_code{HFFMC_DATETIME_ISO.replace('-', '')}{HFFMC_DATETIME.hour:02d}.tif"
    )


@pytest.mark.parametrize(
    "weather_param,expected_key",
    [
        (
            SFMSInterpolatedWeatherParameter.TEMP,
            "sfms/interpolated/temperature/2024/01/15/temperature_20240115.tif",
        ),
        (SFMSInterpolatedWeatherParameter.RH, "sfms/interpolated/relative_humidity/2024/01/15/relative_humidity_20240115.tif"),
        (
            SFMSInterpolatedWeatherParameter.WIND_SPEED,
            "sfms/interpolated/wind_speed/2024/01/15/wind_speed_20240115.tif",
        ),
        (
            SFMSInterpolatedWeatherParameter.WIND_DIRECTION,
            "sfms/interpolated/wind_direction/2024/01/15/wind_direction_20240115.tif",
        ),
        (
            SFMSInterpolatedWeatherParameter.PRECIP,
            "sfms/interpolated/precipitation/2024/01/15/precipitation_20240115.tif",
        ),
    ],
)
def test_get_interpolated_key_weather_params(
    addresser: RasterKeyAddresser,
    weather_param: SFMSInterpolatedWeatherParameter,
    expected_key: str,
):
    dt = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)
    result = addresser.get_interpolated_key(dt, weather_param)
    assert result == expected_key


@pytest.mark.parametrize(
    "dt,expected_key",
    [
        (
            datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc),
            "sfms/interpolated/temperature/2024/01/15/temperature_20240115.tif",
        ),
        (
            datetime(2024, 12, 31, 20, 0, 0, tzinfo=timezone.utc),
            "sfms/interpolated/temperature/2024/12/31/temperature_20241231.tif",
        ),
        (
            datetime(2024, 3, 5, 20, 0, 0, tzinfo=timezone.utc),
            "sfms/interpolated/temperature/2024/03/05/temperature_20240305.tif",
        ),
    ],
)
def test_get_interpolated_key_different_dates(
    addresser: RasterKeyAddresser, dt: datetime, expected_key: str
):
    result = addresser.get_interpolated_key(dt, SFMSInterpolatedWeatherParameter.TEMP)
    assert result == expected_key


CALC_DATETIME = datetime(2024, 10, 10, 3, tzinfo=timezone.utc)


def _make_s3(*, new_keys_exist: bool, legacy_keys_exist: bool = False) -> MagicMock:
    mock = MagicMock()
    mock.all_objects_exist = AsyncMock(side_effect=[new_keys_exist, legacy_keys_exist])
    return mock


@pytest.mark.anyio
async def test_resolve_weather_data_keys_returns_new_format_when_available(addresser: RasterKeyAddresser):
    mock_s3 = _make_s3(new_keys_exist=True)
    result = await addresser.resolve_weather_data_keys(mock_s3, RDPS_MODEL_RUN_00_START, CALC_DATETIME, HOUR_OFFSET)
    assert result is not None
    temp_key, rh_key, wind_speed_key, _ = result
    assert "MSC_RDPS_AirTemp_AGL-2m" in temp_key
    assert "MSC_RDPS_RelativeHumidity_AGL-2m" in rh_key
    assert "MSC_RDPS_WindSpeed_AGL-10m" in wind_speed_key
    mock_s3.all_objects_exist.assert_called_once()


@pytest.mark.anyio
async def test_resolve_weather_data_keys_falls_back_to_legacy(addresser: RasterKeyAddresser):
    mock_s3 = _make_s3(new_keys_exist=False, legacy_keys_exist=True)
    result = await addresser.resolve_weather_data_keys(mock_s3, RDPS_MODEL_RUN_00_START, CALC_DATETIME, HOUR_OFFSET)
    assert result is not None
    temp_key, rh_key, wind_speed_key, precip_key = result
    assert "CMC_reg_TMP" in temp_key
    assert "CMC_reg_RH" in rh_key
    assert "CMC_reg_WIND" in wind_speed_key
    assert "COMPUTED_reg" in precip_key


@pytest.mark.anyio
async def test_resolve_weather_data_keys_returns_none_when_both_absent(addresser: RasterKeyAddresser):
    mock_s3 = _make_s3(new_keys_exist=False, legacy_keys_exist=False)
    result = await addresser.resolve_weather_data_keys(mock_s3, RDPS_MODEL_RUN_00_START, CALC_DATETIME, HOUR_OFFSET)
    assert result is None
    assert mock_s3.all_objects_exist.call_count == 2


@pytest.mark.anyio
async def test_resolve_weather_data_keys_hffmc_returns_new_format_when_available(addresser: RasterKeyAddresser):
    mock_s3 = _make_s3(new_keys_exist=True)
    result = await addresser.resolve_weather_data_keys_hffmc(mock_s3, RDPS_MODEL_RUN_00_START, HOUR_OFFSET)
    assert result is not None
    temp_key, rh_key, wind_speed_key, _ = result
    assert "MSC_RDPS_AirTemp_AGL-2m" in temp_key
    assert "MSC_RDPS_RelativeHumidity_AGL-2m" in rh_key
    assert "MSC_RDPS_WindSpeed_AGL-10m" in wind_speed_key
    mock_s3.all_objects_exist.assert_called_once()


@pytest.mark.anyio
async def test_resolve_weather_data_keys_hffmc_falls_back_to_legacy(addresser: RasterKeyAddresser):
    mock_s3 = _make_s3(new_keys_exist=False, legacy_keys_exist=True)
    result = await addresser.resolve_weather_data_keys_hffmc(mock_s3, RDPS_MODEL_RUN_00_START, HOUR_OFFSET)
    assert result is not None
    temp_key, rh_key, wind_speed_key, precip_key = result
    assert "CMC_reg_TMP" in temp_key
    assert "CMC_reg_RH" in rh_key
    assert "CMC_reg_WIND" in wind_speed_key
    assert "COMPUTED_reg" in precip_key


@pytest.mark.anyio
async def test_resolve_weather_data_keys_hffmc_returns_none_when_both_absent(addresser: RasterKeyAddresser):
    mock_s3 = _make_s3(new_keys_exist=False, legacy_keys_exist=False)
    result = await addresser.resolve_weather_data_keys_hffmc(mock_s3, RDPS_MODEL_RUN_00_START, HOUR_OFFSET)
    assert result is None
    assert mock_s3.all_objects_exist.call_count == 2
