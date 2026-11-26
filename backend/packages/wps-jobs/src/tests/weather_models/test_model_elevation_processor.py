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
    assert [(row.station_code, row.elevation) for row in rows] == [
        (2, 1234.57),
        (3, None),
        (4, None),
        (5, None),
    ]
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


@pytest.mark.parametrize("elevation", [1234.5, None])
def test_samples_are_saved(elevation: float | None) -> None:
    session = session_with_stations([1], [])
    elevation_sampler = Mock()
    elevation_sampler.download_and_sample.return_value = {1: elevation}
    ingestion.ModelElevationProcessor(session, [station(1)]).process_run(
        run_record(), "RDPS", elevation_sampler
    )
    assert session.add_all.call_args.args[0][0].elevation == elevation


def test_missing_station_metadata_does_not_download_a_surface_field() -> None:
    session = session_with_stations([1], [])
    elevation_sampler = Mock()
    ingestion.ModelElevationProcessor(session, []).process_run(
        run_record(), "GDPS", elevation_sampler
    )
    elevation_sampler.download_and_sample.assert_not_called()
    assert session.add_all.call_args.args[0][0].elevation is None


def test_download_failure_does_not_save_assignments() -> None:
    session = session_with_stations([1], [])
    elevation_sampler = Mock()
    elevation_sampler.download_and_sample.side_effect = OSError("unavailable")
    with pytest.raises(OSError, match="unavailable"):
        ingestion.ModelElevationProcessor(session, [station(1)]).process_run(
            run_record(), "GFS", elevation_sampler
        )
    session.add_all.assert_not_called()
    session.flush.assert_not_called()


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


def test_run_failure_preserves_exception_with_context_for_chatops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    select_runs = Mock()
    runs = [run_record(1), run_record(2)]
    select_runs.return_value.all.return_value = [(run, None) for run in runs]
    monkeypatch.setattr(ingestion, "get_prediction_model_run_timestamp_records", select_runs)
    processor = ingestion.ModelElevationProcessor(MagicMock(), [station(1)])
    error = OSError("surface unavailable")
    process_run = Mock(side_effect=error)
    monkeypatch.setattr(processor, "process_run", process_run)

    with pytest.raises(OSError, match="surface unavailable") as raised:
        processor.process(ModelEnum.HRDPS)

    assert raised.value is error
    formatted = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    assert "surface unavailable" in formatted
    assert (
        f"Station elevation processing failed for HRDPS initialization {RUN.isoformat()}"
        in formatted
    )
    process_run.assert_called_once()
    assert process_run.call_args.args[:2] == (runs[0], "HRDPS")


def test_nam_does_not_collect_elevations(monkeypatch: pytest.MonkeyPatch) -> None:
    select_runs = Mock()
    monkeypatch.setattr(ingestion, "get_prediction_model_run_timestamp_records", select_runs)
    ingestion.ModelElevationProcessor(MagicMock(), []).process(ModelEnum.NAM)
    select_runs.assert_not_called()


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
    weather = MagicMock()
    weather.process.side_effect = lambda: events.append("weather")
    monkeypatch.setattr(module, job_class, Mock(return_value=weather))
    monkeypatch.setattr(module, "judge_run", Mock(return_value=1))
    elevation = Mock()

    def collect(model_type: ModelEnum) -> None:
        events.append("elevation")
        if fail:
            raise OSError("unavailable")

    elevation.process.side_effect = collect
    constructor = Mock(return_value=elevation)
    monkeypatch.setattr(module, "ModelElevationProcessor", constructor)
    interpolation = Mock()
    interpolation.process.side_effect = lambda _: events.append("interpolation")
    monkeypatch.setattr(module, "ModelValueProcessor", Mock(return_value=interpolation))
    if fail:
        with pytest.raises(OSError, match="unavailable"):
            module.process_models()
        assert events == ["weather", "elevation"]
    else:
        module.process_models()
        assert events == ["weather", "elevation", "interpolation"]
    assert constructor.call_args.args[1] is weather.grib_processor.stations


@pytest.mark.anyio
@pytest.mark.parametrize("fail", [False, True])
async def test_ecmwf_collects_elevations_before_interpolation(
    monkeypatch: pytest.MonkeyPatch, fail: bool
) -> None:
    module = importlib.import_module("weather_model_jobs.ecmwf")
    events = []

    async def stations() -> list[WeatherStation]:
        return [station(1)]

    monkeypatch.setattr(module, "get_stations_asynchronously", stations)
    weather = Mock()
    weather.process.side_effect = lambda: events.append("weather")
    monkeypatch.setattr(module, "ECMWF", Mock(return_value=weather))
    elevation = Mock()

    def collect(model_type: ModelEnum) -> None:
        events.append("elevation")
        if fail:
            raise OSError("unavailable")

    elevation.process.side_effect = collect
    monkeypatch.setattr(module, "ModelElevationProcessor", Mock(return_value=elevation))
    interpolation = Mock()
    interpolation.process.side_effect = lambda: events.append("interpolation")
    monkeypatch.setattr(module, "ECMWFPredictionProcessor", Mock(return_value=interpolation))
    if fail:
        with pytest.raises(OSError, match="unavailable"):
            await module.process_models()
        assert events == ["weather", "elevation"]
    else:
        await module.process_models()
        assert events == ["weather", "elevation", "interpolation"]
