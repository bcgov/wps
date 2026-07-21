"""
Full-fidelity reproduction of the real HRDPS job: EnvCanada.process() (download
+ ingest, all 4 model-run hours) -> ModelValueProcessor.process() (per-station
ML interpolation) -> apply_data_retention_policy() (retention delete) -- the
exact sequence and session boundaries run_model_job()/process_models() use in
production. None of the isolated single-phase tests built earlier in this
investigation reproduced the OOM, including the fully real download+decode
pipeline run alone under a real --memory=1g constraint. This combines all
three phases in one process, matching production exactly, as the remaining
untested condition.

Only the WFWX station lookup is stubbed (no live WFWX credentials available
locally) -- station count and identities are synthetic, but everything else
(GDAL raster decode, real HTTPS downloads, real Postgres session/commit
boundaries, real sklearn regression fitting, the real retention DELETE) runs
for real. HourlyActual history is seeded for the synthetic stations so the
interpolation phase has real data to fit against instead of trivially empty
queries.

Run inside podman with --memory=1g to match the actual production limit:
    podman run --rm --memory=1g \\
        -v "$(pwd)/backend/packages/wps-jobs/src/weather_model_jobs":/app/weather_model_jobs \\
        -e POSTGRES_WRITE_HOST=host.containers.internal \\
        -e POSTGRES_READ_HOST=host.containers.internal \\
        wps-jobs:local \\
        uv run --package wps-jobs --no-sync python -m weather_model_jobs.profile_full_pipeline --stations 500
"""

import argparse
import random
from datetime import datetime, timedelta, timezone

import requests

import weather_model_jobs.common_model_fetchers as common_fetchers_module
import weather_model_jobs.utils.process_grib as process_grib_module
from weather_model_jobs.common_model_fetchers import ModelValueProcessor, apply_data_retention_policy
from weather_model_jobs.env_canada import EnvCanada, mark_prediction_model_run_processed
from wps_shared.db.crud.weather_models import get_prediction_model, get_prediction_run
from wps_shared.db.database import get_write_session_scope
from wps_shared.db.models.observations import HourlyActual
from wps_shared.weather_models import ModelEnum, adjust_model_day, get_env_canada_model_run_hours

BASE_STATION_CODE = 900_000
BC_LAT_RANGE = (48.3, 60.0)
BC_LON_RANGE = (-139.0, -114.0)


class _FakeStation:
    def __init__(self, code, lat, long, name):
        self.code = code
        self.lat = lat
        self.long = long
        self.name = name


def _fake_stations(count: int):
    rng = random.Random(42)
    return [
        _FakeStation(
            code=BASE_STATION_CODE + i,
            lat=rng.uniform(*BC_LAT_RANGE),
            long=rng.uniform(*BC_LON_RANGE),
            name=f"profile-station-{i}",
        )
        for i in range(count)
    ]


def _install_stubs(station_count: int):
    stations = _fake_stations(station_count)
    # get_stations_synchronously is called once each by GribFileProcessor.__init__ (via
    # process_grib_module) and ModelValueProcessor.__init__ (via common_fetchers_module) --
    # both need the SAME synthetic roster so phase 2 interpolates the same stations phase 1
    # wrote predictions for.
    process_grib_module.get_stations_synchronously = lambda: stations
    common_fetchers_module.get_stations_synchronously = lambda: stations


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
    """Seed HourlyActual history for the synthetic stations so ModelValueProcessor's
    per-station regression fitting has real data to work with, not trivially-empty queries."""
    rng = random.Random(43)
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
            if i % 50 == 0:
                session.flush()
    print(f"seeded {station_count} synthetic stations x {hours}h of HourlyActual history")


def main():
    parser = argparse.ArgumentParser(description="Full process_models()-equivalent pipeline under real conditions.")
    parser.add_argument("--model", choices=["HRDPS", "RDPS", "GDPS"], default="HRDPS")
    parser.add_argument("--stations", type=int, default=500)
    parser.add_argument("--history-hours", type=int, default=72)
    args = parser.parse_args()

    model_type = ModelEnum(args.model)
    _install_stubs(args.stations)
    _seed_actuals(args.stations, args.history_hours)

    print(f"RSS before run: {_rss_mb():.1f} MB")

    # Mirrors process_models() exactly: one DB session + one http session shared across
    # BOTH download/ingest and interpolation.
    with get_write_session_scope() as session, requests.Session() as http_session:
        env_canada = EnvCanada(session, http_session, model_type)
        env_canada.process()
        print(
            f"RSS after EnvCanada.process() (download+ingest, all 4 hours, "
            f"{env_canada.files_processed} files): {_rss_mb():.1f} MB"
        )

        # Force completeness for hours that got at least one successful download, so
        # ModelValueProcessor has real work to do rather than skipping everything over a
        # handful of real per-file failures. Hours with zero successful downloads never got
        # a PredictionModelRunTimestamp row created at all (only a successful download
        # triggers get_or_create_prediction_run), so skip those instead of crashing on None.
        prediction_model = get_prediction_model(session, model_type, env_canada.projection)
        marked = 0
        for hour in get_env_canada_model_run_hours(model_type):
            run_timestamp = env_canada.now.replace(minute=0, second=0, microsecond=0)
            run_timestamp = adjust_model_day(run_timestamp, hour).replace(hour=hour)
            if get_prediction_run(session, prediction_model.id, run_timestamp) is not None:
                mark_prediction_model_run_processed(session, model_type, env_canada.projection, env_canada.now, hour)
                marked += 1
        session.flush()
        print(f"marked {marked}/4 model runs complete for interpolation")

        model_value_processor = ModelValueProcessor(session)
        model_value_processor.process(model_type)
        print(f"RSS after ModelValueProcessor.process() (interpolation): {_rss_mb():.1f} MB")

    # Mirrors run_model_job(): apply_data_retention_policy() runs after process_models()
    # returns, in its own fresh session -- this is where the real incident's last log line
    # was logged, immediately before the pod died.
    apply_data_retention_policy()
    print(f"RSS after apply_data_retention_policy() (retention delete): {_rss_mb():.1f} MB")


if __name__ == "__main__":
    main()
