"""
Fast, isolated test of the "single long-lived write session -> unbounded
identity-map growth" hypothesis, with no network downloads and no GDAL decode.

process_grib_file's per-station work (GribFileProcessor.store_prediction_value)
is what's suspected of driving unbounded memory growth in the real
env-canada-hrdps job: production holds one un-flushed write session open for
the entire run (session.commit() happens exactly once, at the very end of
process_models()), across 4 model-run hours x ~245 files x up to
WFWX_MAX_PAGE_SIZE=1000 stations. Every ModelRunPrediction created along the
way sits in that session's identity map until then.

This script drives store_prediction_value directly in a tight loop against a
real local Postgres, skipping the slow parts (HTTP downloads, GDAL raster
reads, WFWX lookups) entirely, so the *shape* of the RSS curve (plateau vs.
linear climb) shows up in seconds/minutes instead of the ~30+ minutes the full
pipeline takes.

Usage:
    uv run --package wps-jobs python -m weather_model_jobs.profile_hrdps_session_growth \\
        --files 245 --stations 1000 --sample-every 5000
"""

import argparse
import resource
import sys
from datetime import datetime, timedelta, timezone

from weather_model_jobs.utils.process_grib import GribFileProcessor, ModelRunInfo
from wps_shared.db.crud.weather_models import get_or_create_prediction_run, get_prediction_model
from wps_shared.db.database import get_write_session_scope
from wps_shared.weather_models import ModelEnum, ProjectionEnum


def _rss_mb() -> float:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is bytes on macOS, KB on Linux.
    return peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024


def main():
    parser = argparse.ArgumentParser(description="Fast isolated test of write-session identity-map growth.")
    parser.add_argument("--files", type=int, default=245, help="Simulated file count.")
    parser.add_argument("--stations", type=int, default=1000, help="Simulated station count per file.")
    parser.add_argument("--sample-every", type=int, default=5000, help="Print peak RSS every N store_prediction_value calls.")
    args = parser.parse_args()

    # __new__ skips __init__, so this never calls get_stations_synchronously (no WFWX needed) --
    # store_prediction_value doesn't touch self.stations or any other instance state.
    processor = GribFileProcessor.__new__(GribFileProcessor)

    now = datetime.now(timezone.utc)
    grib_info = ModelRunInfo(
        model_enum=ModelEnum.HRDPS,
        projection=ProjectionEnum.HRDPS_LATLON,
        model_run_timestamp=now,
        prediction_timestamp=now,
        variable_name="profile_test_tmp",
    )

    with get_write_session_scope() as session:
        prediction_model = get_prediction_model(session, ModelEnum.HRDPS, ProjectionEnum.HRDPS_LATLON)
        prediction_run = get_or_create_prediction_run(session, prediction_model, now)

        total = args.files * args.stations
        print(f"Simulating {args.files} files x {args.stations} stations = {total} store_prediction_value calls")
        print(f"peak RSS before loop: {_rss_mb():.1f} MB")

        calls = 0
        for f in range(args.files):
            # Distinct timestamp per "file" so rows don't collide with each other or with
            # any real data, without needing to touch the DB to check.
            grib_info.prediction_timestamp = now + timedelta(hours=f)
            for s in range(args.stations):
                station_code = 900_000 + s  # well outside any real station-code range
                processor.store_prediction_value(station_code, 1.0, prediction_run, grib_info, session)
                calls += 1
                if calls % args.sample_every == 0:
                    print(f"[{calls:>8}/{total}] peak RSS so far: {_rss_mb():.1f} MB")

        print(f"[{calls:>8}/{total}] peak RSS so far: {_rss_mb():.1f} MB (final, before commit)")


if __name__ == "__main__":
    main()
