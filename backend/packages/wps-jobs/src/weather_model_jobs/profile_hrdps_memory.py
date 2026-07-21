"""
Standalone memory-profiling harness for the env-canada-hrdps cronjob.

v2: exercises the real download -> GDAL decode -> per-station raster read ->
SQLAlchemy store loop across ALL model-run hours in a single process (exactly
matching production's EnvCanada.process()), against a real local Postgres so
the write-session identity-map behaviour is real too -- not a stub. Only the
WFWX station lookup is faked, to avoid needing live WFWX credentials.

The first version of this script (stubbed session, single hour) showed peak
RSS plateauing well under the 1Gi limit, which ruled out a leak in the
download/GDAL/pyproj path. The remaining suspect is production's *single*
write session held open across the whole job (session.commit() only happens
once, at the very end of process_models()) -- every ModelRunPrediction
created via store_prediction_value() sits in that session's identity map,
unflushed, for the entire run. With real WFWX station counts (up to
WFWX_MAX_PAGE_SIZE=1000) across 4 model-run hours x ~245 files each, that
could be the actual unbounded-growth mechanism. This version is built to
surface that.

Setup (once):
    podman run -d --name wps-profile-db -p 5432:5432 \\
        -e POSTGRES_USER=wps -e POSTGRES_PASSWORD=wps -e POSTGRES_DB=wps \\
        postgis/postgis
    cd backend/packages/wps-api && uv run alembic upgrade head
    # (defaults in wps_shared.db.database already point at wps/wps@localhost:5432/wps,
    # matching docker-compose.yml's db service, so no env vars needed.)

Usage (run directly on the host, not in the podman image, so `localhost`
resolves to the postgres container above):
    uv run --package wps-jobs python -m weather_model_jobs.profile_hrdps_memory --stations 1000

Deep dive with memray:
    uv run --package wps-jobs memray run --live -m weather_model_jobs.profile_hrdps_memory --stations 1000
"""

import argparse
import random
from datetime import datetime, timezone

import requests

import weather_model_jobs.env_canada as env_canada_module
import weather_model_jobs.utils.process_grib as process_grib_module
from wps_shared.db.database import get_write_session_scope
from wps_shared.weather_models import ModelEnum, get_env_canada_model_run_hours
from wps_shared.weather_models.eccc_url_fetcher import ECCCUrlFetcher
from wps_shared.weather_models.model_run_urls import get_model_run_urls

# BC's approximate station bounding box. The station *count* is what drives
# per-file iteration cost, not any particular station's identity.
BC_LAT_RANGE = (48.3, 60.0)
BC_LON_RANGE = (-139.0, -114.0)


class _FakeStation:
    def __init__(self, code, lat, long):
        self.code = code
        self.lat = lat
        self.long = long


def _fake_stations(count: int):
    rng = random.Random(42)
    return [
        _FakeStation(code=1000 + i, lat=rng.uniform(*BC_LAT_RANGE), long=rng.uniform(*BC_LON_RANGE))
        for i in range(count)
    ]


def _install_stubs(station_count: int):
    # get_stations_synchronously is only called once, inside GribFileProcessor.__init__,
    # so it must be patched before EnvCanada() constructs its processor. get_prediction_model
    # and get_or_create_prediction_run are deliberately left real -- they, and
    # store_prediction_value, are what exercise the real session/identity-map behaviour
    # we're trying to observe here.
    process_grib_module.get_stations_synchronously = lambda: _fake_stations(station_count)

    # Looked up per-URL in process_model_run_urls; stub so every file is (re)processed on
    # every run, regardless of what's already flagged as processed in the DB from a
    # previous profiling pass.
    env_canada_module.get_processed_file_record = lambda *_a, **_k: None
    env_canada_module.flag_file_as_processed = lambda *_a, **_k: None


def _rss_mb() -> float:
    # Current RSS, not resource.getrusage().ru_maxrss -- that's a monotonic historical peak
    # that can never decrease, so it can't show whether GDAL's cache is now being evicted
    # rather than growing unboundedly.
    # /proc/self/status is dependency-free and always present in the Linux containers this
    # actually runs in; psutil is a fallback for local macOS runs where it isn't.
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except FileNotFoundError:
        pass
    import psutil

    return psutil.Process().memory_info().rss / (1024 * 1024)


def main():
    parser = argparse.ArgumentParser(description="Profile EnvCanada.process() memory use against a real DB session.")
    parser.add_argument("--model", choices=["HRDPS", "RDPS", "GDPS"], default="HRDPS")
    parser.add_argument(
        "--hour",
        type=int,
        default=None,
        help="Profile a single model-run hour instead of all of them (e.g. 0/6/12/18).",
    )
    parser.add_argument("--sample-every", type=int, default=10, help="Print peak RSS every N files.")
    parser.add_argument(
        "--stations",
        type=int,
        default=260,
        help="Number of synthetic WFWX stations to simulate (real roster can approach WFWX_MAX_PAGE_SIZE=1000).",
    )
    args = parser.parse_args()

    model_type = ModelEnum(args.model)
    _install_stubs(args.stations)

    now = datetime.now(timezone.utc)
    hours = [args.hour] if args.hour is not None else list(get_env_canada_model_run_hours(model_type))

    # One DB session and one http session for the whole run, matching process_models():
    # `with get_write_session_scope() as session, requests.Session() as http_session: ...`.
    with get_write_session_scope() as session, requests.Session() as http_session:
        env_canada = env_canada_module.EnvCanada(session, http_session, model_type)
        print(f"{len(env_canada.grib_processor.stations)} stations loaded")

        for hour in hours:
            urls = get_model_run_urls(now, model_type, hour)
            fetcher = ECCCUrlFetcher(now, hour, session=http_session)
            print(f"--- hour {hour:02d}Z: {len(urls)} urls ---")

            for i in range(0, len(urls), args.sample_every):
                batch = urls[i : i + args.sample_every]
                env_canada.process_model_run_urls(batch, fetcher)
                print(
                    f"[hour={hour:02d} {i + len(batch):>4}/{len(urls)}] current RSS: {_rss_mb():.1f} MB "
                    f"(downloaded={env_canada.files_downloaded}, processed={env_canada.files_processed}, "
                    f"errors={env_canada.exception_count})"
                )

            fetcher.log_connection_summary()

        print(f"Committing session (identity map holds every ModelRunPrediction added this run)...")


if __name__ == "__main__":
    main()
