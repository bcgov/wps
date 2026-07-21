"""
Extends profile_ml_interpolation_growth.py to cover two gaps that test left
open:

1. StationMachineLearning._learn_models queries the full MAX_DAYS_TO_LEARN=19
   days (~456 hours) of HourlyActual history per station. The earlier test
   only seeded 72 hours (~3 days) -- about 1/6th the real per-station query
   volume.

2. ModelValueProcessor.process()'s outer loop interpolates EVERY currently
   "complete=True, interpolated=False" model run it finds in one call, not
   just one. If a backlog had built up (e.g. from earlier failed/killed
   runs), that multiplies the whole per-station workload by however many
   runs are backlogged, all within calls that share the same session -- the
   earlier test only ever exercised exactly one model run.

No network calls to the real ECCC servers -- this is pure Postgres, using
the local DB already set up for the other profiling scripts in this
investigation.

Usage:
    uv run --package wps-jobs python -m weather_model_jobs.profile_ml_backlog_growth \\
        --stations 300 --backlog-runs 4 --sample-every 25
"""

import argparse
import random
from datetime import datetime, timedelta, timezone

import weather_model_jobs.common_model_fetchers as common_fetchers_module
from weather_model_jobs.common_model_fetchers import ModelValueProcessor
from wps_shared.db.crud.weather_models import (
    get_or_create_prediction_run,
    get_prediction_model,
    get_prediction_model_run_timestamp_records,
)
from wps_shared.db.database import get_write_session_scope
from wps_shared.db.models.observations import HourlyActual
from wps_shared.db.models.weather_models import ModelRunPrediction
from wps_shared.weather_models import ModelEnum, ProjectionEnum

BASE_STATION_CODE = 900_000
MAX_DAYS_TO_LEARN_HOURS = 19 * 24  # matches weather_model_jobs.machine_learning.MAX_DAYS_TO_LEARN
PREDICTIONS_PER_RUN = 16  # hourly-spaced predictions per station per backlogged run


class _FakeStation:
    def __init__(self, code, lat, long, name):
        self.code = code
        self.lat = lat
        self.long = long
        self.name = name


def _install_stubs():
    common_fetchers_module.get_stations_synchronously = lambda: []


def _rss_mb() -> float:
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except FileNotFoundError:
        pass
    import psutil

    return psutil.Process().memory_info().rss / (1024 * 1024)


def _seed_actuals(station_count: int, hours: int):
    """Seed the FULL 19-day HourlyActual history per station (not the earlier test's 72h)."""
    rng = random.Random(42)
    base_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) - timedelta(hours=hours)

    with get_write_session_scope() as session:
        session.query(HourlyActual).filter(HourlyActual.station_code >= BASE_STATION_CODE).delete()
        session.flush()

        for i in range(station_count):
            station_code = BASE_STATION_CODE + i
            for h in range(hours):
                weather_date = base_time + timedelta(hours=h)
                session.add(
                    HourlyActual(
                        weather_date=weather_date,
                        station_code=station_code,
                        temp_valid=True,
                        temperature=15.0 + rng.uniform(-5, 5),
                        rh_valid=True,
                        relative_humidity=50.0 + rng.uniform(-10, 10),
                        wdir_valid=True,
                        wind_direction=rng.uniform(0, 360),
                        wspeed_valid=True,
                        wind_speed=rng.uniform(0, 20),
                        precip_valid=True,
                        precipitation=0.0,
                    )
                )
            if i % 25 == 0:
                session.flush()
        print(f"seeded {station_count} stations x {hours}h ({hours / 24:.0f} days) of HourlyActual history")


def _seed_backlog_runs(station_count: int, backlog_runs: int):
    """Create `backlog_runs` distinct, already-complete-but-uninterpolated model runs, each
    with its own ModelRunPrediction rows per station, all falling inside the seeded
    HourlyActual window so _learn_models' join finds real matches."""
    with get_write_session_scope() as session:
        session.query(ModelRunPrediction).filter(ModelRunPrediction.station_code >= BASE_STATION_CODE).delete()
        session.flush()

        prediction_model = get_prediction_model(session, ModelEnum.HRDPS, ProjectionEnum.HRDPS_LATLON)
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        rng = random.Random(43)

        model_run_ids = []
        for r in range(backlog_runs):
            run_timestamp = now - timedelta(hours=6 * r)
            prediction_run = get_or_create_prediction_run(session, prediction_model, run_timestamp)
            prediction_run.complete = True
            prediction_run.interpolated = False
            session.add(prediction_run)
            session.flush()
            model_run_ids.append(prediction_run.id)

            for i in range(station_count):
                station_code = BASE_STATION_CODE + i
                for h in range(PREDICTIONS_PER_RUN):
                    # Entirely in the past relative to `now`, inside the seeded HourlyActual
                    # window, so training pairs actually exist -- realism of forecast-vs-actual
                    # timing doesn't matter for a memory test, only real data volume does.
                    prediction_timestamp = run_timestamp - timedelta(hours=h)
                    session.add(
                        ModelRunPrediction(
                            prediction_model_run_timestamp_id=prediction_run.id,
                            prediction_timestamp=prediction_timestamp,
                            station_code=station_code,
                            tmp_tgl_2=15.0 + rng.uniform(-5, 5),
                            rh_tgl_2=50.0 + rng.uniform(-10, 10),
                            apcp_sfc_0=0.0,
                            wdir_tgl_10=rng.uniform(0, 360),
                            wind_tgl_10=rng.uniform(0, 20),
                        )
                    )
                if i % 25 == 0:
                    session.flush()
        print(f"seeded {backlog_runs} backlogged model runs x {station_count} stations x {PREDICTIONS_PER_RUN} predictions each")
        return model_run_ids


def main():
    parser = argparse.ArgumentParser(description="Test ModelValueProcessor memory across a backlog of model runs, full 19-day history.")
    parser.add_argument("--stations", type=int, default=300)
    parser.add_argument("--backlog-runs", type=int, default=4)
    parser.add_argument("--history-hours", type=int, default=MAX_DAYS_TO_LEARN_HOURS)
    parser.add_argument("--sample-every", type=int, default=25, help="Print RSS every N stations within a run.")
    args = parser.parse_args()

    _install_stubs()
    _seed_actuals(args.stations, args.history_hours)
    _seed_backlog_runs(args.stations, args.backlog_runs)

    print(f"RSS before interpolation: {_rss_mb():.1f} MB")

    with get_write_session_scope() as session:
        mvp = ModelValueProcessor(session)
        query = get_prediction_model_run_timestamp_records(
            session, complete=True, interpolated=False, model_type=ModelEnum.HRDPS
        )
        runs = list(query)
        print(f"{len(runs)} backlogged model runs found to interpolate")

        for run_idx, (model_run, _model) in enumerate(runs, start=1):
            for i in range(args.stations):
                station_code = BASE_STATION_CODE + i
                station = _FakeStation(code=station_code, lat=49.0, long=-123.0, name=f"profile-station-{i}")
                mvp._process_model_run_for_station(model_run, station, ModelEnum.HRDPS)

                if (i + 1) % args.sample_every == 0:
                    print(f"[run {run_idx}/{len(runs)} station {i + 1:>4}/{args.stations}] RSS: {_rss_mb():.1f} MB")

            # Mirrors _process_model_run's own end-of-run commit.
            session.commit()
            print(f"[run {run_idx}/{len(runs)} complete] RSS: {_rss_mb():.1f} MB")


if __name__ == "__main__":
    main()
