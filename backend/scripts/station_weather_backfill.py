"""Copy model runs from the legacy Postgres tables into `runs` and `by_time` in object storage.

Before this change the model jobs wrote station predictions to weather_station_model_predictions
in Postgres. They now write to `runs` and `by_time` only, and the readers read only those. A new
deployment's tables start empty, so this fills them with the runs Postgres still has:

- MoreCast shows `by_time`'s daily rows for a window of past days.
- Bias adjustment trains on the last 19 days of `runs`.
- Fire watch reads the newest ECMWF run in `runs`.

Run from ./backend, once per model, against the deployment's database and bucket:

    uv run python scripts/station_weather_backfill.py --model GDPS --days 30

A run already in `runs` is skipped, so the script can be run again. `by_time` only takes a run's
row where the run is at least as new as the row's, so backfilling never undoes newer predictions.
Exits 0 when every run was copied or already there, 1 otherwise.

Design: docs/architecture/station-weather-storage.md
"""

import argparse
import sys
from datetime import timedelta

import wps_shared.db.database
from sqlalchemy import text
from wps_shared.utils.time import get_utc_now
from wps_shared.weather_models import ModelEnum, ProjectionEnum
from wps_weather_data.by_time import ByTimeTable
from wps_weather_data.runs import RunsTable

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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--model", required=True, choices=[model.value for model in ModelEnum])
    parser.add_argument("--days", type=int, default=30, help="how far back to copy runs")
    parser.add_argument("--dry-run", action="store_true", help="list the runs that would be copied")
    args = parser.parse_args()
    model = ModelEnum(args.model)
    since = get_utc_now() - timedelta(days=args.days)

    runs = RunsTable()
    by_time = ByTimeTable()
    copied = skipped = failed = 0
    with wps_shared.db.database.get_read_session_scope() as session:
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
            if args.dry_run:
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
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
