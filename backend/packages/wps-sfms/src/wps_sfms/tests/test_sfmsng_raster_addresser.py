from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from wps_shared.run_type import RunType
from wps_shared.sfms.raster_addresser import (
    FBPParameter,
    FWIParameter,
    SFMSInterpolatedWeatherParameter,
)
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

# 2024-04-15 20:00 UTC
TEST_DATETIME = datetime(2024, 4, 15, 20, 0, 0, tzinfo=timezone.utc)
NON_UTC = datetime(2024, 4, 15, 13, 0, 0, tzinfo=ZoneInfo("America/Vancouver"))


@pytest.fixture
def addresser():
    return SFMSNGRasterAddresser()


class TestTemporalFuelKeys:
    @pytest.mark.parametrize(
        "run_type,expected_key",
        [
            (RunType.ACTUAL, "sfms_ng/actual/2024/04/15/danger_rating_20240415.tif"),
            (RunType.FORECAST, "sfms_ng/forecast/2024/04/15/danger_rating_20240415.tif"),
        ],
    )
    def test_danger_rating_key(self, addresser, run_type, expected_key):
        assert addresser.get_danger_rating_key(TEST_DATETIME, run_type) == expected_key

    def test_julian_keys_use_julian_static_prefix(self, addresser: SFMSNGRasterAddresser):
        assert addresser.get_julian_key("green_up_on") == "sfms_ng/static/julian/green_up_on.tif"

    def test_julian_archive_key_is_addressed_by_hash(self, addresser: SFMSNGRasterAddresser):
        assert (
            addresser.get_julian_archive_key("green_up_on", "abc123")
            == "sfms_ng/static/julian/archive/green_up_on/abc123.tif"
        )

    def test_temporal_fuel_keys_are_dated_and_versioned(self, addresser: SFMSNGRasterAddresser):
        assert addresser.get_temporal_fuel_key(date(2026, 6, 1), 2) == (
            "sfms_ng/fuel/temporal/2026/06/01/2/fuel2026_06_01_2.tif"
        )
        assert addresser.get_national_fuel_codes_key() == (
            "sfms_ng/fuel/temporal/fuel_codes_lookup.json"
        )


class TestGetFoliarMoistureContentInputs:
    def test_get_fmc_key_uses_shared_static_date_path(self, addresser: SFMSNGRasterAddresser):
        assert addresser.get_fmc_key(date(2024, 4, 15)) == (
            "sfms_ng/static/fmc/2024/04/15/fmc_20240415.tif"
        )

    def test_get_fmc_inputs_uses_sfmsng_static_rasters(self, addresser: SFMSNGRasterAddresser):
        target_dates = [date(2024, 4, 15), date(2024, 4, 16)]
        fuel_key = addresser.gdal_path(addresser.get_fuel_raster_key(TEST_DATETIME, 3))

        result = addresser.get_fmc_inputs(target_dates, fuel_key)

        s3 = addresser.s3_prefix
        assert result.fuel_key == fuel_key
        assert result.elevation_key == f"{s3}/sfms_ng/static/bc_elevation.tif"
        assert result.latitude_key == f"{s3}/sfms_ng/static/latitude.tif"
        assert result.longitude_key == f"{s3}/sfms_ng/static/longitude.tif"
        assert result.output_keys == {
            date(2024, 4, 15): "sfms_ng/static/fmc/2024/04/15/fmc_20240415.tif",
            date(2024, 4, 16): "sfms_ng/static/fmc/2024/04/16/fmc_20240416.tif",
        }

    @pytest.mark.parametrize(
        "method_name,expected_key",
        [
            ("get_slope_key", "sfms_ng/static/bc_slope.tif"),
            ("get_aspect_key", "sfms_ng/static/bc_aspect.tif"),
            ("get_latitude_key", "sfms_ng/static/latitude.tif"),
            ("get_longitude_key", "sfms_ng/static/longitude.tif"),
            ("get_elevation_key", "sfms_ng/static/bc_elevation.tif"),
        ],
    )
    def test_static_lookup_helpers(
        self, addresser: SFMSNGRasterAddresser, method_name: str, expected_key: str
    ):
        assert getattr(addresser, method_name)() == expected_key


class TestRunManifestKeys:
    def test_manifest_key_uses_the_target_date_folder(self, addresser: SFMSNGRasterAddresser):
        assert (
            addresser.get_run_manifest_key(
                RunType.ACTUAL,
                date(2026, 10, 13),
                datetime(2026, 10, 13, 20, 45, 0, tzinfo=timezone.utc),
            )
            == "sfms_ng/runs/actual/2026/10/13/target-2026-10-13_run-2026-10-13T20-45-00.000000Z.json"
        )

    def test_forecast_manifest_key_uses_the_forecast_date_folder(
        self, addresser: SFMSNGRasterAddresser
    ):
        # forecast runs process dates after the run datetime; the folder is the forecast date
        assert (
            addresser.get_run_manifest_key(
                RunType.FORECAST,
                date(2026, 10, 14),
                datetime(2026, 10, 13, 20, 45, 0, tzinfo=timezone.utc),
            )
            == "sfms_ng/runs/forecast/2026/10/14/target-2026-10-14_run-2026-10-13T20-45-00.000000Z.json"
        )

    def test_manifest_key_zero_pads_the_run_datetime_parts(self, addresser: SFMSNGRasterAddresser):
        assert (
            addresser.get_run_manifest_key(
                RunType.ACTUAL, date(2026, 1, 2), datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
            )
            == "sfms_ng/runs/actual/2026/01/02/target-2026-01-02_run-2026-01-02T03-04-05.000000Z.json"
        )

    def test_manifest_key_preserves_run_datetime_microseconds(
        self, addresser: SFMSNGRasterAddresser
    ):
        assert (
            addresser.get_run_manifest_key(
                RunType.ACTUAL,
                date(2026, 1, 2),
                datetime(2026, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc),
            )
            == "sfms_ng/runs/actual/2026/01/02/target-2026-01-02_run-2026-01-02T03-04-05.123456Z.json"
        )

    def test_non_utc_raises(self, addresser: SFMSNGRasterAddresser):
        for_date = date(2026, 10, 13)
        with pytest.raises(AssertionError, match="is not in UTC"):
            addresser.get_run_manifest_key(RunType.ACTUAL, for_date, NON_UTC)


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
        with pytest.raises(AssertionError, match="is not in UTC"):
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
        with pytest.raises(AssertionError, match="is not in UTC"):
            addresser.get_actual_index_key(NON_UTC, FWIParameter.FFMC)


class TestGetFwiInputs:
    WEATHER = {
        param: f"sfms_ng/actual/2024/04/15/{param.value}_20240415.tif"
        for param in SFMSInterpolatedWeatherParameter
    }
    INDEX_KEYS = {
        FWIParameter.DMC: "sfms_ng/actual/2024/04/15/dmc_20240415.tif",
        FWIParameter.DC: "sfms_ng/actual/2024/04/15/dc_20240415.tif",
    }

    def test_reads_the_given_index_rasters_and_fwi_weather(self, addresser: SFMSNGRasterAddresser):
        result = addresser.get_fwi_inputs(
            TEST_DATETIME, FWIParameter.BUI, RunType.ACTUAL, self.WEATHER, self.INDEX_KEYS
        )

        assert result.index_keys == {
            param: addresser.gdal_path(key) for param, key in self.INDEX_KEYS.items()
        }
        # wind direction is interpolated but no FWI index reads it
        assert result.weather_keys == {
            param: addresser.gdal_path(self.WEATHER[param])
            for param in (
                SFMSInterpolatedWeatherParameter.TEMP,
                SFMSInterpolatedWeatherParameter.RH,
                SFMSInterpolatedWeatherParameter.PRECIP,
                SFMSInterpolatedWeatherParameter.WIND_SPEED,
            )
        }
        assert result.output_key == "sfms_ng/actual/2024/04/15/bui_20240415.tif"
        assert result.run_type == RunType.ACTUAL

    def test_output_key_uses_the_run_type(self, addresser: SFMSNGRasterAddresser):
        result = addresser.get_fwi_inputs(
            TEST_DATETIME, FWIParameter.BUI, RunType.FORECAST, self.WEATHER, self.INDEX_KEYS
        )

        assert result.output_key == "sfms_ng/forecast/2024/04/15/bui_20240415.tif"
        assert result.run_type == RunType.FORECAST

    def test_non_utc_raises(self, addresser: SFMSNGRasterAddresser):
        weather, index_keys = self.WEATHER, self.INDEX_KEYS

        with pytest.raises(AssertionError, match="is not in UTC"):
            addresser.get_fwi_inputs(NON_UTC, FWIParameter.BUI, RunType.ACTUAL, weather, index_keys)


class TestPrimaryFireBehaviourInputs:
    def test_fbp_key_uses_sfc_parameter(self, addresser: SFMSNGRasterAddresser):
        assert addresser.get_fbp_key(TEST_DATETIME, FBPParameter.SFC, RunType.ACTUAL) == (
            "sfms_ng/actual/2024/04/15/sfc_20240415.tif"
        )

    def test_percent_conifer_key_uses_year(self, addresser: SFMSNGRasterAddresser):
        assert addresser.get_percent_conifer_key(2024) == "sfms/static/m12_2024.tif"

    def test_percent_dead_conifer_key_uses_year(self, addresser: SFMSNGRasterAddresser):
        assert addresser.get_percent_dead_conifer_key(2024) == "sfms/static/m34_2024.tif"

    @pytest.mark.parametrize("run_type", [RunType.ACTUAL, RunType.FORECAST])
    def test_builds_same_day_inputs_and_five_output_keys(
        self, addresser: SFMSNGRasterAddresser, run_type: RunType
    ):
        fuel_key = addresser.gdal_path(addresser.get_fuel_raster_key(TEST_DATETIME, 3))
        percent_conifer_key = addresser.gdal_path(addresser.get_percent_conifer_key(2024))
        wind_speed_key = addresser.gdal_path(
            addresser.get_weather_key(
                TEST_DATETIME,
                SFMSInterpolatedWeatherParameter.WIND_SPEED,
                run_type,
            )
        )
        wind_direction_key = addresser.gdal_path(
            addresser.get_weather_key(
                TEST_DATETIME,
                SFMSInterpolatedWeatherParameter.WIND_DIRECTION,
                run_type,
            )
        )
        fmc_key = addresser.gdal_path(addresser.get_fmc_key(TEST_DATETIME.date()))
        ffmc_key = addresser.gdal_path(
            addresser.get_index_key(TEST_DATETIME, FWIParameter.FFMC, run_type)
        )
        bui_key = addresser.gdal_path(
            addresser.get_index_key(TEST_DATETIME, FWIParameter.BUI, run_type)
        )
        slope_key = addresser.gdal_path(addresser.get_slope_key())
        aspect_key = addresser.gdal_path(addresser.get_aspect_key())

        result = addresser.get_primary_fire_behaviour_inputs(
            TEST_DATETIME,
            run_type,
            fuel_key,
            percent_conifer_key,
            ffmc_key,
            bui_key,
            wind_speed_key,
            wind_direction_key,
            fmc_key,
            slope_key,
            aspect_key,
        )

        assert result.fuel_key == fuel_key
        assert result.ffmc_key == ffmc_key
        assert result.bui_key == bui_key
        assert result.wind_speed_key == wind_speed_key
        assert result.wind_direction_key == wind_direction_key
        assert result.slope_key == slope_key
        assert result.aspect_key == aspect_key
        assert result.percent_conifer_key == percent_conifer_key
        assert result.fmc_key == fmc_key
        assert result.output_keys == {
            FBPParameter.SFC: f"sfms_ng/{run_type.value}/2024/04/15/sfc_20240415.tif",
            FBPParameter.ROS: f"sfms_ng/{run_type.value}/2024/04/15/ros_20240415.tif",
            FBPParameter.HFI: f"sfms_ng/{run_type.value}/2024/04/15/hfi_20240415.tif",
            FBPParameter.TFC: f"sfms_ng/{run_type.value}/2024/04/15/tfc_20240415.tif",
            FBPParameter.CFB: f"sfms_ng/{run_type.value}/2024/04/15/cfb_20240415.tif",
        }
        assert result.run_type == run_type

    def test_non_utc_raises(self, addresser: SFMSNGRasterAddresser):
        fuel_key = addresser.gdal_path(addresser.get_fuel_raster_key(TEST_DATETIME, 3))
        percent_conifer_key = addresser.gdal_path(addresser.get_percent_conifer_key(2024))

        with pytest.raises(AssertionError, match="is not in UTC"):
            addresser.get_primary_fire_behaviour_inputs(
                NON_UTC,
                RunType.ACTUAL,
                fuel_key,
                percent_conifer_key,
                "ffmc",
                "bui",
                "wind-speed",
                "wind-direction",
                "fmc",
                "slope",
                "aspect",
            )


class TestGetForecastKeys:
    @pytest.mark.parametrize(
        "weather_param,expected_key",
        [
            (
                SFMSInterpolatedWeatherParameter.TEMP,
                "sfms_ng/forecast/2024/04/15/temperature_20240415.tif",
            ),
            (
                SFMSInterpolatedWeatherParameter.RH,
                "sfms_ng/forecast/2024/04/15/relative_humidity_20240415.tif",
            ),
            (
                SFMSInterpolatedWeatherParameter.WIND_SPEED,
                "sfms_ng/forecast/2024/04/15/wind_speed_20240415.tif",
            ),
            (
                SFMSInterpolatedWeatherParameter.WIND_DIRECTION,
                "sfms_ng/forecast/2024/04/15/wind_direction_20240415.tif",
            ),
            (
                SFMSInterpolatedWeatherParameter.PRECIP,
                "sfms_ng/forecast/2024/04/15/precipitation_20240415.tif",
            ),
        ],
    )
    def test_forecast_weather_params(
        self,
        addresser: SFMSNGRasterAddresser,
        weather_param: SFMSInterpolatedWeatherParameter,
        expected_key,
    ):
        assert addresser.get_forecast_weather_key(TEST_DATETIME, weather_param) == expected_key

    @pytest.mark.parametrize(
        "fwi_param,expected_key",
        [
            (FWIParameter.FFMC, "sfms_ng/forecast/2024/04/15/ffmc_20240415.tif"),
            (FWIParameter.DMC, "sfms_ng/forecast/2024/04/15/dmc_20240415.tif"),
            (FWIParameter.DC, "sfms_ng/forecast/2024/04/15/dc_20240415.tif"),
            (FWIParameter.ISI, "sfms_ng/forecast/2024/04/15/isi_20240415.tif"),
            (FWIParameter.BUI, "sfms_ng/forecast/2024/04/15/bui_20240415.tif"),
            (FWIParameter.FWI, "sfms_ng/forecast/2024/04/15/fwi_20240415.tif"),
        ],
    )
    def test_forecast_index_params(self, addresser: SFMSNGRasterAddresser, fwi_param, expected_key):
        assert addresser.get_forecast_index_key(TEST_DATETIME, fwi_param) == expected_key
