# wps_weather_data module

This package reads and writes station weather data in object storage. The design is in
[docs/architecture/station-weather-storage.md](../../../docs/architecture/station-weather-storage.md).

## table.py

`DeltaWeatherTable` is what the Delta Lake tables share: where the table lives, the storage
options for reaching it, and `maintain()`, the upkeep every table needs (`optimize` merges
small files, a checkpoint keeps the transaction log quick to open, and `vacuum` deletes files
that no table version from the last 30 days refers to). Create a table object once and reuse
it; creating one does not contact the object store.

## runs.py

`RunsTable` is the `runs` dataset: station values from every weather model run.
`append_run` writes one version of a run in a single commit. `read` returns the newest version
of each run, and every reader should go through it so that rule lives in one place.

## staging.py

`StagingTable` is a model's `staging` dataset: the station values of runs that are still
downloading, one table per model. A job stages the files it processes with `append_files`, and
each file leaves a marker row in the same commit, so `processed_sources` tells what is done.
Once every file of a run is staged, the job reads it back with `station_values`, publishes the
run to `runs` and `by_time`, then calls `delete_run`.

## by_time.py

`ByTimeTable` is the `by_time` dataset: the newest value per station, time and source.
`merge_run` merges a model run in after it is appended to `runs`. A row is only replaced by a
run at least as new as the one it came from. `read` returns a time range for one resolution
(`hourly` or `daily`) and a list of sources. Only model sources are written so far.

## wf1.py

`Wf1Table` is the `wf1` dataset: every observation (`ACTUALS`) and forecaster's noon forecast
(`FORECAST`) fetched from WF1, append-only. `actuals_table` and `forecasts_table` turn WF1
records into rows with the `by_time` columns, with a missing or out-of-range value as null.
`append_changed` appends only the rows that differ from the version before them, so a correction
or a changed forecast is a new version. The WF1 jobs then merge the rows into `by_time` with
`ByTimeTable.merge_wf1_rows`.

The hourly actuals job also writes WF1's daily actuals, with `daily_actuals_table`: WF1's own
daily record for 20:00 UTC, whose precipitation is the total WF1 accumulated over the 24 hours
before. Nothing here adds up hourly values.

## data_mart.py

Historical observations from the BCWS data mart
(https://www.for.gov.bc.ca/ftp/HPR/external/!publish/BCWS_DATA_MART/), which has every station's
hourly observations back to 1987. `read_observations` turns its CSV files into hourly `ACTUALS`
rows, converting the Pacific Standard Time hours to UTC, with the wind gust and the hourly FFMC,
ISI and FWI. A noon row that carries WF1's daily precip total also becomes a daily `ACTUALS` row,
with WF1's daily FWI System indices and danger rating. `write_observations` writes them to `wf1` and
`by_time`. A value the hourly actuals job fetched from WF1 is never replaced by one from the
data mart.
`data_mart_backfill.py` downloads the files and runs it: `python -m
wps_weather_data.data_mart_backfill`, or as a one-off OpenShift job (see
`docs/DATA_REPROCESSING.md`).

## by_station.py

`ByStationTable` is the `by_station` dataset: the `by_time` rows in a Delta table partitioned by
resolution, station and year, so that climatology can read one station across every year without
touching any other station's data. `read` returns a station's whole record, optionally for some
sources.

The `station-weather-by-station` cron job runs `python -m wps_weather_data.by_station` each
night: it replaces the current year's rows from `by_time`, in one commit per resolution. After a
backfill, run it once with `--from-year` to rebuild the earlier years (as a one-off OpenShift
job: see `docs/DATA_REPROCESSING.md`). The maintenance job
vacuums the files each rebuild replaces.

## stations.py

`StationsTable` is the `stations` dataset: WF1's list of weather stations (code, name, location,
elevation and status). The hourly actuals job replaces it each run with `replace`, so the
Station Weather API can list stations without calling WF1. `read` returns every station.

## grids/

Weather model grids over BC, in Icechunk, alongside the station data. Each field is kept as the
GRIB file's own packed integers with its scales, so what is stored decodes to exactly what was
published.

- `grib.py`: GRIB2 fields as their packed integers, and the crop covering BC.
- `models.py`: the models kept (HRDPS and RDPS so far) and `load_run`, which downloads a run
  from the MSC datamart and reads it, cropped to BC.
- `store.py`: `GridStore`, one of a model's two stores, `recent` (every run for about a day) or
  `history` (one run a day). `write_run` adds a run as a group in one commit, `read_point` and
  `read_map` read it back decoded, `delete_runs_before` drops old runs, and `maintain` expires
  snapshots and garbage collects. It reaches the object store through the object_store crate,
  because Icechunk's default AWS SDK storage cannot delete on ECS.

- `job.py`: run hourly per model (`python -m wps_weather_data.grids.job --model HRDPS`). It
  writes the model's runs from the last day that `recent` lacks, the daily run (18Z) to
  `history` as well, skips a run the datamart has not finished publishing, and drops runs older
  than two days from `recent`. The nightly maintenance job garbage collects the grid stores.

Their dependencies are the `grids` extra, which the jobs install and the API does not. See
`docs/architecture/model-grid-storage-spike.md`.

## actuals.py

`StationObservations` reads `ACTUALS` from `by_time` for a time window, once per model run being
processed. Training pairs model values with its hourly observations and learns daily precip from
its 24 hour totals; ingest adds its observed precip to a run's first day of 24 hour precip.

## maintenance.py

Runs `maintain()` on every table. Run by the `station-weather-maintenance` cron job:

```bash
python -m wps_weather_data.maintenance
```

## addresser.py

`StationWeatherAddresser` builds the object store keys, in the style of `BaseRasterAddresser`.
Production tables live under `weather/stations/`. Dev deployments share one bucket, so each
writes under `dev/{suffix}/weather/stations/`, using the `SUFFIX` setting (for example
`pr-123`). With no `SUFFIX`, as when running locally, the production root is used.

## Status

No station weather is kept in Postgres. The model jobs (GDPS, RDPS, HRDPS, GFS, NAM and ECMWF)
stage runs in `staging`, publish them to `runs` and `by_time`, and train the bias adjustments on
`runs` and `by_time`'s `ACTUALS`; they no longer use the database. The WF1 jobs write `ACTUALS`
and `FORECAST` to `wf1` and `by_time`. The API reads MoreCast's model values from `by_time`
(`morecast.py`) and fire watch's from `runs` (`fire_watch.py`).

`backend/scripts/station_weather_backfill.py` copies history from the legacy Postgres tables into
`runs`, `wf1` and `by_time`, to fill a deployment's tables.
