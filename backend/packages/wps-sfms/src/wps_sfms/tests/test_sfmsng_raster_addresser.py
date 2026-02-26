from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import FWIParameter, SFMSInterpolatedWeatherParameter
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

# 2024-04-15 20:00 UTC
TEST_DATETIME = datetime(2024, 4, 15, 20, 0, 0, tzinfo=timezone.utc)
NON_UTC = datetime(2024, 4, 15, 13, 0, 0, tzinfo=ZoneInfo("America/Vancouver"))


@pytest.fixture
def addresser():
    return SFMSNGRasterAddresser()


class TestGetInterpolatedKey:
    @pytest.mark.parametrize(
        "weather_param,expected_key",
        [
            (
                SFMSInterpolatedWeatherParameter.TEMP,
                "sfms_ng/interpolated/temp/2024/04/15/temp_20240415.tif",
            ),
            (
                SFMSInterpolatedWeatherParameter.RH,
                "sfms_ng/interpolated/rh/2024/04/15/rh_20240415.tif",
            ),
            (
                SFMSInterpolatedWeatherParameter.WIND_SPEED,
                "sfms_ng/interpolated/wind_speed/2024/04/15/wind_speed_20240415.tif",
            ),
            (
                SFMSInterpolatedWeatherParameter.PRECIP,
                "sfms_ng/interpolated/precip/2024/04/15/precip_20240415.tif",
            ),
        ],
    )
    def test_weather_params(self, addresser, weather_param, expected_key):
        assert addresser.get_interpolated_key(TEST_DATETIME, weather_param) == expected_key

    def test_zero_pads_month_and_day(self, addresser):
        dt = datetime(2024, 3, 5, 20, 0, 0, tzinfo=timezone.utc)
        result = addresser.get_interpolated_key(dt, SFMSInterpolatedWeatherParameter.TEMP)
        assert result == "sfms_ng/interpolated/temp/2024/03/05/temp_20240305.tif"

    def test_non_utc_raises(self, addresser):
        with pytest.raises(Exception):
            addresser.get_interpolated_key(NON_UTC, SFMSInterpolatedWeatherParameter.TEMP)


class TestGetUploadedIndexKey:
    @pytest.mark.parametrize(
        "fwi_param,expected_key",
        [
            (FWIParameter.FFMC, "sfms_ng/uploads/actual/2024-04-15/ffmc20240415.tif"),
            (FWIParameter.DMC, "sfms_ng/uploads/actual/2024-04-15/dmc20240415.tif"),
            (FWIParameter.DC, "sfms_ng/uploads/actual/2024-04-15/dc20240415.tif"),
        ],
    )
    def test_fwi_params(self, addresser, fwi_param, expected_key):
        assert addresser.get_uploaded_index_key(TEST_DATETIME, fwi_param) == expected_key

    def test_non_utc_raises(self, addresser):
        with pytest.raises(Exception):
            addresser.get_uploaded_index_key(NON_UTC, FWIParameter.FFMC)


class TestGetCalculatedIndexKey:
    def test_default_run_type_is_actual(self, addresser):
        result = addresser.get_calculated_index_key(TEST_DATETIME, FWIParameter.DC)
        assert result == "sfms_ng/calculated/actual/2024-04-15/dc20240415.tif"

    def test_forecast_run_type(self, addresser):
        result = addresser.get_calculated_index_key(TEST_DATETIME, FWIParameter.FFMC, run_type="forecast")
        assert result == "sfms_ng/calculated/forecast/2024-04-15/ffmc20240415.tif"

    def test_non_utc_raises(self, addresser):
        with pytest.raises(Exception):
            addresser.get_calculated_index_key(NON_UTC, FWIParameter.DC)


class TestGetActualFwiInputs:
    @pytest.mark.parametrize("fwi_param", [FWIParameter.FFMC, FWIParameter.DMC, FWIParameter.DC])
    def test_all_params(self, addresser, fwi_param):
        s3 = addresser.s3_prefix
        p = fwi_param.value
        result = addresser.get_actual_fwi_inputs(TEST_DATETIME, fwi_param)

        assert result.temp_key == f"{s3}/sfms_ng/interpolated/temp/2024/04/15/temp_20240415.tif"
        assert result.rh_key == f"{s3}/sfms_ng/interpolated/rh/2024/04/15/rh_20240415.tif"
        assert result.precip_key == f"{s3}/sfms_ng/interpolated/precip/2024/04/15/precip_20240415.tif"
        assert result.prev_fwi_key == f"{s3}/sfms_ng/uploads/actual/2024-04-14/{p}20240414.tif"
        assert result.output_key == f"sfms_ng/calculated/actual/2024-04-15/{p}20240415.tif"
        assert result.cog_key == f"{s3}/sfms_ng/calculated/actual/2024-04-15/{p}20240415_cog.tif"
        assert result.run_type == RunType.ACTUAL

    def test_gdal_prefix_on_inputs_not_output(self, addresser):
        s3 = addresser.s3_prefix
        result = addresser.get_actual_fwi_inputs(TEST_DATETIME, FWIParameter.DMC)

        assert result.temp_key.startswith(s3)
        assert result.rh_key.startswith(s3)
        assert result.precip_key.startswith(s3)
        assert result.prev_fwi_key.startswith(s3)
        assert not result.output_key.startswith(s3)

    def test_prev_fwi_key_uses_yesterday(self, addresser):
        result = addresser.get_actual_fwi_inputs(TEST_DATETIME, FWIParameter.DC)

        assert "2024-04-14" in result.prev_fwi_key
        assert "2024-04-15" not in result.prev_fwi_key

    def test_output_key_uses_actual_run_type(self, addresser):
        result = addresser.get_actual_fwi_inputs(TEST_DATETIME, FWIParameter.DMC)

        assert "actual" in result.output_key
        assert "forecast" not in result.output_key

    def test_non_utc_raises(self, addresser):
        with pytest.raises(Exception):
            addresser.get_actual_fwi_inputs(NON_UTC, FWIParameter.DMC)
