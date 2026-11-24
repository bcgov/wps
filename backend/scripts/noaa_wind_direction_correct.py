"""Correct the GFS wind directions stored before the station job computed them right.

Run it once per deployment that has GFS runs from before the fix, straight after deploying it: until
then, bias adjusted GFS wind directions are wrong. `--before` is when the fix was deployed. Runs
stored since then are left alone, and so are those already corrected, so it can be run again.

It reports what it would correct, and corrects nothing unless given --apply. `by_station` takes the
corrected rows from `by_time`: this year's the next night, and earlier years' when it is rebuilt.

A run that was part downloaded when the fix was deployed is stored with some of each, and is not
corrected. Pass a later `--before` only if the runs stored until then are known to be mirrored.

Reads the backend's own S3 settings. SUFFIX names the deployment (`pr-123`, or `prod`) and is
required, because with none set the tables would be production's. From ./backend:

    SUFFIX=pr-123 uv run python scripts/noaa_wind_direction_correct.py --model GFS \
        --before 2026-11-24T20:00:00Z
"""

import argparse
import sys
from datetime import UTC, datetime

from wps_shared import config
from wps_shared.weather_models import ModelEnum
from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.noaa_wind_direction import MIRRORED_MODELS, correct_stored_runs
from wps_weather_data.runs import RunsTable


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--model", required=True, choices=[m.value for m in MIRRORED_MODELS])
    parser.add_argument("--before", required=True, type=datetime.fromisoformat)
    parser.add_argument("--apply", action="store_true", help="correct them, not only report")
    args = parser.parse_args()
    if not config.get("SUFFIX"):
        parser.error("set SUFFIX to the deployment to correct")
    before = args.before if args.before.tzinfo else args.before.replace(tzinfo=UTC)

    corrected = correct_stored_runs(
        RunsTable(), ByTimeTable(), ModelEnum(args.model), before, dry_run=not args.apply
    )
    verb = "corrected" if args.apply else "would correct"
    for run_ts in corrected:
        print(f"[{verb}] {args.model} {run_ts}")
    print(f"\n{verb} {len(corrected)} runs stored before {before}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
