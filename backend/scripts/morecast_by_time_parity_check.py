"""Compare MoreCast's model values read from the `by_time` table with the same read from Postgres.

MoreCast shows the 20:00 UTC prediction per station, day and model, raw and bias-adjusted. This
runs that read both ways for every station over a range of days and reports where they differ:
values present in only one, values from a different model run, and values that differ to
float32 precision. It also prints how long each read took.

Run from ./backend:

    uv run python scripts/morecast_by_time_parity_check.py --days-back 3 --days-ahead 10

Exits 0 when the two agree, 1 otherwise.

Design: docs/architecture/station-weather-storage.md
"""

import argparse
import math
import sys
from datetime import datetime, time, timedelta
from time import perf_counter

import wps_shared.db.database
from wps_shared.schemas.morecast_v2 import WeatherIndeterminate
from wps_shared.utils.time import get_utc_now, vancouver_tz
from wps_shared.weather_models.fetch.predictions import (
    fetch_latest_model_run_predictions_by_station_code_and_date_range,
)
from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.morecast import fetch_model_predictions
from wps_wf1.wfwx_api import get_stations_synchronously

VALUE_FIELDS = ("temperature", "relative_humidity", "precipitation", "wind_direction", "wind_speed")

# Postgres holds doubles and `by_time` holds float32, which keeps about seven significant digits.
RELATIVE_TOLERANCE = 1e-6
ABSOLUTE_TOLERANCE = 1e-6


def values_match(expected, actual) -> bool:
    if expected is None or actual is None:
        return expected is None and actual is None
    if math.isnan(expected) or math.isnan(actual):
        return math.isnan(expected) and math.isnan(actual)
    return math.isclose(expected, actual, rel_tol=RELATIVE_TOLERANCE, abs_tol=ABSOLUTE_TOLERANCE)


def key_of(value: WeatherIndeterminate) -> tuple:
    return (value.station_code, str(value.determinate.value), value.utc_timestamp)


def compare(
    from_postgres: list[WeatherIndeterminate], from_by_time: list[WeatherIndeterminate]
) -> list[str]:
    """Return a description of each kind of difference between the two reads."""
    expected = {key_of(value): value for value in from_postgres}
    actual = {key_of(value): value for value in from_by_time}
    problems = []
    only_postgres = expected.keys() - actual.keys()
    only_by_time = actual.keys() - expected.keys()
    if only_postgres:
        problems.append(f"{len(only_postgres)} values only in Postgres, e.g. {min(only_postgres)}")
    if only_by_time:
        problems.append(f"{len(only_by_time)} values only in by_time, e.g. {min(only_by_time)}")

    in_both = expected.keys() & actual.keys()
    different_run = [
        key
        for key in in_both
        if expected[key].prediction_run_timestamp != actual[key].prediction_run_timestamp
    ]
    if different_run:
        key = min(different_run)
        problems.append(
            f"{len(different_run)} values come from a different run, e.g. {key}: "
            f"Postgres {expected[key].prediction_run_timestamp}, "
            f"by_time {actual[key].prediction_run_timestamp}"
        )
    # Values from different runs are expected to differ, so only compare those from the same run.
    same_run = in_both - set(different_run)
    for field in VALUE_FIELDS:
        differing = [
            key
            for key in same_run
            if not values_match(getattr(expected[key], field), getattr(actual[key], field))
        ]
        if differing:
            key = min(differing)
            problems.append(
                f"{field}: {len(differing)} values differ, e.g. {key}: "
                f"Postgres {getattr(expected[key], field)}, by_time {getattr(actual[key], field)}"
            )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--days-back", type=int, default=3, help="days before today to compare")
    parser.add_argument("--days-ahead", type=int, default=10, help="days after today to compare")
    args = parser.parse_args()

    today = get_utc_now().astimezone(vancouver_tz).date()
    start_time = datetime.combine(
        today - timedelta(days=args.days_back), time.min, tzinfo=vancouver_tz
    )
    end_time = datetime.combine(
        today + timedelta(days=args.days_ahead), time.max, tzinfo=vancouver_tz
    )
    stations = get_stations_synchronously()

    started = perf_counter()
    with wps_shared.db.database.get_read_session_scope() as session:
        from_postgres = fetch_latest_model_run_predictions_by_station_code_and_date_range(
            session, stations, start_time, end_time
        )
    postgres_seconds = perf_counter() - started

    started = perf_counter()
    from_by_time = fetch_model_predictions(ByTimeTable(), stations, start_time, end_time)
    by_time_seconds = perf_counter() - started

    print(f"{len(stations)} stations, {start_time.date()} to {end_time.date()}")
    print(f"Postgres: {len(from_postgres)} values in {postgres_seconds:.2f} s")
    print(f"by_time:  {len(from_by_time)} values in {by_time_seconds:.2f} s")

    if not from_postgres and not from_by_time:
        print("Nothing to compare.")
        return 1
    problems = compare(from_postgres, from_by_time)
    for problem in problems:
        print(f"[differs] {problem}")
    if not problems:
        print("[ok] the two reads agree")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
