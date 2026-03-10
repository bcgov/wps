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


class TestGetActualWeatherKey:
    @pytest.mark.parametrize(
        "weather_param,expected_key",
        [
            (
                SFMSInterpolatedWeatherParameter.TEMP,
                "sfms_ng/actual/2024/04/15/temperature_20240415.tif",
            ),
            (
                SFMSInterpolatedWeatherParameter.RH,
                "sfms_ng/actual/2024/04/15/relative_humidity_20240415.tif",
            ),
            (
                SFMSInterpolatedWeatherParameter.WIND_SPEED,
                "sfms_ng/actual/2024/04/15/wind_speed_20240415.tif",
            ),
            (
                SFMSInterpolatedWeatherParameter.WIND_DIRECTION,
                "sfms_ng/actual/2024/04/15/wind_direction_20240415.tif",
            ),
            (
                SFMSInterpolatedWeatherParameter.PRECIP,
                "sfms_ng/actual/2024/04/15/precipitation_20240415.tif",
            ),
        ],
    )
    def test_weather_params(
        self,
        addresser: SFMSNGRasterAddresser,
        weather_param: SFMSInterpolatedWeatherParameter,
        expected_key,
    ):
        assert addresser.get_actual_weather_key(TEST_DATETIME, weather_param) == expected_key

    def test_zero_pads_month_and_day(self, addresser: SFMSNGRasterAddresser):
        dt = datetime(2024, 3, 5, 20, 0, 0, tzinfo=timezone.utc)
        result = addresser.get_actual_weather_key(dt, SFMSInterpolatedWeatherParameter.TEMP)
        assert result == "sfms_ng/actual/2024/03/05/temperature_20240305.tif"

    def test_non_utc_raises(self, addresser: SFMSNGRasterAddresser):
        with pytest.raises(Exception):
            addresser.get_actual_weather_key(NON_UTC, SFMSInterpolatedWeatherParameter.TEMP)


class TestGetActualIndexKey:
    @pytest.mark.parametrize(
        "fwi_param,expected_key",
        [
            (FWIParameter.FFMC, "sfms_ng/actual/2024/04/15/ffmc_20240415.tif"),
            (FWIParameter.DMC, "sfms_ng/actual/2024/04/15/dmc_20240415.tif"),
            (FWIParameter.DC, "sfms_ng/actual/2024/04/15/dc_20240415.tif"),
        ],
    )
    def test_fwi_params(self, addresser: SFMSNGRasterAddresser, fwi_param, expected_key):
        assert addresser.get_actual_index_key(TEST_DATETIME, fwi_param) == expected_key

    def test_non_utc_raises(self, addresser: SFMSNGRasterAddresser):
        with pytest.raises(Exception):
            addresser.get_actual_index_key(NON_UTC, FWIParameter.FFMC)


class TestGetActualFwiInputs:
    @pytest.mark.parametrize(
        "fwi_param,index_key_checks",
        [
            (FWIParameter.FFMC, {FWIParameter.FFMC: "2024/04/14/ffmc_20240414.tif"}),
            (FWIParameter.DMC, {FWIParameter.DMC: "2024/04/14/dmc_20240414.tif"}),
            (FWIParameter.DC, {FWIParameter.DC: "2024/04/14/dc_20240414.tif"}),
            (FWIParameter.ISI, {FWIParameter.FFMC: "2024/04/15/ffmc_20240415.tif"}),
            (
                FWIParameter.BUI,
                {
                    FWIParameter.DMC: "2024/04/15/dmc_20240415.tif",
                    FWIParameter.DC: "2024/04/15/dc_20240415.tif",
                },
            ),
            (
                FWIParameter.FWI,
                {
                    FWIParameter.ISI: "2024/04/15/isi_20240415.tif",
                    FWIParameter.BUI: "2024/04/15/bui_20240415.tif",
                },
            ),
        ],
    )
    def test_all_params(
        self,
        addresser: SFMSNGRasterAddresser,
        fwi_param: FWIParameter,
        index_key_checks: dict[FWIParameter, str],
    ):
        s3 = addresser.s3_prefix
        p = fwi_param.value
        result = addresser.get_actual_fwi_inputs(TEST_DATETIME, fwi_param)

        assert (
            result.weather_keys[SFMSInterpolatedWeatherParameter.TEMP]
            == f"{s3}/sfms_ng/actual/2024/04/15/temperature_20240415.tif"
        )
        assert (
            result.weather_keys[SFMSInterpolatedWeatherParameter.RH]
            == f"{s3}/sfms_ng/actual/2024/04/15/relative_humidity_20240415.tif"
        )
        assert (
            result.weather_keys[SFMSInterpolatedWeatherParameter.PRECIP]
            == f"{s3}/sfms_ng/actual/2024/04/15/precipitation_20240415.tif"
        )
        assert (
            result.weather_keys[SFMSInterpolatedWeatherParameter.WIND_SPEED]
            == f"{s3}/sfms_ng/actual/2024/04/15/wind_speed_20240415.tif"
        )
        for index_param, expected_suffix in index_key_checks.items():
            assert result.index_keys[index_param] == f"{s3}/sfms_ng/actual/{expected_suffix}"
        assert result.output_key == f"sfms_ng/actual/2024/04/15/{p}_20240415.tif"
        assert result.run_type == RunType.ACTUAL

    def test_gdal_prefix_on_inputs_not_output(self, addresser: SFMSNGRasterAddresser):
        s3 = addresser.s3_prefix
        result = addresser.get_actual_fwi_inputs(TEST_DATETIME, FWIParameter.DMC)

        for weather_key in result.weather_keys.values():
            assert weather_key.startswith(s3)
        for index_key in result.index_keys.values():
            assert index_key.startswith(s3)
        assert not result.output_key.startswith(s3)

    def test_prev_fwi_key_uses_yesterday(self, addresser: SFMSNGRasterAddresser):
        result = addresser.get_actual_fwi_inputs(TEST_DATETIME, FWIParameter.DC)

        dc_dependency_key = result.index_keys[FWIParameter.DC]
        assert "2024/04/14" in dc_dependency_key
        assert "2024/04/15" not in dc_dependency_key

    def test_output_key_uses_actual_run_type(self, addresser: SFMSNGRasterAddresser):
        result = addresser.get_actual_fwi_inputs(TEST_DATETIME, FWIParameter.DMC)

        assert "actual" in result.output_key
        assert "forecast" not in result.output_key

    def test_non_utc_raises(self, addresser: SFMSNGRasterAddresser):
        with pytest.raises(Exception):
            addresser.get_actual_fwi_inputs(NON_UTC, FWIParameter.DMC)
