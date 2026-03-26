"""
Unit tests for wps_weather.wx_4panel_charts.wx_4panel_charts.

All external dependencies (wps_shared, cartopy, matplotlib, xarray, aiofiles, and the
wx_4panel_charts plotting sub-modules) are patched in sys.modules before the module under
test is imported, so that GDAL / native libraries are never needed during the test run.
"""

import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from enum import Enum
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Build lightweight stand-ins for the enums used by the module under test.
# These must be defined before the module is imported so that the identity
# checks inside wx_4panel_charts.py (e.g.  `chart.status == ChartStatusEnum.INPROGRESS`)
# still work correctly.
# ---------------------------------------------------------------------------


class ECCCModel(str, Enum):
    GDPS = "GDPS"
    RDPS = "RDPS"


class ChartStatusEnum(str, Enum):
    COMPLETE = "complete"
    INPROGRESS = "in_progress"
    FAILED = "failed"


ModelNames = (ECCCModel.GDPS.value, ECCCModel.RDPS.value)


# ---------------------------------------------------------------------------
# Patch sys.modules so that importing the module under test does not trigger
# the GDAL / cartopy / matplotlib native-library chain.
# ---------------------------------------------------------------------------

_wps_shared_models_mock = MagicMock()
_wps_shared_models_mock.ChartStatusEnum = ChartStatusEnum
_wps_shared_models_mock.ECCCModel = ECCCModel
_wps_shared_models_mock.ModelNames = ModelNames

_patches = {
    # wps_shared
    "wps_shared": MagicMock(),
    "wps_shared.db": MagicMock(),
    "wps_shared.db.models": MagicMock(),
    "wps_shared.db.models.wx_4panel_charts": _wps_shared_models_mock,
    "wps_shared.db.crud": MagicMock(),
    "wps_shared.db.crud.wx_4panel_charts": MagicMock(),
    "wps_shared.db.database": MagicMock(),
    "wps_shared.utils": MagicMock(),
    "wps_shared.utils.s3_client": MagicMock(),
    "wps_shared.utils.time": MagicMock(),
    "wps_shared.wps_logging": MagicMock(),
    # native / heavy libs
    "cartopy": MagicMock(),
    "cartopy.crs": MagicMock(),
    "matplotlib": MagicMock(),
    "matplotlib.pyplot": MagicMock(),
    "xarray": MagicMock(),
    "aiofiles": MagicMock(),
    "aiofiles.tempfile": MagicMock(),
    # wx_4panel_charts plotting sub-modules
    "wps_weather.wx_4panel_charts.plot_4panel_gdps": MagicMock(),
    "wps_weather.wx_4panel_charts.plot_4panel_rdps": MagicMock(),
    "wps_weather.wx_4panel_charts.plot_500mb": MagicMock(),
    "wps_weather.wx_4panel_charts.plot_500mb_rdps": MagicMock(),
    "wps_weather.wx_4panel_charts.plot_700mb": MagicMock(),
    "wps_weather.wx_4panel_charts.plot_700mb_rdps": MagicMock(),
    "wps_weather.wx_4panel_charts.plot_mslp": MagicMock(),
    "wps_weather.wx_4panel_charts.plot_mslp_rdps": MagicMock(),
    "wps_weather.wx_4panel_charts.plot_precip": MagicMock(),
    "wps_weather.wx_4panel_charts.plot_precip_rdps": MagicMock(),
    "wps_weather.wx_4panel_charts.panel_layout": MagicMock(),
    "wps_weather.wx_4panel_charts.plotter_factory": MagicMock(),
    "wps_weather.wx_4panel_charts.wx_4panel_chart_addresser": MagicMock(),
    "wps_weather.wx_4panel_charts.config_builder": MagicMock(),
}

# Import the module under test with all heavy dependencies mocked.
# Using patch.dict (rather than setdefault) ensures sys.modules is fully
# restored afterwards so other test files aren't polluted.
with patch.dict("sys.modules", _patches):
    sys.modules.pop("wps_weather.wx_4panel_charts.wx_4panel_charts", None)
    from wps_weather.wx_4panel_charts.wx_4panel_charts import (  # noqa: E402
        FourPanelChartRunner,
        get_init_datetime,
        parse_args,
    )
    _wx4panel_charts_module = sys.modules["wps_weather.wx_4panel_charts.wx_4panel_charts"]

# Re-insert the module into sys.modules and bind it as a package attribute so
# that patch("wps_weather.wx_4panel_charts.wx_4panel_charts.XXX") can resolve
# its target via pkgutil.resolve_name during test execution.
import wps_weather.wx_4panel_charts as _wx4panel_pkg  # noqa: E402

sys.modules["wps_weather.wx_4panel_charts.wx_4panel_charts"] = _wx4panel_charts_module
_wx4panel_pkg.wx_4panel_charts = _wx4panel_charts_module
del _wx4panel_pkg, _wx4panel_charts_module

# Keep direct references to the mocks used inside FourPanelChartRunner so that
# test helpers can configure them without going through sys.modules (which is
# restored to its original state after the patch.dict block above).
_config_builder_mock = _patches["wps_weather.wx_4panel_charts.config_builder"]
_raster_addresser_mock = _patches["wps_weather.wx_4panel_charts.wx_4panel_chart_addresser"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_runner(s3_client=None):
    if s3_client is None:
        s3_client = AsyncMock()
    return FourPanelChartRunner(s3_client)


def make_mock_chart(status=ChartStatusEnum.INPROGRESS):
    chart = AsyncMock()
    chart.status = status
    return chart


def make_mock_configs():
    """Return a 4-tuple of dicts matching the keys that _make_4panel_charts reads."""
    cfg500 = {"z500_grib": "k/z500.grib2", "vort_grib": "k/vort.grib2"}
    cfgmslp = {"mslp_grib": "k/mslp.grib2", "thk_grib": "k/thk.grib2"}
    cfg700 = {
        "z700_grib": "k/z700.grib2",
        "rh500_grib": "k/rh500.grib2",
        "rh700_grib": "k/rh700.grib2",
        "rh850_grib": "k/rh850.grib2",
    }
    cfgpcpn = {
        "show_precip": True,
        "pcpn_grib": "k/pcpn.grib2",
        "show_jet_core": True,
        "jet_spd_grib": "k/jet.grib2",
    }
    return cfg500, cfgmslp, cfg700, cfgpcpn


def new_session_scope():
    """Return a fresh async context manager each call (avoids exhausted-generator errors)."""

    @asynccontextmanager
    async def _scope():
        yield MagicMock()

    return _scope()


# ---------------------------------------------------------------------------
# _open_dataset_s3
# ---------------------------------------------------------------------------


class TestOpenDatasetS3:
    @pytest.mark.anyio
    async def test_raises_runtime_error_on_404_status(self):
        s3_client = MagicMock()
        response = {"ResponseMetadata": {"HTTPStatusCode": 404}, "Body": AsyncMock()}
        s3_client.get_object = AsyncMock(return_value=response)
        runner = make_runner(s3_client)

        with pytest.raises(RuntimeError, match="HTTP status code was: 404"):
            await runner._open_dataset_s3("some/key")

    @pytest.mark.anyio
    async def test_raises_runtime_error_on_500_status(self):
        s3_client = MagicMock()
        response = {"ResponseMetadata": {"HTTPStatusCode": 500}, "Body": AsyncMock()}
        s3_client.get_object = AsyncMock(return_value=response)
        runner = make_runner(s3_client)

        with pytest.raises(RuntimeError, match="HTTP status code was: 500"):
            await runner._open_dataset_s3("some/key")

    @pytest.mark.anyio
    async def test_error_message_includes_key(self):
        s3_client = MagicMock()
        response = {"ResponseMetadata": {"HTTPStatusCode": 403}, "Body": AsyncMock()}
        s3_client.get_object = AsyncMock(return_value=response)
        runner = make_runner(s3_client)

        with pytest.raises(RuntimeError, match="some/specific/key"):
            await runner._open_dataset_s3("some/specific/key")

    @pytest.mark.anyio
    async def test_calls_get_object_with_key(self):
        s3_client = MagicMock()
        response = {"ResponseMetadata": {"HTTPStatusCode": 404}, "Body": AsyncMock()}
        s3_client.get_object = AsyncMock(return_value=response)
        runner = make_runner(s3_client)

        with pytest.raises(RuntimeError):
            await runner._open_dataset_s3("weather/data/file.grib2")

        s3_client.get_object.assert_called_once_with("weather/data/file.grib2")


# ---------------------------------------------------------------------------
# _dataset
# ---------------------------------------------------------------------------

# A real class used as a stand-in for xr.Dataset in isinstance checks below.
_FakeDataset = type("Dataset", (), {})


class TestDataset:
    @pytest.mark.anyio
    async def test_logs_error_and_raises_type_error_when_open_dataset_returns_non_dataset(self):
        runner = make_runner()
        runner._open_dataset_s3 = AsyncMock(return_value="not_a_dataset")

        with patch("wps_weather.wx_4panel_charts.wx_4panel_charts.xr") as mock_xr:
            mock_xr.Dataset = _FakeDataset
            with patch("wps_weather.wx_4panel_charts.wx_4panel_charts.logger") as mock_logger:
                with pytest.raises(TypeError):
                    async with runner._dataset("some/key"):
                        pass

                mock_logger.error.assert_called_once()
                assert "some/key" in mock_logger.error.call_args[0][0]

    @pytest.mark.anyio
    async def test_error_message_includes_actual_type(self):
        runner = make_runner()
        runner._open_dataset_s3 = AsyncMock(return_value=42)

        with patch("wps_weather.wx_4panel_charts.wx_4panel_charts.xr") as mock_xr:
            mock_xr.Dataset = _FakeDataset
            with pytest.raises(TypeError, match="int"):
                async with runner._dataset("some/key"):
                    pass


# ---------------------------------------------------------------------------
# _make_4panel_charts
# ---------------------------------------------------------------------------


class TestMake4PanelCharts:
    def _make_runner(self, object_exists=False, all_objects_exist=True):
        s3_client = MagicMock()
        s3_client.object_exists = AsyncMock(return_value=object_exists)
        s3_client.all_objects_exist = AsyncMock(return_value=all_objects_exist)
        runner = make_runner(s3_client)
        runner._make_4panel_chart = AsyncMock()
        # Make ConfigBuilder() instances return properly shaped configs.
        _config_builder_mock.ConfigBuilder.return_value.build_config_for_hour.return_value = (
            make_mock_configs()
        )
        # Make RasterAddresser().get_4panel_key return a deterministic string key.
        _raster_addresser_mock.WX4PanelChartAddresser.return_value.get_4panel_key.return_value = (
            "4panel/output.png"
        )
        return runner, s3_client

    @pytest.mark.anyio
    async def test_skips_hour_when_output_key_exists(self):
        runner, _ = self._make_runner(object_exists=True)

        result = await runner._make_4panel_charts(ECCCModel.GDPS, "20260318", "00", 3, 3, 3)

        assert result is True
        runner._make_4panel_chart.assert_not_called()

    @pytest.mark.anyio
    async def test_returns_false_when_required_files_missing(self):
        runner, _ = self._make_runner(object_exists=False, all_objects_exist=False)

        result = await runner._make_4panel_charts(ECCCModel.GDPS, "20260318", "00", 3, 3, 3)

        assert result is False
        runner._make_4panel_chart.assert_not_called()

    @pytest.mark.anyio
    async def test_returns_true_when_all_hours_processed(self):
        runner, _ = self._make_runner(object_exists=False, all_objects_exist=True)

        result = await runner._make_4panel_charts(ECCCModel.GDPS, "20260318", "00", 3, 6, 3)

        assert result is True
        assert runner._make_4panel_chart.call_count == 2

    @pytest.mark.anyio
    async def test_returns_true_when_range_is_empty(self):
        # start_hour > end_hour — no hours to process
        runner, _ = self._make_runner()

        result = await runner._make_4panel_charts(ECCCModel.GDPS, "20260318", "00", 10, 3, 3)

        assert result is True
        runner._make_4panel_chart.assert_not_called()

    @pytest.mark.anyio
    async def test_processes_correct_number_of_hours(self):
        runner, _ = self._make_runner(object_exists=False, all_objects_exist=True)

        await runner._make_4panel_charts(ECCCModel.GDPS, "20260318", "00", 0, 9, 3)

        # hours: 0, 3, 6, 9 → 4 charts
        assert runner._make_4panel_chart.call_count == 4

    @pytest.mark.anyio
    async def test_output_name_contains_model_and_date_for_gdps(self):
        runner, _ = self._make_runner(object_exists=False, all_objects_exist=True)
        raster_mock = _raster_addresser_mock.WX4PanelChartAddresser.return_value

        await runner._make_4panel_charts(ECCCModel.GDPS, "20260318", "00", 3, 3, 3)

        # The output filename (second arg to get_4panel_key) should embed model and date.
        output_name = raster_mock.get_4panel_key.call_args[0][1]
        assert "20260318" in output_name
        assert "GDPS" in output_name

    @pytest.mark.anyio
    async def test_output_name_contains_rdps_for_rdps_model(self):
        runner, _ = self._make_runner(object_exists=False, all_objects_exist=True)
        raster_mock = _raster_addresser_mock.WX4PanelChartAddresser.return_value

        await runner._make_4panel_charts(ECCCModel.RDPS, "20260318", "12", 3, 3, 3)

        output_name = raster_mock.get_4panel_key.call_args[0][1]
        assert "RDPS" in output_name

    @pytest.mark.anyio
    async def test_output_key_is_checked_before_generating(self):
        runner, s3_client = self._make_runner(object_exists=False, all_objects_exist=True)

        await runner._make_4panel_charts(ECCCModel.GDPS, "20260318", "00", 3, 3, 3)

        s3_client.object_exists.assert_called_once()
        runner._make_4panel_chart.assert_called_once()

    @pytest.mark.anyio
    async def test_stops_processing_on_missing_files(self):
        runner, _ = self._make_runner(object_exists=False, all_objects_exist=False)

        result = await runner._make_4panel_charts(ECCCModel.GDPS, "20260318", "00", 3, 6, 3)

        assert result is False
        runner._make_4panel_chart.assert_not_called()

    @pytest.mark.anyio
    async def test_continues_to_next_hour_when_make_4panel_chart_raises_type_error(self):
        runner, _ = self._make_runner(object_exists=False, all_objects_exist=True)
        # First hour raises TypeError (e.g. _dataset returned a non-Dataset); second succeeds.
        runner._make_4panel_chart = AsyncMock(side_effect=[TypeError("bad dataset"), None])

        result = await runner._make_4panel_charts(ECCCModel.GDPS, "20260318", "00", 3, 6, 3)

        assert result is True
        assert runner._make_4panel_chart.call_count == 2


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


class TestRun:
    @pytest.mark.anyio
    async def test_raises_value_error_for_unsupported_model(self):
        runner = make_runner()
        with pytest.raises(ValueError, match="Model must be one of"):
            await runner.run("20260318", ["00"], 0, 84, 3, "INVALID_MODEL")

    @pytest.mark.anyio
    async def test_does_not_process_when_chart_status_is_complete(self):
        runner = make_runner()
        chart = make_mock_chart(status=ChartStatusEnum.COMPLETE)
        runner._make_4panel_charts = AsyncMock()

        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_write_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_or_create_processed_four_panel_chart",
                new=AsyncMock(return_value=chart),
            ),
        ):
            await runner.run("20260318", ["00"], 0, 84, 3, ECCCModel.GDPS)

        runner._make_4panel_charts.assert_not_called()

    @pytest.mark.anyio
    async def test_does_not_process_when_chart_is_none(self):
        runner = make_runner()
        runner._make_4panel_charts = AsyncMock()

        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_write_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_or_create_processed_four_panel_chart",
                new=AsyncMock(return_value=None),
            ),
        ):
            await runner.run("20260318", ["00"], 0, 84, 3, ECCCModel.GDPS)

        runner._make_4panel_charts.assert_not_called()

    @pytest.mark.anyio
    async def test_calls_make_4panel_charts_when_inprogress(self):
        runner = make_runner()
        chart = make_mock_chart(status=ChartStatusEnum.INPROGRESS)
        runner._make_4panel_charts = AsyncMock(return_value=True)

        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_write_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_or_create_processed_four_panel_chart",
                new=AsyncMock(return_value=chart),
            ),
            patch("wps_weather.wx_4panel_charts.wx_4panel_charts.save_four_panel_chart"),
        ):
            await runner.run("20260318", ["00"], 0, 84, 3, ECCCModel.GDPS)

        runner._make_4panel_charts.assert_called_once_with(ECCCModel.GDPS, "20260318", "00", 0, 84, 3)

    @pytest.mark.anyio
    async def test_sets_chart_status_to_complete_on_success(self):
        runner = make_runner()
        chart = make_mock_chart(status=ChartStatusEnum.INPROGRESS)
        runner._make_4panel_charts = AsyncMock(return_value=True)

        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_write_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_or_create_processed_four_panel_chart",
                new=AsyncMock(return_value=chart),
            ),
            patch("wps_weather.wx_4panel_charts.wx_4panel_charts.save_four_panel_chart"),
        ):
            await runner.run("20260318", ["00"], 0, 84, 3, ECCCModel.GDPS)

        assert chart.status == ChartStatusEnum.COMPLETE

    @pytest.mark.anyio
    async def test_saves_chart_when_complete(self):
        runner = make_runner()
        chart = make_mock_chart(status=ChartStatusEnum.INPROGRESS)
        runner._make_4panel_charts = AsyncMock(return_value=True)

        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_write_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_or_create_processed_four_panel_chart",
                new=AsyncMock(return_value=chart),
            ),
            patch("wps_weather.wx_4panel_charts.wx_4panel_charts.save_four_panel_chart") as mock_save,
        ):
            await runner.run("20260318", ["00"], 0, 84, 3, ECCCModel.GDPS)

        mock_save.assert_called_once()

    @pytest.mark.anyio
    async def test_does_not_save_chart_when_make_charts_returns_false(self):
        runner = make_runner()
        chart = make_mock_chart(status=ChartStatusEnum.INPROGRESS)
        runner._make_4panel_charts = AsyncMock(return_value=False)

        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_write_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_or_create_processed_four_panel_chart",
                new=AsyncMock(return_value=chart),
            ),
        ):
            await runner.run("20260318", ["00"], 0, 84, 3, ECCCModel.GDPS)

        assert chart.status != ChartStatusEnum.COMPLETE

    @pytest.mark.anyio
    async def test_processes_each_model_run_hour(self):
        runner = make_runner()
        # Use a fresh INPROGRESS chart for each model-run hour so the first iteration's
        # status mutation (→ COMPLETE) doesn't suppress the second iteration.
        runner._make_4panel_charts = AsyncMock(return_value=True)

        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_write_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_or_create_processed_four_panel_chart",
                new=AsyncMock(
                    side_effect=[
                        make_mock_chart(status=ChartStatusEnum.INPROGRESS),
                        make_mock_chart(status=ChartStatusEnum.INPROGRESS),
                    ]
                ),
            ),
            patch("wps_weather.wx_4panel_charts.wx_4panel_charts.save_four_panel_chart"),
        ):
            await runner.run("20260318", ["00", "12"], 0, 84, 3, ECCCModel.GDPS)

        assert runner._make_4panel_charts.call_count == 2
        calls = runner._make_4panel_charts.call_args_list
        assert calls[0] == call(ECCCModel.GDPS, "20260318", "00", 0, 84, 3)
        assert calls[1] == call(ECCCModel.GDPS, "20260318", "12", 0, 84, 3)

    @pytest.mark.anyio
    async def test_does_not_process_when_chart_status_is_failed(self):
        runner = make_runner()
        chart = make_mock_chart(status=ChartStatusEnum.FAILED)
        runner._make_4panel_charts = AsyncMock()

        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_write_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_or_create_processed_four_panel_chart",
                new=AsyncMock(return_value=chart),
            ),
        ):
            await runner.run("20260318", ["00"], 0, 84, 3, ECCCModel.GDPS)

        runner._make_4panel_charts.assert_not_called()


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------


class TestParseArgs:
    def test_default_model_runs_is_00_and_12(self):
        with patch("sys.argv", ["prog", "--init_ymd", "20260318"]):
            args = parse_args()
        assert args.model_runs == ["00", "12"]

    def test_default_start_hour_is_zero(self):
        with patch("sys.argv", ["prog", "--init_ymd", "20260318"]):
            args = parse_args()
        assert args.start_hour == 0

    def test_default_end_hour_is_84(self):
        with patch("sys.argv", ["prog", "--init_ymd", "20260318"]):
            args = parse_args()
        assert args.end_hour == 84

    def test_default_step_is_3(self):
        with patch("sys.argv", ["prog", "--init_ymd", "20260318"]):
            args = parse_args()
        assert args.step == 3

    def test_default_model_is_rdps(self):
        with patch("sys.argv", ["prog", "--init_ymd", "20260318"]):
            args = parse_args()
        assert args.model == "RDPS"

    def test_explicit_model_runs_00_and_12_accepted(self):
        with patch("sys.argv", ["prog", "--init_ymd", "20260318", "--model_runs", "00", "12"]):
            args = parse_args()
        assert args.model_runs == ["00", "12"]

    def test_explicit_start_hour_end_hour_step(self):
        with patch(
            "sys.argv",
            ["prog", "--init_ymd", "20260318", "--start_hour", "6", "--end_hour", "48", "--step", "6"],
        ):
            args = parse_args()
        assert args.start_hour == 6
        assert args.end_hour == 48
        assert args.step == 6

    def test_gdps_model_accepted(self):
        with patch("sys.argv", ["prog", "--init_ymd", "20260318", "--model", "GDPS"]):
            args = parse_args()
        assert args.model == "GDPS"

    def test_init_ymd_stored_correctly(self):
        with patch("sys.argv", ["prog", "--init_ymd", "20260318"]):
            args = parse_args()
        assert args.init_ymd == "20260318"


    def test_invalid_model_runs_rejected(self):
        with patch("sys.argv", ["prog", "--init_ymd", "20260318", "--model_runs", "06"]):
            with pytest.raises(SystemExit):
                parse_args()

    def test_invalid_model_rejected(self):
        with patch("sys.argv", ["prog", "--init_ymd", "20260318", "--model", "HRDPS"]):
            with pytest.raises(SystemExit):
                parse_args()


# ---------------------------------------------------------------------------
# get_init_datetime
# ---------------------------------------------------------------------------

_FIXED_NOW = datetime(2026, 3, 26, 15, 30, 45, tzinfo=timezone.utc)
_FIXED_NOW_MIDNIGHT = _FIXED_NOW.replace(hour=0, minute=0, second=0, microsecond=0)


def _make_db_result(timestamp: datetime):
    result = MagicMock()
    result.model_run_timestamp = timestamp
    return result


class TestGetInitDatetime:
    @pytest.mark.anyio
    async def test_returns_incomplete_timestamp_when_in_progress_found(self):
        incomplete_ts = datetime(2026, 3, 24, 12, 0, 0, tzinfo=timezone.utc)
        incomplete = _make_db_result(incomplete_ts)

        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_read_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_utc_now",
                return_value=_FIXED_NOW,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_earliest_in_progress_date_limited",
                new=AsyncMock(return_value=incomplete),
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_last_complete",
                new=AsyncMock(return_value=None),
            ),
        ):
            result = await get_init_datetime()

        assert result == incomplete_ts.replace(hour=0, minute=0, second=0, microsecond=0)

    @pytest.mark.anyio
    async def test_result_is_always_zeroed_to_midnight(self):
        incomplete_ts = datetime(2026, 3, 24, 18, 45, 59, 999999, tzinfo=timezone.utc)
        incomplete = _make_db_result(incomplete_ts)

        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_read_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_utc_now",
                return_value=_FIXED_NOW,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_earliest_in_progress_date_limited",
                new=AsyncMock(return_value=incomplete),
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_last_complete",
                new=AsyncMock(return_value=None),
            ),
        ):
            result = await get_init_datetime()

        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.microsecond == 0

    @pytest.mark.anyio
    async def test_returns_last_complete_plus_one_day_when_no_incomplete(self):
        last_complete_ts = datetime(2026, 3, 25, 0, 0, 0, tzinfo=timezone.utc)
        last_complete = _make_db_result(last_complete_ts)

        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_read_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_utc_now",
                return_value=_FIXED_NOW,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_earliest_in_progress_date_limited",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_last_complete",
                new=AsyncMock(return_value=last_complete),
            ),
        ):
            result = await get_init_datetime()

        assert result == last_complete_ts + timedelta(days=1)

    @pytest.mark.anyio
    async def test_returns_today_midnight_when_both_results_are_none(self):
        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_read_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_utc_now",
                return_value=_FIXED_NOW,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_earliest_in_progress_date_limited",
                new=AsyncMock(return_value=None),
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_last_complete",
                new=AsyncMock(return_value=None),
            ),
        ):
            result = await get_init_datetime()

        assert result == _FIXED_NOW_MIDNIGHT

    @pytest.mark.anyio
    async def test_passes_min_date_seven_days_before_now_to_incomplete_query(self):
        incomplete = _make_db_result(datetime(2026, 3, 25, 0, 0, 0, tzinfo=timezone.utc))

        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_read_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_utc_now",
                return_value=_FIXED_NOW,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_earliest_in_progress_date_limited",
                new=AsyncMock(return_value=incomplete),
            ) as mock_incomplete,
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_last_complete",
                new=AsyncMock(return_value=None),
            ),
        ):
            await get_init_datetime()

        expected_min_date = _FIXED_NOW_MIDNIGHT - timedelta(days=7)
        actual_min_date = mock_incomplete.call_args[0][1]
        assert actual_min_date == expected_min_date

    @pytest.mark.anyio
    async def test_incomplete_query_takes_priority_over_last_complete(self):
        incomplete_ts = datetime(2026, 3, 24, 0, 0, 0, tzinfo=timezone.utc)
        last_complete_ts = datetime(2026, 3, 25, 0, 0, 0, tzinfo=timezone.utc)
        incomplete = _make_db_result(incomplete_ts)
        last_complete = _make_db_result(last_complete_ts)

        with (
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_async_read_session_scope",
                side_effect=new_session_scope,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_utc_now",
                return_value=_FIXED_NOW,
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_earliest_in_progress_date_limited",
                new=AsyncMock(return_value=incomplete),
            ),
            patch(
                "wps_weather.wx_4panel_charts.wx_4panel_charts.get_last_complete",
                new=AsyncMock(return_value=last_complete),
            ) as mock_last_complete,
        ):
            result = await get_init_datetime()

        # When incomplete exists, get_last_complete should not be called at all.
        mock_last_complete.assert_not_called()
        assert result == incomplete_ts.replace(hour=0, minute=0, second=0, microsecond=0)
