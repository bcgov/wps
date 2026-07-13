"""Compare the station lists in SFMS stations_*.csv dumps against the stations
recorded on the matching sfms_run rows.

The two lists measure different things, so a plain set-equality check is not
meaningful:

  * Each CSV is an Oracle SQL*Plus spool of STATION_BC_ACTIVE_REPORTING_VW -- the
    roster of every active reporting station at that moment.
  * sfms_run.stations is the subset of that roster which had an ACTUAL or MANUAL
    daily in WF1 when the job ran (see is_sfms_daily in wps_wf1.parsers, which
    applies the same station-pool criteria as the view plus a record type filter).

So the run is expected to be a subset of the roster, growing through the afternoon
as stations report in. This script reports the two things that are actually worth
knowing:

  * chronic non-reporters -- roster stations absent from every day's final run,
    i.e. active on paper but never delivering a daily.
  * stations in a run but not in the roster -- normally roster lag (the station went
    active between the CSV dump and the run), but flagged since nothing else explains it.

A CSV is matched to the first sfms_run whose run_datetime falls at or after the
timestamp in the CSV filename, within --window minutes.

Run from ./backend with:
    uv run python scripts/check_sfms_run_stations.py --dir ~/projects/data/sfms_stations_july_2_12
"""

import argparse
import csv
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from wps_shared.db.database import get_read_session_scope
from wps_shared.db.models.sfms_run import SFMSRun

FILENAME_RE = re.compile(r"^stations_(\d{8})_(\d{4})\.csv$")


@dataclass
class RunComparison:
    """One CSV roster compared against the sfms_run it fed."""

    csv_name: str
    csv_timestamp: datetime
    run_id: int
    run_type: str
    run_datetime: datetime
    roster: set[int]
    reported: set[int]
    # Stations with a row in the sibling weather_*.csv, i.e. SFMS had data for them at
    # dump time. Empty when no weather CSV sits alongside the stations CSV.
    has_weather: set[int] = field(default_factory=set)
    weather_csv_name: str | None = None

    @property
    def not_yet_reported(self) -> set[int]:
        """Roster stations with no daily at run time. Expected, especially early."""
        return self.roster - self.reported

    @property
    def not_in_roster(self) -> set[int]:
        """Stations in the run that the roster does not know about."""
        return self.reported - self.roster

    @property
    def data_not_in_run(self) -> set[int]:
        """SFMS had weather for these, but the run did not include them."""
        return self.has_weather - self.reported

    @property
    def run_without_data(self) -> set[int]:
        """The run included these, but SFMS's weather extract had no row for them."""
        return self.reported - self.has_weather

    @property
    def local_day(self) -> date:
        return self.run_datetime.date()


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dir", type=Path, required=True, help="directory of stations_*.csv files")
    parser.add_argument(
        "--window", type=int, default=60, help="minutes after the CSV timestamp to look for a run"
    )
    parser.add_argument(
        "--run-type",
        choices=["actual", "forecast", "any"],
        default="actual",
        help="restrict matching to one run type",
    )
    parser.add_argument(
        "--tz", default="America/Vancouver", help="timezone the CSV filename timestamps are in"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="list station codes on every run, not just anomalies"
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


def read_weather_stations(path: Path) -> set[int]:
    """Station codes with a weather row in the SFMS_DAILY_VW spool. The file opens with a
    blank line, then a header, then a dashes rule, before the padded data rows."""
    codes = set()
    columns: list[str] | None = None
    with path.open(newline="") as handle:
        for row in csv.reader(handle):
            if not row:
                continue
            cells = [cell.strip() for cell in row]
            if columns is None:
                if "STATION_CODE" in cells:
                    columns = [cell.lower() for cell in cells]
                continue
            if cells[0].startswith("---"):
                continue
            record = dict(zip(columns, cells))
            code = record.get("station_code", "")
            if code.isdigit():
                codes.add(int(code))
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


def format_codes(codes: set[int], limit: int = 12) -> str:
    ordered = sorted(codes)
    if len(ordered) <= limit:
        return ", ".join(str(code) for code in ordered)
    shown = ", ".join(str(code) for code in ordered[:limit])
    return f"{shown}, ... (+{len(ordered) - limit} more)"


def final_runs_per_day(comparisons: list[RunComparison]) -> list[RunComparison]:
    """The last run of each day -- by then every healthy station should have reported."""
    latest: dict[date, RunComparison] = {}
    for comparison in comparisons:
        current = latest.get(comparison.local_day)
        if current is None or comparison.run_datetime > current.run_datetime:
            latest[comparison.local_day] = comparison
    return [latest[day] for day in sorted(latest)]


def report_reporting_progress(comparisons: list[RunComparison], verbose: bool) -> None:
    print("== reporting progress (run is expected to be a subset of the roster) ==")
    by_day: dict[date, list[RunComparison]] = defaultdict(list)
    for comparison in comparisons:
        by_day[comparison.local_day].append(comparison)

    for day in sorted(by_day):
        print(f"  {day:%Y-%m-%d}")
        for comparison in sorted(by_day[day], key=lambda item: item.run_datetime):
            percent = 100 * len(comparison.reported) / len(comparison.roster)
            print(
                f"    {comparison.run_datetime:%H:%M} run {comparison.run_id:<5} "
                f"reported {len(comparison.reported):>3}/{len(comparison.roster):<3} ({percent:5.1f}%)  "
                f"not yet reported: {len(comparison.not_yet_reported):>3}"
                f"   [{comparison.csv_name}]"
            )
            if verbose and comparison.not_yet_reported:
                print(f"        not yet reported: {format_codes(comparison.not_yet_reported)}")
    print()


def report_chronic_non_reporters(comparisons: list[RunComparison]) -> list[int]:
    """Roster stations that never made it into a single day's final run."""
    finals = final_runs_per_day(comparisons)
    if not finals:
        return []

    absences: dict[int, int] = defaultdict(int)
    for comparison in finals:
        for code in comparison.not_yet_reported:
            absences[code] += 1

    chronic = sorted(code for code, count in absences.items() if count == len(finals))
    intermittent = sorted(
        (count, code) for code, count in absences.items() if count < len(finals)
    )

    # If weather CSVs are present we can say whether these stations have data at all,
    # which separates "SFMS never had it" from "we dropped it".
    ever_had_weather: set[int] = set()
    for comparison in comparisons:
        ever_had_weather |= comparison.has_weather
    have_weather_csvs = any(comparison.weather_csv_name for comparison in comparisons)

    print(f"== chronic non-reporters (absent from all {len(finals)} final runs of the day) ==")
    if chronic:
        for code in chronic:
            if not have_weather_csvs:
                detail = "never reported a daily actual"
            elif code in ever_had_weather:
                detail = "HAS weather data in the SFMS extract -- we are dropping it"
            else:
                detail = "no weather row in any SFMS extract either -- SFMS never had data"
            print(f"  station {code}: in the roster every day, {detail}")
        print("  ^ active in STATION_BC_ACTIVE_REPORTING_VW but never making it into a run.")
    else:
        print("  none -- every roster station reported at least once by end of day")
    print()

    if intermittent:
        print("== intermittent non-reporters (missed some final runs) ==")
        for count, code in sorted(intermittent, reverse=True):
            print(f"  station {code}: missing from {count}/{len(finals)} final runs")
        print("  ^ consistent with normal transient station outages.")
        print()

    return chronic


def report_weather_gap(comparisons: list[RunComparison], verbose: bool) -> list[int]:
    """Compare against SFMS's own weather extract: did a station have data that the run
    failed to pick up? Returns the codes still missing at the final run of each day."""
    with_weather = [item for item in comparisons if item.weather_csv_name]
    if not with_weather:
        print("== weather CSV comparison ==")
        print("  skipped -- no weather_*.csv files alongside the stations_*.csv files")
        print()
        return []

    print("== stations SFMS had weather for, but the run did not use ==")
    by_day: dict[date, list[RunComparison]] = defaultdict(list)
    for comparison in with_weather:
        by_day[comparison.local_day].append(comparison)

    for day in sorted(by_day):
        print(f"  {day:%Y-%m-%d}")
        for comparison in sorted(by_day[day], key=lambda item: item.run_datetime):
            print(
                f"    {comparison.run_datetime:%H:%M} run {comparison.run_id:<5} "
                f"weather rows {len(comparison.has_weather):>3}  run {len(comparison.reported):>3}  "
                f"had data, not in run: {len(comparison.data_not_in_run):>3}  "
                f"in run, no data row: {len(comparison.run_without_data):>2}"
            )
            if verbose and comparison.data_not_in_run:
                print(f"        had data, not in run: {format_codes(comparison.data_not_in_run)}")
    print()

    finals = [item for item in final_runs_per_day(with_weather)]
    persistent: dict[int, int] = defaultdict(int)
    for comparison in finals:
        for code in comparison.data_not_in_run:
            persistent[code] += 1

    print(f"== still missing at the final run of the day ({len(finals)} days) ==")
    if persistent:
        for code, count in sorted(persistent.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  station {code}: had weather data but was left out of {count}/{len(finals)} final runs")
        print("  ^ these are real misses -- SFMS had the data by end of day and the run did not.")
    else:
        print("  none -- by the last run of the day the run used every station SFMS had data for")
    print(
        "  NOTE: the early (first run of the day) gap is not directly comparable. SFMS_DAILY_VW\n"
        "  has no record type column, so a weather row there may still be a FORECAST record,\n"
        "  while the run only accepts ACTUAL/MANUAL (see is_sfms_daily in wps_wf1.parsers)."
    )
    print()
    return sorted(persistent)


def report_not_in_roster(comparisons: list[RunComparison]) -> list[RunComparison]:
    """Stations that made it into a run without being on the roster."""
    offenders = [comparison for comparison in comparisons if comparison.not_in_roster]

    print("== stations in a run but not in the roster ==")
    if not offenders:
        print("  none -- every run was a clean subset of its roster")
        print()
        return []

    for comparison in offenders:
        print(
            f"  run {comparison.run_id} ({comparison.run_datetime:%Y-%m-%d %H:%M}) vs "
            f"{comparison.csv_name}: {format_codes(comparison.not_in_roster)}"
        )
    print(
        "  ^ usually roster lag: the station went active in WF1 between the CSV dump\n"
        "    and the run. Check whether the code appears in a later CSV the same day."
    )
    print()
    return offenders


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

        comparisons: list[RunComparison] = []
        unmatched: list[tuple[str, datetime]] = []

        for path in csv_paths:
            date_part, time_part = FILENAME_RE.match(path.name).groups()
            csv_timestamp = datetime.strptime(date_part + time_part, "%Y%m%d%H%M").replace(
                tzinfo=timezone
            )
            run = match_run(csv_timestamp, runs, window)
            if run is None:
                unmatched.append((path.name, csv_timestamp))
                continue

            weather_path = path.with_name(f"weather_{date_part}_{time_part}.csv")
            has_weather = read_weather_stations(weather_path) if weather_path.exists() else set()

            comparisons.append(
                RunComparison(
                    csv_name=path.name,
                    csv_timestamp=csv_timestamp,
                    run_id=run.id,
                    run_type=run.run_type.value,
                    run_datetime=run.run_datetime.astimezone(timezone),
                    roster=read_csv_stations(path),
                    reported=set(run.stations),
                    has_weather=has_weather,
                    weather_csv_name=weather_path.name if weather_path.exists() else None,
                )
            )

    print(
        f"{len(csv_paths)} CSVs, {len(runs)} sfms_run rows matched within {args.window}m "
        f"(run_type={args.run_type}, tz={args.tz})\n"
    )

    if not comparisons:
        sys.exit("no CSV matched a run -- try widening --window or changing --run-type")

    report_reporting_progress(comparisons, args.verbose)
    chronic = report_chronic_non_reporters(comparisons)
    missed_with_data = report_weather_gap(comparisons, args.verbose)
    not_in_roster = report_not_in_roster(comparisons)

    if unmatched:
        print(f"== CSVs with no run within {args.window}m ({len(unmatched)}) ==")
        for name, csv_timestamp in unmatched:
            print(f"  {name} (dumped {csv_timestamp:%Y-%m-%d %H:%M %Z})")
        print("  ^ a dump with no following run, e.g. after the last run of the day.")
        print()

    print(
        f"summary: {len(comparisons)} runs compared, "
        f"{len(chronic)} chronic non-reporter(s), "
        f"{len(missed_with_data)} station(s) with data missed by a final run, "
        f"{len(not_in_roster)} run(s) with stations off the roster, "
        f"{len(unmatched)} unmatched CSV(s)"
    )
    return 1 if chronic or missed_with_data or not_in_roster else 0


if __name__ == "__main__":
    sys.exit(main())
