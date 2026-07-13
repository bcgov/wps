"""Compare the station lists in SFMS stations_*.csv dumps against the stations
recorded on the matching sfms_run rows.

Each CSV is an Oracle SQL*Plus spool of STATION_BC_ACTIVE_REPORTING_VW -- the full
set of stations SFMS considered at that moment. sfms_run.stations is the set that
actually made it into the run, so the CSV is normally a superset of the run. This
reports the difference in both directions.

A CSV is matched to the first sfms_run whose run_datetime falls at or after the
timestamp in the CSV filename, within --window minutes.

Run from ./backend with:
    uv run python scripts/check_sfms_run_stations.py --dir ~/projects/data/sfms_stations_july_2_12
"""

import argparse
import csv
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from wps_shared.db.database import get_read_session_scope
from wps_shared.db.models.sfms_run import SFMSRun

FILENAME_RE = re.compile(r"^stations_(\d{8})_(\d{4})\.csv$")


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dir", type=Path, required=True, help="directory of stations_*.csv files")
    parser.add_argument(
        "--window", type=int, default=60, help="minutes after the CSV timestamp to look for a run"
    )
    parser.add_argument(
        "--run-type", choices=["actual", "forecast", "any"], default="any", help="restrict matching to one run type"
    )
    parser.add_argument(
        "--tz", default="America/Vancouver", help="timezone the CSV filename timestamps are in"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="list the station codes that differ, not just counts"
    )
    return parser.parse_args()


def read_csv_stations(path: Path) -> set[int]:
    """Pull station codes out of a SQL*Plus spool: padded columns, a dashes rule line
    and a repeated header row all have to be skipped."""
    codes = set()
    with path.open(newline="") as handle:
        for row in csv.reader(handle):
            if not row:
                continue
            first = row[0].strip().strip("'")
            if first.isdigit():
                codes.add(int(first))
    return codes


def get_runs(session, run_type: str) -> list[SFMSRun]:
    query = session.query(SFMSRun)
    if run_type != "any":
        query = query.filter(SFMSRun.run_type == run_type)
    return query.order_by(SFMSRun.run_datetime).all()


def match_run(csv_timestamp: datetime, runs: list[SFMSRun], window: timedelta) -> SFMSRun | None:
    """First run at or after the CSV timestamp, within the window."""
    for run in runs:
        if csv_timestamp <= run.run_datetime <= csv_timestamp + window:
            return run
    return None


def main():
    args = parse_args()
    timezone = ZoneInfo(args.tz)
    window = timedelta(minutes=args.window)

    csv_dir = args.dir.expanduser()
    csv_paths = sorted(path for path in csv_dir.iterdir() if FILENAME_RE.match(path.name))
    if not csv_paths:
        sys.exit(f"no stations_YYYYMMDD_HHMM.csv files in {csv_dir}")

    with get_read_session_scope() as session:
        runs = get_runs(session, args.run_type)
        if not runs:
            sys.exit("no sfms_run rows found")

        matches, unmatched = [], []
        for path in csv_paths:
            date_part, time_part = FILENAME_RE.match(path.name).groups()
            csv_timestamp = datetime.strptime(date_part + time_part, "%Y%m%d%H%M").replace(
                tzinfo=timezone
            )
            run = match_run(csv_timestamp, runs, window)
            if run is None:
                unmatched.append((path.name, csv_timestamp))
            else:
                matches.append((path, run, read_csv_stations(path)))

    identical, differing = [], []
    for path, run, csv_stations in matches:
        run_stations = set(run.stations)
        in_csv_only = csv_stations - run_stations
        in_run_only = run_stations - csv_stations
        record = (path.name, run, csv_stations, run_stations, in_csv_only, in_run_only)
        (identical if not in_csv_only and not in_run_only else differing).append(record)

    print(
        f"{len(csv_paths)} CSVs, {len(runs)} sfms_run rows "
        f"(run_type={args.run_type}, window={args.window}m, tz={args.tz})\n"
    )

    if identical:
        print(f"== station sets match exactly ({len(identical)}) ==")
        for name, run, csv_stations, _, _, _ in identical:
            local_run_time = run.run_datetime.astimezone(timezone)
            print(
                f"  {name} -> run {run.id} ({run.run_type.value} "
                f"{local_run_time:%Y-%m-%d %H:%M}) : {len(csv_stations)} stations"
            )
        print()

    if differing:
        print(f"== station sets differ ({len(differing)}) ==")
        for name, run, csv_stations, run_stations, in_csv_only, in_run_only in differing:
            local_run_time = run.run_datetime.astimezone(timezone)
            print(f"  {name} -> run {run.id} ({run.run_type.value} {local_run_time:%Y-%m-%d %H:%M})")
            print(
                f"      csv={len(csv_stations)}  run={len(run_stations)}  "
                f"in_csv_not_in_run={len(in_csv_only)}  in_run_not_in_csv={len(in_run_only)}"
            )
            if args.verbose:
                if in_csv_only:
                    print(f"      in csv, not in run: {sorted(in_csv_only)}")
                if in_run_only:
                    print(f"      in run, not in csv: {sorted(in_run_only)}")
        print()

    if unmatched:
        print(f"== no sfms_run within {args.window}m ({len(unmatched)}) ==")
        for name, csv_timestamp in unmatched:
            print(f"  {name} (csv timestamp {csv_timestamp:%Y-%m-%d %H:%M %Z})")
        print()

    print(f"summary: {len(identical)} match, {len(differing)} differ, {len(unmatched)} unmatched")
    return 1 if differing or unmatched else 0


if __name__ == "__main__":
    sys.exit(main())
