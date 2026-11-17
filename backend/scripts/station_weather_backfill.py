"""Copy station weather from the legacy Postgres tables into object storage.

The model jobs used to write station predictions to weather_station_model_predictions, and the
WF1 jobs wrote observations to hourly_actuals and noon forecasts to noon_forecasts. They now
write only to the Delta tables, and the readers read only those. A new deployment's tables start
empty, so this fills them with what Postgres still has:

- MoreCast shows `by_time`'s daily model rows for a window of past days.
- Bias adjustment trains on the last 19 days of `runs`, paired with `by_time`'s `ACTUALS`.
- A run's first day of 24 hour precip adds the `ACTUALS` precip before the run started.
- Fire watch reads the newest ECMWF run in `runs`.

Run from ./backend against the deployment's database and bucket, once per model and once per
WF1 source:

    uv run python scripts/station_weather_backfill.py --model GDPS --days 30
    uv run python scripts/station_weather_backfill.py --wf1 ACTUALS --days 30
    uv run python scripts/station_weather_backfill.py --wf1 FORECAST --days 30

The script can be run again. A run already in `runs` is skipped, and `by_time` only takes a
run's row where the run is at least as new as the row's. WF1 rows keep the time they were first
fetched, every version of a noon forecast is copied, and `wf1` only takes a version that differs
from the one before it. The daily observations are derived from the hourly ones once they
are in `by_time`; the first day copied has no precip total unless the 23 hours before it are there.
Exits 0 when everything was copied or already there, 1 otherwise.

Design: docs/architecture/station-weather-storage.md
"""

import argparse
import sys
from datetime import timedelta
from types import SimpleNamespace

import wps_shared.db.database
from sqlalchemy import text
from wps_shared.utils.time import get_utc_now
from wps_shared.weather_models import ModelEnum, ProjectionEnum
from wps_weather_data.by_time import ACTUALS, FORECAST, ByTimeTable
from wps_weather_data.runs import RunsTable
from wps_weather_data.wf1 import (
    Wf1Table,
    actuals_table,
    forecasts_table,
    merge_daily_actuals,
)

# A model's interpolated runs since a time. ECMWF has two grids with runs at the same times;
# the 0.1 degree one is taken, as the readers did.
RUNS_QUERY = text(
    """
    SELECT DISTINCT ON (run.prediction_run_timestamp)
        run.id, run.prediction_run_timestamp
    FROM prediction_model_run_timestamps AS run
    JOIN prediction_models AS model ON model.id = run.prediction_model_id
    WHERE model.abbreviation = :model
    AND run.complete AND run.interpolated
    AND run.prediction_run_timestamp >= :since
    ORDER BY run.prediction_run_timestamp, (model.projection = :preferred_projection) DESC
    """
)

STATION_ROWS_QUERY = text(
    """
    SELECT station_code, prediction_timestamp, tmp_tgl_2, rh_tgl_2, apcp_sfc_0, wdir_tgl_10,
        wind_tgl_10, bias_adjusted_temperature, bias_adjusted_rh, bias_adjusted_wdir,
        bias_adjusted_wind_speed, delta_precip, precip_24h, bias_adjusted_precip_24h
    FROM weather_station_model_predictions
    WHERE prediction_model_run_timestamp_id = :run_id
    """
)

MODEL_TIMES_QUERY = text(
    """
    SELECT DISTINCT prediction_timestamp
    FROM model_run_predictions
    WHERE prediction_model_run_timestamp_id = :run_id
    """
)


# Hourly observations since a time, with when they were fetched.
ACTUALS_QUERY = text(
    """
    SELECT station_code, weather_date, temperature, relative_humidity, wind_speed,
        wind_direction, precipitation, created_at
    FROM hourly_actuals
    WHERE weather_date >= :since
    """
)

# Every version of each noon forecast since a time, with when it was fetched.
FORECASTS_QUERY = text(
    """
    SELECT station_code, weather_date, temperature, relative_humidity, wind_speed,
        wind_direction, precipitation, created_at
    FROM noon_forecasts
    WHERE weather_date >= :since
    """
)


def station_rows(session, run_id: int) -> list[dict]:
    """A run's station predictions as `runs` rows.

    A row is interpolated if the model itself has no value at that time. That can only be told
    while the run's model_run_predictions still exist, so `is_interpolated` is None once they
    have been deleted.
    """
    model_times = {time for (time,) in session.execute(MODEL_TIMES_QUERY, {"run_id": run_id}).all()}
    rows = []
    for mapping in session.execute(STATION_ROWS_QUERY, {"run_id": run_id}).mappings():
        row = dict(mapping)
        row["is_interpolated"] = (
            row["prediction_timestamp"] not in model_times if model_times else None
        )
        rows.append(row)
    return rows


def backfill_model(session, model: ModelEnum, since, dry_run: bool) -> int:
    """Copy a model's runs. Returns how many failed."""
    runs = RunsTable()
    by_time = ByTimeTable()
    copied = skipped = failed = 0
    model_runs = session.execute(
        RUNS_QUERY,
        {
            "model": model.value,
            "since": since,
            "preferred_projection": ProjectionEnum.ECMWF_LATLON_0_1.value,
        },
    ).all()
    for run_id, run_ts in model_runs:
        if runs.has_run(model, run_ts):
            skipped += 1
            print(f"[in runs   ] {model.value} {run_ts}")
            continue
        if dry_run:
            print(f"[would copy] {model.value} {run_ts}")
            continue
        try:
            rows = station_rows(session, run_id)
            written = runs.append_run(model, run_ts, rows)
            by_time.merge_run(model, run_ts, rows)
            copied += 1
            print(f"[copied    ] {model.value} {run_ts}: {written} rows")
        except Exception as exception:
            failed += 1
            print(f"[failed    ] {model.value} {run_ts}: {exception}")

    print(f"\n{len(model_runs)} runs: {copied} copied, {skipped} already in runs, {failed} failed.")
    return failed


def backfill_wf1(session, source: str, since, dry_run: bool) -> int:
    """Copy observations or noon forecasts. Returns how many failed: 0 or 1."""
    query, to_table = (
        (ACTUALS_QUERY, actuals_table) if source == ACTUALS else (FORECASTS_QUERY, forecasts_table)
    )
    records = [
        SimpleNamespace(**row) for row in session.execute(query, {"since": since}).mappings()
    ]
    print(f"{len(records)} {source} records in Postgres since {since}")
    if dry_run or not records:
        return 0
    try:
        # Each record keeps the time it was first fetched.
        rows = to_table(records)
        by_time = ByTimeTable()
        appended = Wf1Table().append_changed(rows)
        merged = by_time.merge_wf1_rows(rows)
        print(
            f"[copied    ] {source}: {appended.num_rows} versions to wf1, {merged} rows to by_time"
        )
        if source == ACTUALS:
            daily = merge_daily_actuals(by_time, rows)
            print(f"[derived   ] {source}: {daily} daily rows to by_time")
        return 0
    except Exception as exception:
        print(f"[failed    ] {source}: {exception}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    what = parser.add_mutually_exclusive_group(required=True)
    what.add_argument("--model", choices=[model.value for model in ModelEnum])
    what.add_argument("--wf1", choices=[ACTUALS, FORECAST])
    parser.add_argument("--days", type=int, default=30, help="how far back to copy")
    parser.add_argument("--dry-run", action="store_true", help="report what would be copied")
    args = parser.parse_args()
    since = get_utc_now() - timedelta(days=args.days)

    with wps_shared.db.database.get_read_session_scope() as session:
        if args.model:
            failed = backfill_model(session, ModelEnum(args.model), since, args.dry_run)
        else:
            failed = backfill_wf1(session, args.wf1, since, args.dry_run)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
