"""Compare the `runs` table in object storage with weather_station_model_predictions in Postgres.

While a model job writes each finished run to both, this checks that they agree: for every
interpolated run of the model in the last few days, the same stations and prediction times, and
the same values to float32 precision.

Run from ./backend:

    uv run python scripts/station_runs_parity_check.py --model GDPS --days 3

With --backfill, a run that is in Postgres but missing from `runs` is appended, and merged into
`by_time`.
Exits 0 when every run matches, 1 otherwise.

Design: docs/architecture/station-weather-storage.md
"""

import argparse
import math
import sys
from datetime import timedelta

import wps_shared.db.database
from wps_shared.db.crud.weather_models import (
    get_prediction_model_run_timestamp_records,
    get_station_run_rows,
)
from wps_shared.utils.time import get_utc_now
from wps_shared.weather_models import ModelEnum
from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.runs import VALUE_COLUMNS, RunsTable

# Postgres holds doubles and `runs` holds float32, which keeps about seven significant digits.
RELATIVE_TOLERANCE = 1e-6
ABSOLUTE_TOLERANCE = 1e-6


def values_match(expected, actual) -> bool:
    if expected is None or actual is None:
        return expected is None and actual is None
    if math.isnan(expected) or math.isnan(actual):
        return math.isnan(expected) and math.isnan(actual)
    return math.isclose(expected, actual, rel_tol=RELATIVE_TOLERANCE, abs_tol=ABSOLUTE_TOLERANCE)


def compare_run(postgres_rows: list[dict], object_store_rows: list[dict]) -> list[str]:
    """Return a description of each difference between one run's rows in the two stores."""
    expected = {(row["station_code"], row["prediction_timestamp"]): row for row in postgres_rows}
    actual = {(row["station_code"], row["prediction_timestamp"]): row for row in object_store_rows}
    problems = []
    if len(actual) != len(object_store_rows):
        problems.append(f"{len(object_store_rows) - len(actual)} duplicate rows in runs")
    only_postgres = expected.keys() - actual.keys()
    only_runs = actual.keys() - expected.keys()
    if only_postgres:
        problems.append(f"{len(only_postgres)} rows only in Postgres, e.g. {min(only_postgres)}")
    if only_runs:
        problems.append(f"{len(only_runs)} rows only in runs, e.g. {min(only_runs)}")
    for column in VALUE_COLUMNS:
        differing = [
            key
            for key in expected.keys() & actual.keys()
            if not values_match(expected[key][column], actual[key][column])
        ]
        if differing:
            key = min(differing)
            problems.append(
                f"{column}: {len(differing)} values differ, e.g. {key}: "
                f"Postgres {expected[key][column]}, runs {actual[key][column]}"
            )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--model", default="GDPS", choices=[model.value for model in ModelEnum])
    parser.add_argument("--days", type=int, default=3, help="how far back to compare runs")
    parser.add_argument(
        "--backfill", action="store_true", help="append runs that are missing from runs"
    )
    args = parser.parse_args()
    model = ModelEnum(args.model)
    since = get_utc_now() - timedelta(days=args.days)

    runs = RunsTable()
    by_time = ByTimeTable()
    checked = failed = 0
    with wps_shared.db.database.get_read_session_scope() as session:
        records = get_prediction_model_run_timestamp_records(
            session, model, complete=True, interpolated=True
        )
        for model_run, _ in records:
            run_ts = model_run.prediction_run_timestamp
            if run_ts < since:
                continue
            checked += 1
            postgres_rows = get_station_run_rows(session, model_run.id)
            object_store_rows = runs.read(model, run_ts, run_ts).to_pylist()
            if not object_store_rows and postgres_rows:
                if args.backfill:
                    written = runs.append_run(model, run_ts, postgres_rows)
                    by_time.merge_run(model, run_ts, postgres_rows)
                    print(f"[backfilled] {model.value} {run_ts}: {written} rows appended")
                else:
                    failed += 1
                    print(f"[missing   ] {model.value} {run_ts}: not in runs")
                continue
            problems = compare_run(postgres_rows, object_store_rows)
            if problems:
                failed += 1
                print(f"[differs   ] {model.value} {run_ts}:")
                for problem in problems:
                    print(f"             {problem}")
            else:
                print(f"[ok        ] {model.value} {run_ts}: {len(postgres_rows)} rows match")

    print(f"\n{checked} runs checked, {failed} with problems.")
    if checked == 0:
        print(f"No interpolated {model.value} runs in the last {args.days} days.")
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
