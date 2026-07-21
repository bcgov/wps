"""
Fast, isolated test of memory growth in ModelValueProcessor's per-station
interpolation/ML loop (the second phase of process_models(), which runs in
the SAME process and the SAME un-committed-until-the-end session as
EnvCanada.process()).

_process_model_run_for_station() builds a brand new StationMachineLearning
per station -- which materializes ~19 days of HourlyActual/ModelRunPrediction
rows via `list(query)` and fits up to ~24 hourly x 3 variable sklearn
LinearRegression models, plus a v2 wind-direction/precip model -- then reads
and writes WeatherStationModelPrediction rows, all against ONE shared
session whose identity map is never expunged until _process_model_run's
single commit() after ALL stations are done. With real WFWX station counts
approaching WFWX_MAX_PAGE_SIZE=1000, that's up to ~1000 rounds of query
materialization + sklearn model construction sitting in memory at once.

This script seeds a small, realistic dataset for N synthetic stations, then
drives _process_model_run_for_station directly (skipping the outer
per-station logging loop and its own commit -- same as production, where the
commit only happens after every station in the run has been processed) while
sampling RSS, to see whether memory grows with station count.

Setup: uses your existing local Postgres (the one profile_hrdps_memory.py
and profile_hrdps_session_growth.py already ran against) -- no extra setup
needed as long as `HRDPS` exists in prediction_models (it already does).

Usage:
    uv run --package wps-jobs python -m weather_model_jobs.profile_ml_interpolation_growth \\
        --stations 500 --hours 72 --sample-every 25
"""

import argparse
import random
import resource
import sys
from datetime import datetime, timedelta, timezone

import weather_model_jobs.common_model_fetchers as common_fetchers_module
from weather_model_jobs.common_model_fetchers import ModelValueProcessor
from wps_shared.db.crud.weather_models import get_or_create_prediction_run, get_prediction_model
from wps_shared.db.database import get_write_session_scope
from wps_shared.db.models.observations import HourlyActual
from wps_shared.db.models.weather_models import ModelRunPrediction
from wps_shared.weather_models import ModelEnum, ProjectionEnum

BASE_STATION_CODE = 900_000


class _FakeStation:
    def __init__(self, code, lat, long, name):
        self.code = code
        self.lat = lat
        self.long = long
        self.name = name


def _install_stubs():
    # ModelValueProcessor.__init__ calls get_stations_synchronously once; its result isn't
    # used by _process_model_run_for_station when we call it directly, but __init__ still
    # needs to succeed without live WFWX credentials.
    common_fetchers_module.get_stations_synchronously = lambda: []


def _rss_mb() -> float:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024


def _seed(station_count: int, hours: int, model_run_id: int):
    """Seed matching HourlyActual + ModelRunPrediction rows for N synthetic stations, in a
    separate session/transaction so the seed writes don't pollute the profiling baseline."""
    rng = random.Random(42)
    base_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) - timedelta(hours=hours)

    with get_write_session_scope() as session:
        # Idempotent: clear out any synthetic rows left over from a previous run of this
        # script before re-seeding, since the "last N hours" window shifts every run and
        # would otherwise collide with (weather_date, station_code) from earlier runs.
        session.query(HourlyActual).filter(HourlyActual.station_code >= BASE_STATION_CODE).delete()
        session.query(ModelRunPrediction).filter(ModelRunPrediction.station_code >= BASE_STATION_CODE).delete()
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
                session.add(
                    ModelRunPrediction(
                        prediction_model_run_timestamp_id=model_run_id,
                        prediction_timestamp=weather_date,
                        station_code=station_code,
                        tmp_tgl_2=15.0 + rng.uniform(-5, 5),
                        rh_tgl_2=50.0 + rng.uniform(-10, 10),
                        apcp_sfc_0=0.0,
                        wdir_tgl_10=rng.uniform(0, 360),
                        wind_tgl_10=rng.uniform(0, 20),
                    )
                )
            if i % 50 == 0:
                session.flush()
        print(f"seeded {station_count} stations x {hours} hours")


def main():
    parser = argparse.ArgumentParser(description="Profile ModelValueProcessor per-station ML/interpolation memory use.")
    parser.add_argument("--stations", type=int, default=500, help="Number of synthetic stations to simulate.")
    parser.add_argument("--hours", type=int, default=72, help="Hours of history to seed per station.")
    parser.add_argument("--sample-every", type=int, default=25, help="Print peak RSS every N stations.")
    args = parser.parse_args()

    _install_stubs()

    with get_write_session_scope() as setup_session:
        prediction_model = get_prediction_model(setup_session, ModelEnum.HRDPS, ProjectionEnum.HRDPS_LATLON)
        model_run = get_or_create_prediction_run(setup_session, prediction_model, datetime.now(timezone.utc))
        model_run_id = model_run.id

    _seed(args.stations, args.hours, model_run_id)

    print(f"peak RSS before profiling loop: {_rss_mb():.1f} MB")

    # One session for the whole profiling loop, never committed until the very end -- exactly
    # like _process_model_run() holding one session open across every station in a real run.
    with get_write_session_scope() as session:
        prediction_model = get_prediction_model(session, ModelEnum.HRDPS, ProjectionEnum.HRDPS_LATLON)
        model_run = get_or_create_prediction_run(session, prediction_model, datetime.now(timezone.utc))

        mvp = ModelValueProcessor(session)

        for i in range(args.stations):
            station_code = BASE_STATION_CODE + i
            station = _FakeStation(code=station_code, lat=49.0, long=-123.0, name=f"profile-station-{i}")
            mvp._process_model_run_for_station(model_run, station, ModelEnum.HRDPS)

            if (i + 1) % args.sample_every == 0:
                print(f"[{i + 1:>5}/{args.stations}] peak RSS so far: {_rss_mb():.1f} MB")

        print(f"[{args.stations:>5}/{args.stations}] peak RSS so far: {_rss_mb():.1f} MB (final, before commit)")


if __name__ == "__main__":
    main()
