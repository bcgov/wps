import importlib
import traceback
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock

import pytest
from weather_model_jobs import model_elevation_processor as ingestion
from wps_shared.db.models.weather_models import PredictionModelRunTimestamp
from wps_shared.schemas.stations import WeatherStation
from wps_shared.weather_models import ModelEnum

RUN = datetime(2026, 11, 16, tzinfo=timezone.utc)


def station(code: int) -> WeatherStation:
    return WeatherStation(code=code, name=f"Station {code}", lat=50.9, long=-129.9)


def session_with_stations(weather_codes: list[int], saved_codes: list[int]) -> MagicMock:
    session = MagicMock()
    session.scalars.side_effect = [weather_codes, saved_codes]
    return session


def run_record(run_id: int = 1) -> PredictionModelRunTimestamp:
    return PredictionModelRunTimestamp(id=run_id, prediction_run_timestamp=RUN)


def test_only_missing_weather_stations_get_assignments() -> None:
    session = session_with_stations([1, 2, 3, 5, 4], [1])
    elevation_sampler = Mock()
    elevation_sampler.download_and_sample.return_value = {2: 1234.56789, 3: None}
    stations = [station(1), station(2), station(3), station(6)]
    processor = ingestion.ModelElevationProcessor(session, stations)
    processor.process_run(run_record(), "HRDPS", elevation_sampler)
    elevation_sampler.download_and_sample.assert_called_once_with("HRDPS", RUN, stations[1:3])
    rows = session.add_all.call_args.args[0]
    assert [(row.station_code, row.elevation) for row in rows] == [(2, 1234.57)]
    assert all(row.prediction_model_run_timestamp_id == 1 for row in rows)
    session.flush.assert_called_once()
    session.commit.assert_not_called()


@pytest.mark.parametrize("weather_codes,saved_codes", [([1], [1]), ([], [])])
def test_saved_assignments_skip_downloads_even_when_the_elevation_was_null(
    weather_codes: list[int], saved_codes: list[int]
) -> None:
    session = session_with_stations(weather_codes, saved_codes)
    elevation_sampler = Mock()
    ingestion.ModelElevationProcessor(session, [station(1)]).process_run(
        run_record(), "GFS", elevation_sampler
    )
    elevation_sampler.download_and_sample.assert_not_called()
    session.add_all.assert_not_called()
    session.flush.assert_not_called()


@pytest.mark.parametrize("elevation", [1234.5, 0.0])
def test_samples_are_saved(elevation: float) -> None:
    session = session_with_stations([1], [])
    elevation_sampler = Mock()
    elevation_sampler.download_and_sample.return_value = {1: elevation}
    ingestion.ModelElevationProcessor(session, [station(1)]).process_run(
        run_record(), "RDPS", elevation_sampler
    )
    assert session.add_all.call_args.args[0][0].elevation == elevation


def test_null_sample_does_not_save_or_flush() -> None:
    session = session_with_stations([1], [])
    elevation_sampler = Mock()
    elevation_sampler.download_and_sample.return_value = {1: None}
    ingestion.ModelElevationProcessor(session, [station(1)]).process_run(
        run_record(), "RDPS", elevation_sampler
    )
    session.add_all.assert_not_called()
    session.flush.assert_not_called()


def test_missing_station_metadata_does_not_download_a_surface_field() -> None:
    session = session_with_stations([1], [])
    elevation_sampler = Mock()
    ingestion.ModelElevationProcessor(session, []).process_run(
        run_record(), "GDPS", elevation_sampler
    )
    elevation_sampler.download_and_sample.assert_not_called()
    session.add_all.assert_not_called()
    session.flush.assert_not_called()


@pytest.mark.parametrize("error", [OSError("unavailable"), ValueError("invalid surface")])
def test_sampler_failure_does_not_save_assignments(error: Exception, caplog) -> None:
    session = session_with_stations([1], [])
    elevation_sampler = Mock()
    elevation_sampler.download_and_sample.side_effect = error
    ingestion.ModelElevationProcessor(session, [station(1)]).process_run(
        run_record(), "GFS", elevation_sampler
    )
    session.add_all.assert_not_called()
    session.flush.assert_not_called()
    session.commit.assert_not_called()
    assert (
        f"Station elevation sampling failed model=GFS initialization={RUN.isoformat()}"
        in caplog.text
    )
    assert caplog.records[0].exc_info[1] is error


def test_failed_older_run_does_not_block_newer_run(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock()
    session.scalars.side_effect = [[1], [], [1], []]
    older = run_record(1)
    newer = run_record(2)
    newer.prediction_run_timestamp = RUN.replace(hour=12)
    select_runs = Mock()
    select_runs.return_value.all.return_value = [(older, None), (newer, None)]
    monkeypatch.setattr(ingestion, "get_prediction_model_run_timestamp_records", select_runs)
    sample = Mock(side_effect=[OSError("unavailable"), {1: 1234.5}])
    monkeypatch.setattr(ingestion.ModelElevationSampler, "download_and_sample", sample)

    ingestion.ModelElevationProcessor(session, [station(1)]).process(ModelEnum.GFS)

    rows = [row for call in session.add_all.call_args_list for row in call.args[0]]
    assert [(row.prediction_model_run_timestamp_id, row.elevation) for row in rows] == [
        (2, 1234.5),
    ]
    assert [call.args[1] for call in sample.call_args_list] == [RUN, newer.prediction_run_timestamp]
    session.flush.assert_called_once()


def test_processor_selects_pending_runs_and_cleans_up_temporary_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    select_runs = Mock()
    runs = [run_record(1), run_record(2)]
    select_runs.return_value.all.return_value = [(run, None) for run in runs]
    monkeypatch.setattr(ingestion, "get_prediction_model_run_timestamp_records", select_runs)
    processor = ingestion.ModelElevationProcessor(session, [station(1)])
    directories = []

    def process_run(
        run: PredictionModelRunTimestamp,
        model: str,
        elevation_sampler: ingestion.ModelElevationSampler,
    ) -> None:
        assert run in runs
        assert model == "HRDPS"
        directories.append(elevation_sampler.directory)
        (elevation_sampler.directory / f"{run.id}.grib2").write_bytes(b"temporary")

    monkeypatch.setattr(processor, "process_run", process_run)
    processor.process(ModelEnum.HRDPS)
    select_runs.assert_called_once_with(
        session, model_type=ModelEnum.HRDPS, complete=True, interpolated=False
    )
    assert len(directories) == 2
    assert directories[0] == directories[1]
    assert not directories[0].exists()


def test_database_failure_preserves_exception_with_context_for_chatops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    select_runs = Mock()
    runs = [run_record(1), run_record(2)]
    select_runs.return_value.all.return_value = [(run, None) for run in runs]
    monkeypatch.setattr(ingestion, "get_prediction_model_run_timestamp_records", select_runs)
    session = session_with_stations([1], [])
    processor = ingestion.ModelElevationProcessor(session, [station(1)])
    error = RuntimeError("database unavailable")
    session.flush.side_effect = error
    sample = Mock(return_value={1: 1234.5})
    monkeypatch.setattr(ingestion.ModelElevationSampler, "download_and_sample", sample)

    with pytest.raises(RuntimeError, match="database unavailable") as raised:
        processor.process(ModelEnum.HRDPS)

    assert raised.value is error
    formatted = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    assert "database unavailable" in formatted
    assert (
        f"Station elevation processing failed for HRDPS initialization {RUN.isoformat()}"
        in formatted
    )
    sample.assert_called_once()
    session.flush.assert_called_once()


def test_nam_does_not_collect_elevations(monkeypatch: pytest.MonkeyPatch) -> None:
    select_runs = Mock()
    monkeypatch.setattr(ingestion, "get_prediction_model_run_timestamp_records", select_runs)
    ingestion.ModelElevationProcessor(MagicMock(), []).process(ModelEnum.NAM)
    select_runs.assert_not_called()


def prepare_job_elevations(
    monkeypatch: pytest.MonkeyPatch, events: list[str], fail: bool
) -> MagicMock:
    session = session_with_stations([1], [])
    monkeypatch.setattr("wps_shared.db.database._get_write_session", lambda: session)
    select_runs = Mock()
    select_runs.return_value.all.return_value = [(run_record(), None)]
    monkeypatch.setattr(ingestion, "get_prediction_model_run_timestamp_records", select_runs)

    def sample(*args) -> dict[int, float]:
        events.append("elevation")
        if fail:
            raise OSError("unavailable")
        return {1: 1234.5}

    monkeypatch.setattr(ingestion.ModelElevationSampler, "download_and_sample", sample)
    return session


@pytest.mark.parametrize(
    "module_name,job_class,model",
    [
        ("env_canada", "EnvCanada", "HRDPS"),
        ("noaa", "NOAA", "GFS"),
    ],
)
@pytest.mark.parametrize("fail", [False, True])
def test_weather_jobs_collect_elevations_before_interpolation(
    monkeypatch: pytest.MonkeyPatch, module_name: str, job_class: str, model: str, fail: bool
) -> None:
    module = importlib.import_module(f"weather_model_jobs.{module_name}")
    monkeypatch.setattr(module.sys, "argv", [module_name, model])
    events = []
    session = prepare_job_elevations(monkeypatch, events, fail)
    weather = MagicMock()
    weather.grib_processor.stations = [station(1)]
    weather.process.side_effect = lambda: events.append("weather")
    monkeypatch.setattr(module, job_class, Mock(return_value=weather))
    monkeypatch.setattr(module, "judge_run", Mock(return_value=1))
    interpolation = Mock()
    interpolation.process.side_effect = lambda _: events.append("interpolation")
    monkeypatch.setattr(module, "ModelValueProcessor", Mock(return_value=interpolation))
    module.process_models()
    assert events == ["weather", "elevation", "interpolation"]
    if fail:
        session.add_all.assert_not_called()
        session.flush.assert_not_called()
    else:
        assert session.add_all.call_args.args[0][0].elevation == 1234.5
    session.commit.assert_called_once()


@pytest.mark.anyio
@pytest.mark.parametrize("fail", [False, True])
async def test_ecmwf_collects_elevations_before_interpolation(
    monkeypatch: pytest.MonkeyPatch, fail: bool
) -> None:
    module = importlib.import_module("weather_model_jobs.ecmwf")
    events = []
    session = prepare_job_elevations(monkeypatch, events, fail)

    async def stations() -> list[WeatherStation]:
        return [station(1)]

    monkeypatch.setattr(module, "get_stations_asynchronously", stations)
    weather = Mock()
    weather.model_type = ModelEnum.ECMWF
    weather.process.side_effect = lambda: events.append("weather")
    monkeypatch.setattr(module, "ECMWF", Mock(return_value=weather))
    interpolation = Mock()
    interpolation.process.side_effect = lambda: events.append("interpolation")
    monkeypatch.setattr(module, "ECMWFPredictionProcessor", Mock(return_value=interpolation))
    await module.process_models()
    assert events == ["weather", "elevation", "interpolation"]
    if fail:
        session.add_all.assert_not_called()
        session.flush.assert_not_called()
    else:
        assert session.add_all.call_args.args[0][0].elevation == 1234.5
    session.commit.assert_called_once()
