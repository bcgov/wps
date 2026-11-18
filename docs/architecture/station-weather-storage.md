# Station weather data on object storage

## Summary

This proposes moving station weather data out of Postgres and onto object storage. That covers model predictions, observations and forecasts at each weather station.

The layouts follow from the reads we need to support:

- **Every model run** is kept, for the `/weather_models` routes and training.
- **Station history**, one value per station, time and source, is kept in two layouts: by time for MoreCast, and by station for climatology. Climatology statistics are computed on demand from the station files, for one station or a group, over any number of years.

We compared Parquet, GeoParquet, Delta Lake, Zarr and Icechunk with four local benchmarks, written up in [station-weather-storage-evaluation.md](station-weather-storage-evaluation.md). The design uses two of them:

- **Delta Lake** for the two tables that jobs write to, `runs` and `by_time`. Several jobs write to each, and both need compaction. That is what Delta Lake is for.
- **Delta Lake** for `by_station` as well, the copy of `by_time` laid out by station. It has a single writer and would work as plain Parquet files, which is how it was first designed. It is a Delta table so that a nightly rebuild is one commit, a bad one can be undone, and it goes through the same client and upkeep as the other tables.
- **Plain Parquet** for the other files derived from them (`hourly_profile`, `leads`), which have a single writer and are read by screens.

GeoParquet and Icechunk are a poor fit. Zarr is a poor fit for model runs and a reasonable but second-best fit for station history.

Nothing here is built. Delta Lake has been run against our object store in a throwaway table: four writers appending at once lost no commits, and `MERGE`, `optimize`, `vacuum` and checkpoints worked. No real read path has been timed there. See [Main risks](#main-risks).

## Goals

- Support MoreCast's current workflow: the newest value per station, day and source.
- Support climatology: historical observations, forecasts and model values per station, at daily and hourly resolution, for one station or a group.
- Get `weather_station_model_predictions`, `model_run_predictions`, `hourly_actuals`, `noon_forecasts` and the model run bookkeeping tables out of Postgres, along with the partitioning and archiving jobs that exist only to manage their size.
- Let several jobs write to the same table safely, and keep reprocessing history.

## Non-goals

- Backfilling history. Climatology history starts when this is built.
- FWI indices in the station history. It holds weather variables only for now.
- Moving the rest of the application off Postgres.
- Storing the gridded model output. We will store grids only if we have to. The ingest jobs keep only values at station locations, and this design does not change that.

## Background

Six cron jobs (GDPS, RDPS, HRDPS, NAM, GFS, ECMWF) ingest model runs in two steps:

1. As each GRIB file is processed, the raw values at each station go into `model_run_predictions`.
2. When a run has fully downloaded, the job trains a bias adjustment per station on 19 days of history, then writes `weather_station_model_predictions`: the raw values, the bias-adjusted values, `delta_precip`, `precip_24h`, and an interpolated 20:00 UTC row for models that only predict every three hours.

`weather_station_model_predictions` therefore contains nearly everything in `model_run_predictions`. The first table is mostly a staging area.

What makes this painful in Postgres:

- `weather_station_model_predictions` is partitioned by month, managed by `openshift/pgslice/docker/partition_and_archive.sh`.
- Partitions 3 to 6 months old are dumped with `pg_dump` to object storage and dropped. That history cannot be queried without restoring it.
- `model_run_predictions` is pruned by age (`DATA_RETENTION_THRESHOLD`).

Who reads the data:

| Reader | What it reads |
|---|---|
| MoreCast grid (`wps_shared/weather_models/fetch/predictions.py`) | The 20:00 UTC prediction per station, day and model, raw and bias-adjusted, for a range of a few days. It runs one query per day in the range. |
| Fire watch (`app/fire_watch/calculate_weather.py`) | The 20:00 UTC rows of the latest run of one model. |
| `/weather_models` routes | Every run's values for a list of stations, from 5 days before to 10 days after a time of interest. |
| Bias-adjustment training (`weather_model_jobs/bias_adjusted_variable.py`) | Raw predictions from `model_run_predictions` joined to `hourly_actuals`, plus daily precip from `weather_station_model_predictions`, queried per station. |
| Ingest itself | Earlier predictions from the same run, to derive precip deltas and 24-hour totals. |

One constraint on object storage matters here. We use Dell ECS through an S3-compatible API, and `aiobotocore` is pinned because newer `botocore` versions send default checksums that ECS rejects. Delta Lake and Icechunk each bring their own S3 client, which that pin does not cover.

## Use cases

None of these storage formats has an index that can be added later. The way the data is laid out decides which reads are cheap, so the layouts have to follow from the reads we need to support. There are five.

| Use case | Lookup key | Read shape | Data |
|---|---|---|---|
| MoreCast | Date range and source, across many stations | Wide and shallow: all stations, a few days, the newest value per day | Observations, forecasts and models, daily |
| Climatology, one station | Station, across all years | Narrow and deep | Observations, forecasts and models, daily and hourly, weather variables only for now |
| Climatology, a group of stations | Stations and a time-of-year window, across all years | A band through every year | The same |
| Climatology at a chosen lead | One station or a group, filtered by how far ahead each prediction was made | Either shape, with several predictions per time | Models, every run |
| Model run detail (`/weather_models` routes, training) | Model and run | One run or a few weeks of runs, every prediction time | Models, every run |

Decisions behind this table:

- **MoreCast needs only the newest run per day.** Run is how the winning row is picked, not something MoreCast looks up.
- **Climatology history starts now.** There is no backfill, so the deep reads grow by a year per year.
- **Climatology needs both shapes**, one station and groups of stations.
- **Lead has to stay a free choice.** We want to experiment with which prediction counts as the historical one, so no single lead can be baked in. See [Lead time](#lead-time).

The first three use cases read the same logical table: one value per station, time and source, where the source is `ACTUALS`, `FORECAST` or a model. This is the shape MoreCast already uses in `WeatherIndeterminate`. For a model, the value at a given time is the one from the newest run that predicted it. The last two need every run.

MoreCast reads by time across every station. Climatology reads by station across time, for one station or several. One sort order cannot serve both, so the design keeps this table in two layouts.

### Lead time

Lead is how far ahead a prediction was made: the gap between when the model ran and the time it predicts. Several runs predict the same moment, each at a different lead. HRDPS runs four times a day and predicts 48 hours ahead, so about eight runs predict any given hour:

| Run started | Lead for Friday 20:00 UTC |
|---|---|
| Wednesday 00:00 | 44 hours |
| Thursday 00:00 | 20 hours |
| Friday 06:00 | 14 hours |
| Friday 18:00 | 2 hours |

Which one is "the" historical model value depends on the question:

- **What did the model say the weather was?** The shortest lead, here the Friday 18:00 run, is the model's best estimate.
- **How good is the model at forecasting tomorrow?** The shortest lead is the wrong record. Comparing observations with 2-hour-ahead predictions makes the model look far better than it is at the range forecasters use.

`by_time` and `by_station` keep one value per station and time, and for a past time that is the shortest lead. That suits MoreCast and the first question. For the second, and for experimenting with other rules, the design keeps every run and adds a station-keyed copy of all of them, `leads`, so the lead is chosen when reading. This has to work for one station and for groups of stations.

## Why this shape

Each choice below rests on a benchmark in [station-weather-storage-evaluation.md](station-weather-storage-evaluation.md). All of them ran on local disk with synthetic data for an assumed 300 stations.

| Choice | Evidence |
|---|---|
| Parquet as the file format | It was the fastest and simplest of the five formats. Zarr and Icechunk needed 12 and 28 times the objects. GeoParquet added size and write time for no read benefit. See [Benchmark: formats](station-weather-storage-evaluation.md#benchmark-formats). |
| Delta Lake for `runs` and `by_time` | Not chosen on speed: plain Parquet was faster. Chosen because several jobs write to each table and both need compaction. See [Which tool for the job](station-weather-storage-evaluation.md#which-tool-for-the-job). |
| Station history in two layouts | Each layout wins its own read by a wide margin: 5 objects against 420 for one station's history, and 8 against 300 for MoreCast. See [Station history benchmark](station-weather-storage-evaluation.md#station-history-benchmark). |
| One copy of `leads`, keyed by station | A time-keyed copy fetched exactly the same bytes for a group read, so it is not worth a second copy. See [Lead benchmark](station-weather-storage-evaluation.md#lead-benchmark). |
| Climatology computed on demand, not precomputed | Over 30 years, three of the four screen reads fetch under 10 MB and compute in a second or less. Only hourly data for a group is too large, which is why `hourly_profile` exists. See [Reads over 5, 10 and 30 years, for a screen](station-weather-storage-evaluation.md#reads-over-5-10-and-30-years-for-a-screen). |

## Design

### Layout

The flow from sources to readers is drawn in [station-weather-storage-diagram.md](station-weather-storage-diagram.md).

The layout on object storage:

```text
weather/stations/
  runs/                                        Delta table: every model run, append-only
  wf1/                                         Delta table: every observation and forecast from WF1, append-only
  by_time/                                     Delta table: newest value per station and time
  staging/hrdps/                               Delta table per model: station values while a run downloads
  by_station/                                  Delta table: the by_time rows, partitioned by resolution, station and year
  hourly_profile/station=322.parquet                       hourly statistics by month and hour of day
  leads/station=322/2026.parquet                           every prediction at every lead, per station
```

`resolution` is `hourly` or `daily`. `source` is `ACTUALS`, `FORECAST` or a model.

That is the production layout. Dev deployments share one bucket, so each writes the same layout under `dev/{suffix}/`, such as `dev/pr-123/weather/stations/runs/`.

| Dataset | Format | Serves | Written by |
|---|---|---|---|
| `runs` | Delta Lake | Fire watch, training | The six model jobs |
| `staging` | Delta Lake, one per model | The model job itself, between invocations | That model's job |
| `wf1` | Delta Lake | Rebuilding `by_time`; history of corrections | The WF1 jobs |
| `by_time` | Delta Lake | MoreCast; training and ingest (`ACTUALS`) | The model jobs and the WF1 jobs |
| `by_station` | Delta Lake | Climatology for one station or a group | One nightly job |
| `hourly_profile` | Parquet | Hourly climatology for a group, on a screen | The same nightly job |
| `leads` | Parquet | Climatology at a chosen lead, while experimenting | The same nightly job |

The Parquet files have deterministic keys: a reader computes the key from the station and never lists the bucket. The Delta tables are read through their transaction log, `by_station` included.

All values are stored as float32. Postgres stores doubles today, but that precision is not information: the source model fields and the station sensors carry far fewer than float32's seven significant digits. float32 halves the size of `runs` to about 4.5 GB a year. The training golden tests compare exact values and will need a tolerance.

### `runs`

Replaces `weather_station_model_predictions`. A Delta table partitioned by `model` and `run_date`. Each completed run is appended in one commit.

| Column | Type | Notes |
|---|---|---|
| `station_code` | int32 | |
| `run_ts` | timestamp, UTC | Model run start. |
| `prediction_timestamp` | timestamp, UTC | |
| `tmp_tgl_2`, `rh_tgl_2`, `apcp_sfc_0`, `wdir_tgl_10`, `wind_tgl_10` | float32 | Raw model values. |
| `bias_adjusted_temperature`, `bias_adjusted_rh`, `bias_adjusted_wdir`, `bias_adjusted_wind_speed` | float32 | |
| `delta_precip`, `precip_24h`, `bias_adjusted_precip_24h` | float32 | |
| `ingested_at` | timestamp, UTC | When this version of the run was written. A reprocessed run appears again with a later value. |
| `is_interpolated` | bool | New. Marks the 20:00 UTC rows the job interpolates for three-hourly models. |

Each run is written sorted by `station_code`, then `prediction_timestamp`. Compression is zstd.

The surrogate `id`, `create_date` and `update_date` columns are not carried over. A row is identified by model, run, station, prediction time and `ingested_at`.

Each run arrives as one small file. `optimize` merges a closed day's runs into one file per model, which in the format benchmark cut the files read to about a quarter.

### `wf1`

Every observation and forecaster's forecast as fetched from WF1. It is to observations what `runs` is to models: an append-only record that `by_time` is built from. It is a Delta table partitioned by `source` (`ACTUALS` or `FORECAST`), `resolution` and month, with the same columns as `by_time`.

| Source | Resolution | Written by | From |
|---|---|---|---|
| `ACTUALS` | `hourly` | `app/jobs/hourly_actuals.py`, hourly, fetching the last three hours | WF1 hourlies, replacing `hourly_actuals` |
| `ACTUALS` | `daily` | The same job, fetching WF1's daily actuals for the latest 20:00 UTC and the one before | WF1 dailies of record type `ACTUAL` or `MANUAL`, for active stations, through the same call the SFMS daily actuals job makes; not in Postgres before |
| `FORECAST` | `daily`, at 20:00 UTC | `app/jobs/noon_forecasts.py`, hourly, fetching every forecast from now on | WF1 noon forecasts, replacing `noon_forecasts` |

The WF1 jobs append a row only when it is new or differs from the newest version already stored, with the `ingested_at` of that fetch (`Wf1Table.append_changed`). A corrected observation is therefore a second row with a later `ingested_at`, and the original stays. Each job then merges every row it fetched into `by_time`, not only the changed ones, so a merge that failed after the append is made good by the next run, which fetches the same rows again. In `by_time` a row is replaced only by one fetched at least as recently.

A value WF1 does not have, or that is outside its valid range (RH 0 to 100, wind direction 0 to 360, wind speed and precip not negative), is null. That replaces the per-variable validity flags of `hourly_actuals`. `ACTUALS` has no `daily` rows yet: nothing reads a noon observation from `by_time`, and MoreCast takes its observations from WF1 directly.

A side effect is that it records forecast history from now on, even though WF1 itself keeps only the latest forecast: each time a forecast changes between fetches, the new value is appended. That history is only as fine as the fetch interval, and it covers forecasts published by any tool, not only MoreCast.

### `staging`

Replaces `model_run_predictions`. It holds a run that is still downloading.

A run arrives as hundreds of GRIB files, one per variable per forecast hour, published over a span of time. The cron job processes whatever is available, exits, and returns later for the rest. Bias adjustment needs the whole run, so the partial run has to be kept somewhere between invocations.

Each model has its own `staging` Delta table, partitioned by run, so each table has one writer: the model's job. A row is one value:

| Column | Type | Notes |
|---|---|---|
| `run` | string | The partition, such as `20261117T00`. |
| `run_ts` | timestamp, UTC | |
| `station_code` | int32 | Null on a file's marker row. |
| `prediction_timestamp` | timestamp, UTC | |
| `variable` | string | Which model field the value is, such as `tmp_tgl_2`. Null on a marker row. |
| `value` | float64 | Kept at full precision, since the station predictions are computed from it. |
| `source` | string | The file the value came from: its URL, or for ECMWF its forecast hour. |
| `written_at` | timestamp, UTC | A value staged twice takes the newest. |

Every processed file leaves a marker row in the same commit as its values, so the files a run has processed are the distinct `source` values of its partition, and a file is either processed with all its values or not at all. A job commits every 50 files and at the end of each run, so a run has a handful of commits rather than one per GRIB, which would be roughly 245 for an HRDPS run and 405 for GDPS. The cost is that a crash loses the files processed since the last commit, and the next invocation fetches them again.

An earlier version of this design kept plain Parquet files with the processed files listed in their footers. The Delta table was chosen instead because it reuses the write path already proven against our object store, and its commits make "processed" and "staged" the same event.

When the run is complete, the job reads it back from `staging`, computes bias adjustments and derived precip in memory, appends the run to `runs`, merges it into `by_time`, and deletes the run from `staging`. A run that yields no station predictions is left in `staging` and logged as an error, rather than deleted and downloaded again. The steps, and what happens after a failure at each one, are under [Run bookkeeping](#run-bookkeeping).

### `by_time`

A Delta table partitioned by `resolution`, `source` and month. It holds one row per station and time.

| Column | Type | Notes |
|---|---|---|
| `station_code` | int32 | |
| `timestamp` | timestamp, UTC | The hour for `hourly`. The 20:00 UTC noon record for `daily`. |
| `temperature`, `relative_humidity`, `wind_speed`, `wind_direction` | float32 | |
| `precipitation` | float32 | The hour's precipitation for `hourly`, the 24-hour total for `daily`. |
| `bias_adjusted_temperature`, `bias_adjusted_relative_humidity`, `bias_adjusted_wind_speed`, `bias_adjusted_wind_direction`, `bias_adjusted_precipitation` | float32 | Models only, null otherwise. |
| `ffmc`, `dmc`, `dc`, `isi`, `bui`, `fwi` | float32 | WF1 and the data mart only, null for models: the FWI System indices WF1 calculated. An `hourly` row has only the hourly FFMC, ISI and FWI. |
| `dewpoint` | float32 | WF1 actuals only. |
| `wind_gust` | float32 | Data mart hourly observations only; WF1's records do not carry it. |
| `grass_curing` | float32 | Percent cured, on WF1's daily actuals and noon forecasts. |
| `danger_rating` | int8 | The forest danger class, 1 to 5, on daily actuals. |
| `observation_valid`, `observation_valid_comment` | bool, string | Whether WF1 accepted an actual, and why not. Null for the data mart, which does not say. Climatology leaves out a record WF1 marked invalid. |
| `run_ts` | timestamp, UTC | Models only: the run the row came from. |
| `ingested_at` | timestamp, UTC | When the row was written. |

What each source holds:

| Source | Hourly | Daily | Replaces |
|---|---|---|---|
| `ACTUALS` | Hourly observations from WF1 | WF1's daily actual for 20:00 UTC, fetched by the hourly actuals job. Its precipitation is the total WF1 accumulated over the 24 hours before, so nothing is summed here | `hourly_actuals` |
| `FORECAST` | The latest forecaster's forecast per station and hour, once hourly forecasts exist | The latest forecaster's noon forecast per station and day | `noon_forecasts` |
| Each model | The newest run's value for each prediction time | The newest run's 20:00 UTC row per day | The MoreCast queries on `weather_station_model_predictions` |

`morecast_2_materialized_view` has a model but no reader in the Python code, so it can be dropped with the tables.

`FORECAST` is the forecaster's forecast as WF1 holds it. WF1 keeps only the latest: publishing a forecast overwrites the previous one, so WF1 cannot supply forecast history. MoreCast can, because it saves a new record with a timestamp every time a forecaster submits. That history goes into `leads`.

For a model, the table covers future times as well as past ones. After appending a run to `runs`, the model's job merges the run into `by_time`, replacing each row the run predicts. Once a time has passed, its row stops changing and holds the last prediction made for it. That settled row is what climatology reads.

Each write is a Delta `MERGE` on station, timestamp, resolution and source, limited to the partitions it touches. Jobs for different sources write to different partitions.

`by_time` is entirely derived. The model rows can be rebuilt from `runs`, and the `ACTUALS` and `FORECAST` rows from `wf1`, in each case by taking the newest version.

FWI indices are out of scope for now. Adding them later means adding columns, which older files simply lack.

### `by_station`

The same rows as `by_time`, laid out by station: a Delta table partitioned by `resolution`, `station_code` and `year` (the UTC year), in place of `by_time`'s `resolution`, `source` and month. `source` is a column, and each file is sorted by source then time. A station's record is its own files, one per year, and a read opens only those.

A nightly job is the only writer (`wps_weather_data.by_station`, the `station-weather-by-station` cron job). It replaces the current year's rows with what `by_time` now holds, in one commit per resolution, so a reader sees a year either as it was or as it now is. A year that has ended is rebuilt only when asked for (`--from-year`), which is how a backfill of earlier years, or a correction to one, reaches this table. The maintenance job vacuums the files each rebuild replaces.

An earlier version of this design kept plain Parquet files per station: a `history.parquet` for the years that had ended and a file for the current year. It read faster, with no transaction log to open, but the nightly job then updated stations one at a time, a job that stopped part way left a year in two files for readers to reconcile, and the files went through a second S3 client. As a Delta table, at 300 stations and 40 years of daily observations (12,000 files), reading one station's whole record took 30 to 50 ms from local disk once the table was open. That has not been timed against ECS.

This copy lags `by_time` by up to a day. It is derived and can be rebuilt at any time.

### `hourly_profile`

One file per station, holding the count, mean, minimum and maximum of each weather variable per source, year, month and hour of day. The nightly job derives it from the hourly `by_station` files. It exists so that a screen can show hourly climatology for a group of stations without downloading every hourly value. See [Reads over 5, 10 and 30 years, for a screen](station-weather-storage-evaluation.md#reads-over-5-10-and-30-years-for-a-screen).

### `leads`

Every prediction for one station at every lead, in one plain Parquet file per station per year. For models it is `runs` regrouped by station, so that a station's history can be read at any lead without scanning every run. For forecasters it is every MoreCast submission, read from `morecast_forecast`.

| Column | Type | Notes |
|---|---|---|
| `source` | string | The model, or `FORECAST`. |
| `timestamp` | timestamp, UTC | The time predicted. |
| `run_ts` | timestamp, UTC | The run that made the prediction. For `FORECAST`, when the forecaster submitted it. |
| `lead_hours` | int16 | `timestamp` minus `run_ts`. Stored so a reader can filter on it directly. |
| Weather and bias-adjusted columns | float32 | As in `by_time`. |

Rows are sorted by source, then `timestamp`, then `lead_hours`, and each model's month is written as its own row group. A reader applies whatever rule it is testing: a fixed lead, a range of leads, the newest run before a cutoff hour, or every lead to see how skill changes with range. Observations to compare against come from the same station's `by_station` file.

It serves both shapes:

- **One station.** Fetch the station's file for each year. It is about 20 MB for six models.
- **A group of stations.** For each station, fetch the footer and then only the row groups for the models and months wanted, as ranged GETs.

The [lead benchmark](station-weather-storage-evaluation.md#lead-benchmark) is why there is no time-keyed copy.

The nightly job that writes `by_station` writes this too, from `runs` and `morecast_forecast`, rebuilding the current year's file each night.

This dataset exists for experimenting. Once a rule is settled, the cheaper form is to store that rule's result as another source in `by_time` and `by_station`, such as `HRDPS_DAY1`. Reads of a settled rule are then small whole-file reads, and `leads` can be dropped.

### Writes

`runs` and `by_time` each have several writers: the six model jobs, and for `by_time` the WF1 jobs as well. Delta Lake makes that safe by committing through its transaction log: of two writers that collide, one commits and the other retries or fails. What that does and does not guarantee, compared with Postgres, is under [Transaction guarantees](#transaction-guarantees).

On an S3-compatible store that safety depends on the store. The `deltalake` library has three ways to commit safely: a conditional PUT that the store must enforce (`If-None-Match`), a copy that fails if the target exists, or a DynamoDB lock. We have no DynamoDB next to our object store, so this design depends on Dell ECS enforcing conditional PUTs. It does: a check with four concurrent writers lost no commits, using the storage option `conditional_put: etag`. The library's fourth mode, `AWS_S3_ALLOW_UNSAFE_RENAME`, is only safe with a single writer per table.

If ECS does not enforce conditional PUTs, the fallback is one table per writer: a `runs` and `by_time` table per model, and one `by_time` table for the WF1 jobs. Each then has a single writer, and readers combine them. Compaction still works.

Every other dataset has exactly one writer: each model's job for its `staging` table, and the nightly job for `by_station`, `hourly_profile` and `leads`.

Delta Lake uses its own S3 client, not the pinned `aiobotocore`. Delta Lake has worked against our object store in an earlier trial.

### Transaction guarantees

These are not the guarantees Postgres gave. A single commit to a single Delta table is atomic, isolated and durable. Several things Postgres provided around that are gone, and the design covers them with jobs that can be run again safely.

| Property | Postgres | Delta Lake as used here |
|---|---|---|
| Atomicity | Any number of rows and tables in one transaction | One commit to one table is all or nothing. There are no transactions across tables. |
| Consistency | Primary keys, unique constraints, foreign keys, `NOT NULL` | The schema and column types are enforced. There are no unique or foreign key constraints. |
| Isolation | Readers and writers coordinate through locks and MVCC, and a conflicting writer waits | A reader sees one consistent version of a table. Writers are optimistic: a conflicting commit fails instead of waiting. |
| Durability | The write-ahead log, plus database backups | A commit is as durable as the object store. A table's history is its own log, kept for 30 days by `vacuum`. |

Where each difference shows up:

- **Publishing a run is three commits.** The job appends to `runs`, merges into `by_time`, then deletes from `staging`. A crash in between leaves the tables disagreeing until the job runs again. The order of the steps and the safe redo, described under [Run bookkeeping](#run-bookkeeping), are recovery, not atomicity. The WF1 jobs have the same shape: an append to `wf1`, then a merge into `by_time`, done once for the hourly observations and again for the daily actuals.
- **Uniqueness is by convention.** `by_time` has one row per station, time, resolution and source only because every writer goes through the `MERGE`. In `runs` and `wf1` a reprocessed run or a corrected value is a second row, and readers take the newest `ingested_at`. Postgres rejected a duplicate outright.
- **The `wf1` change check is not guarded.** The job reads the newest stored version, compares, then appends. Two overlapping runs of the same job could both append the same version, because appends never conflict with each other. A reader taking the newest version is unaffected; the history would hold a duplicate.
- **A merge that collides fails, and nothing retries it.** If another commit lands on `by_time` between a `MERGE` reading the table and committing, the library reports a commit failure. The jobs do not catch it: the job fails, and its next run makes the table good. The six model jobs, the two WF1 jobs and the daily `optimize` all write `by_time`. Whether merges into different partitions collide at all has not been checked against the version in use.
- **Everything rests on ECS enforcing conditional PUTs.** That is what stops two writers claiming the same commit. It was checked once, with four writers appending. Two merges at once, and a merge against `optimize`, have not been tested.
- **Backups are different.** Reading a table as it was covers 30 days of mistakes inside that table. It does not cover losing the bucket or a table's log, and what ECS provides for versioning or replication is not known.
- **A read is consistent within one table only.** Each read fetches the commits made since the last one, so it sees the table's latest version. Nothing ties two tables together: a job or request that reads `runs` and then `by_time` can see them at different moments, such as between the two commits of a run being published. In Postgres one transaction saw both tables at the same point.

This is acceptable for this data because it is append-only or derived, every job can be run again safely, and each source has one writer. It would not be acceptable for transactional data, which is why `morecast_forecast` stays in Postgres.

Two things remain to do before relying on it:

1. Test concurrent merges on ECS: two sources merging into `by_time` at once, and a merge racing `optimize`, checking for lost or duplicated rows.
2. Retry on a commit conflict around the merges into `by_time`, so that a collision costs a retry and not a failed job.

### Run bookkeeping

Three Postgres tables tracked ingest. The model jobs no longer use them: the state they held is read from `staging` and `runs` instead.

| Was, in Postgres | Question it answers | Now |
|---|---|---|
| `processed_model_run_urls` | Has this GRIB file been processed? | Does the run's `staging` partition have a marker row for it? |
| `prediction_model_run_timestamps.complete` | Has every GRIB file for the run been processed? | Does the run's `staging` partition have a marker row for every expected file? |
| `prediction_model_run_timestamps.interpolated` | Has the run been bias-adjusted and published? | Is the run in `runs`, with nothing left in `staging`? |
| `prediction_models` | What are the model's name and projection? | A constant in code, next to `ModelEnum` and `ProjectionEnum`. The table itself stays, because SFMS's `model_run_for_sfms` refers to it. |
| The integer run ID | Which run does this row belong to? | The model and `run_ts`. |

#### One job invocation

The job does this for each run its schedule covers. Env Canada and NOAA work out the runs with `model_run_timestamp`; ECMWF checks today's and yesterday's 00 and 12 UTC runs.

| Step | What happens | Code |
|---|---|---|
| 1. Skip a published run | A run in `runs` with nothing left in `staging` is done. The job moves on without downloading anything. | `run_is_published` in `common_model_fetchers.py` |
| 2. Find what is left | The job reads the run's marker rows once to learn which files are already processed. | `RunStager.__init__`, `StagingTable.processed_sources` |
| 3. Skip processed files | A file with a marker row, or one added in this invocation and not yet committed, is skipped. | `RunStager.is_processed` |
| 4. Process new files | The job downloads the file, extracts the value at each station, and adds the file with its values to the stager. | `EnvCanada.process_model_run_urls`, `NOAA.process_url`, `ECMWF.process_model_run` |
| 5. Commit in batches | Every 50 files, and in a `finally` at the end of the run, the stager writes one commit with the files' values and marker rows. | `RunStager.add`, `RunStager.flush`, `StagingTable.append_files` |
| 6. Check completeness | A run with a marker row for every expected file is complete, and the job publishes it. | `RunStager.is_complete`, `complete_runs` |

Env Canada and NOAA record a file by its URL. ECMWF records it by forecast hour, such as `fxx=003`, so a file fetched from any of its mirrors counts.

#### Publishing a complete run

| Step | What happens | Code |
|---|---|---|
| 1. Read the run back | The run's values, per station, one dict per prediction time in time order. A value staged twice takes the newest `written_at`. | `StagingTable.station_values` |
| 2. Read the training history | The model's recent runs from `runs`, read once for every station. | `read_model_history` in `machine_learning.py` |
| 3. Compute the station predictions | Precip, the interpolated 20:00 row and the bias adjustments, in memory. | `ModelValueProcessor._process_model_run_for_station`, `ECMWFPredictionProcessor._process_model_run_for_station` |
| 4. Append to `runs` | One commit with the whole run. | `RunsTable.append_run` |
| 5. Merge into `by_time` | Keyed on station, time, resolution and source. | `ByTimeTable.merge_run` |
| 6. Delete from `staging` | Drops the run's partition. | `StagingTable.delete_run` |

The steps run in this order on purpose: deleting from `staging` last is what makes a crash safe.

#### One value, from file to tables

An RDPS run starting 2026-11-17 12:00 UTC, at station 322, for 2026-11-18 20:00 UTC, 32 hours in. RDPS is hourly, so 20:00 is one of the model's own times and no row is interpolated. The values are made up; the shapes are real. All times are UTC.

**`staging`**, while the run downloads. RDPS publishes one file per variable and forecast hour, so the five values come from five files. Each file also leaves one marker row, written in the same commit as its values. This is the marker row of the temperature file; the other four files have one each.

| `run` | `run_ts` | `station_code` | `prediction_timestamp` | `variable` | `value` | `source` | `written_at` |
|---|---|---|---|---|---|---|---|
| `20261117T12` | 2026-11-17 12:00 | 322 | 2026-11-18 20:00 | `tmp_tgl_2` | 4.2 | `…_RDPS_AirTemp_AGL-2m_RLatLon0.09_PT032H.grib2` | 2026-11-17 15:10 |
| `20261117T12` | 2026-11-17 12:00 | 322 | 2026-11-18 20:00 | `rh_tgl_2` | 78.0 | `…_RDPS_RelativeHumidity_AGL-2m_RLatLon0.09_PT032H.grib2` | 2026-11-17 15:10 |
| `20261117T12` | 2026-11-17 12:00 | 322 | 2026-11-18 20:00 | `apcp_sfc_0` | 6.4 | `…_RDPS_Precip-Accum_Sfc_RLatLon0.09_PT032H.grib2` | 2026-11-17 15:10 |
| `20261117T12` | 2026-11-17 12:00 | 322 | 2026-11-18 20:00 | `wdir_tgl_10` | 210.0 | `…_RDPS_WindDir_AGL-10m_RLatLon0.09_PT032H.grib2` | 2026-11-17 15:40 |
| `20261117T12` | 2026-11-17 12:00 | 322 | 2026-11-18 20:00 | `wind_tgl_10` | 12.5 | `…_RDPS_WindSpeed_AGL-10m_RLatLon0.09_PT032H.grib2` | 2026-11-17 15:40 |
| `20261117T12` | 2026-11-17 12:00 | null | 2026-11-18 20:00 | null | null | `…_RDPS_AirTemp_AGL-2m_RLatLon0.09_PT032H.grib2` | 2026-11-17 15:10 |

Each value row is one station from one file, so a file covering 320 stations leaves 320 value rows and one marker row. `apcp_sfc_0` is the precip accumulated since the run started.

**`runs`**, once the run is published. The five staged values become one row with everything the job computed. `precip_24h` is 6.4 less the 3.3 accumulated by 2026-11-17 20:00 in the same run, and `delta_precip` is 6.4 less the 6.1 at 19:00.

| Column | Value |
|---|---|
| `model` | `RDPS` |
| `run_date` | 2026-11-17 |
| `station_code` | 322 |
| `run_ts` | 2026-11-17 12:00 |
| `prediction_timestamp` | 2026-11-18 20:00 |
| `tmp_tgl_2` | 4.2 |
| `rh_tgl_2` | 78.0 |
| `apcp_sfc_0` | 6.4 |
| `wdir_tgl_10` | 210.0 |
| `wind_tgl_10` | 12.5 |
| `bias_adjusted_temperature` | 5.0 |
| `bias_adjusted_rh` | 74.0 |
| `bias_adjusted_wdir` | 205.0 |
| `bias_adjusted_wind_speed` | 9.8 |
| `delta_precip` | 0.3 |
| `precip_24h` | 3.1 |
| `bias_adjusted_precip_24h` | 2.7 |
| `ingested_at` | 2026-11-17 16:42 |
| `is_interpolated` | false |

`model` and `run_date` are the partition. A run published again is appended with a later `ingested_at`, and readers take the newest.

**`by_time`**, merged from the `runs` row. Every prediction becomes an `hourly` row, and a 20:00 UTC prediction also becomes a `daily` row. The two differ only in their precipitation: the hourly row carries the precip since the previous prediction, the daily row the 24 hour total and its bias adjustment.

| Column | `hourly` row | `daily` row |
|---|---|---|
| `resolution` | `hourly` | `daily` |
| `source` | `RDPS` | `RDPS` |
| `month` | `2026-11` | `2026-11` |
| `station_code` | 322 | 322 |
| `timestamp` | 2026-11-18 20:00 | 2026-11-18 20:00 |
| `temperature` | 4.2 | 4.2 |
| `relative_humidity` | 78.0 | 78.0 |
| `wind_speed` | 12.5 | 12.5 |
| `wind_direction` | 210.0 | 210.0 |
| `precipitation` | 0.3 (`delta_precip`) | 3.1 (`precip_24h`) |
| `bias_adjusted_temperature` | 5.0 | 5.0 |
| `bias_adjusted_relative_humidity` | 74.0 | 74.0 |
| `bias_adjusted_wind_speed` | 9.8 | 9.8 |
| `bias_adjusted_wind_direction` | 205.0 | 205.0 |
| `bias_adjusted_precipitation` | null | 2.7 (`bias_adjusted_precip_24h`) |
| `run_ts` | 2026-11-17 12:00 | 2026-11-17 12:00 |
| `ingested_at` | 2026-11-17 16:42 | 2026-11-17 16:42 |

`resolution`, `source` and `month` are the partition. There is one row per station, time, resolution and source. The next RDPS run that predicts 2026-11-18 20:00 replaces both rows, so `run_ts` says which run a row came from. MoreCast reads the `daily` rows.

After publishing, these rows, and every other row in the `20261117T12` partition, are deleted from `staging`.

#### What the next invocation does after a failure

| Where the job stopped | What the next invocation finds | What it does |
|---|---|---|
| Partway through downloading | The run in `staging`, not in `runs` | Processes the files that have no marker row yet. Files since the last commit are fetched again. |
| Downloaded, but publishing failed | The run complete in `staging`, not in `runs` | Publishes it again. |
| After appending to `runs`, before deleting from `staging` | The run in both | Publishes it again. The second append is a newer version of the run, which readers prefer, and the keyed merge is harmless to repeat. |
| The run produced no station predictions | The run complete in `staging`, an error logged | Leaves it there, so it is not downloaded again. |
| Finished | The run in `runs` only | Skips it. |

A run left half-downloaded once it has dropped out of the job's schedule, about a day later, stays in `staging` unfinished. The old Postgres bookkeeping had the same reach. The maintenance job compacts and vacuums every model's `staging` table, and a deleted run's files are removed once they are older than the vacuum retention.

Reprocessing a published run is deliberate, not something the job does by itself: an operator asks for a model and run, the job downloads it again and appends it as a newer version.

The API had one bookkeeping read: fire watch looked up the newest interpolated ECMWF run. It now asks `runs` for the newest ECMWF run of the last seven days, and `fire_watch_weather` records the run's start time instead of its `prediction_model_run_timestamps` id.

`model_run_for_sfms` and `saved_model_run_for_sfms_urls` also live in Postgres. They track RDPS grids saved for SFMS, not station data, and are outside this design.

### Maintenance

Delta tables need three chores, run by a scheduled job:

- **`optimize`** merges small files. `runs` gets one small file per run, and `by_time` gets new files on every `MERGE`.
- **`vacuum`** deletes files no longer referenced. Without it, `by_time` grows by about a hundred times its live size in two months. The retention window is how far back time travel reaches; 30 days is a reasonable start.
- **Checkpoints** keep the transaction log short, so opening a table stays fast.

This replaces the `pgslice` partition job and the `pg_dump` archive.

### Reprocessing history

`runs` and `wf1` are append-only. Reprocessing a run appends it again with a new `ingested_at`, and the earlier version stays. Nothing is copied or replaced, so there is no second table and nothing for a crash to leave half-done.

A run is always reprocessed whole, so the version belongs to the run, not the row. A reader of `runs` takes the newest `ingested_at` for each model and run. Two readers touch `runs` directly, the `/weather_models` routes and training, and both go through one shared read function that applies this. `by_time`, `by_station` and `leads` are built from the newest version, so nothing downstream sees a duplicate.

What this keeps:

- **Model values.** Every version of every run, permanently.
- **Forecasts.** Every MoreCast submission, in `leads`.
- **Observations and WF1 forecasts.** Every version, permanently, in `wf1`. It works the same way as `runs`: a correction is a new row with a later `ingested_at`. Corrections are expected to be rare, so this costs almost nothing.

### Reads

| Reader | Reads | Objects |
|---|---|---|
| MoreCast grid | `by_time`, daily, every source | About 1 file per source and month after compaction |
| Climatology, one station | `by_station` | 1 file per year the station has |
| Climatology, a group, daily | `by_station` | 1 file per station and year |
| Climatology, a group, hourly | `hourly_profile` | 1 per station |
| Climatology at a chosen lead | `leads`, with ranged GETs | Per station and year: 1 footer, plus 1 row group per model per month wanted |
| Fire watch | `runs`, one run of one model | The run's files in its `run_date` partition |
| `/weather_models` routes | `runs`, for run dates in the window | About 12 files per model after compaction |
| Bias-adjustment training | `runs` for the 19-day window and `by_time` for the observations, loaded once per job | About 23 files for RDPS after compaction |
| Ingest | The run's `staging` files, and observed precipitation from `by_time` | A handful per run |

Reading a Delta table starts with its transaction log. A cold open took about 200 ms in the local benchmark and 839 ms against our object store, on a tiny table with a fresh checkpoint. API pods should keep table state in memory and refresh it, not reopen the table on every request.

`by_station` is read through Delta Lake, limited to the station's partitions. The Parquet files are fetched through the existing S3 client and filtered with `pyarrow`. Ranged GETs are used for group reads of `leads`. The API computes climatology statistics on demand and can cache them.

### Retention

`by_time`, `by_station` and `hourly_profile` are kept indefinitely: they are the climatology record and cost about 1.1 GB a year together.

`runs` and `wf1` are kept indefinitely too. They are the only complete records, and everything else is rebuilt from them. `runs` is the large one, at about 4.5 GB a year as float32; `wf1` is small.

`leads` is about 6 GB a year. It can be dropped and rebuilt from `runs` and `morecast_forecast` at any time.

### What stays in Postgres

Nothing for station weather. The model jobs no longer use the database at all. The related tables that stay are:

- `morecast_forecast`, which holds forecasts as forecasters submit them in MoreCast. It is transactional application data. The nightly job reads it to build the `FORECAST` rows in `leads`.
- `prediction_models`, which SFMS's `model_run_for_sfms` refers to.

No code reads or writes the six legacy tables: `weather_station_model_predictions`, `model_run_predictions`, `prediction_model_run_timestamps`, `processed_model_run_urls`, `hourly_actuals` and `noon_forecasts`. They stay, with the `pgslice` jobs, until `backend/scripts/station_weather_backfill.py` has copied production's history into `runs`, `wf1` and `by_time` and the result has been checked. A follow-up migration then drops them.

### Behaviour to preserve

- **Which run wins.** Today the daily queries keep the most recently updated row per station, model and day. `by_time` keeps the newest run's row. These differ if an old run is reprocessed.
- **The integer run ID.** `ModelPredictionDetails` carried `prediction_model_run_timestamp_id`, and fire watch passed it between queries. It is now the run's start time; fire watch only uses ECMWF, so that identifies the run.
- **`id` and `update_date`.** The route `POST /weather_models/{model}/predictions/most_recent/{start_date}/{end_date}` returns the database row's `id` and `update_date` for each prediction. Neither exists once the table is gone. No caller of that route was found in the web or mobile code, so the plan is to drop both fields. The API is public, so an outside caller cannot be ruled out.
- **Training's noon value.** Training rebuilds the 20:00 UTC interpolation from the neighbouring raw rows, while `runs` already stores it. `test_machine_learning_golden.py` is the place to confirm training gives the same output from either source.
- **Observation validity.** `hourly_actuals` carried a validity flag per variable, and training kept an hour only when its temperature and RH were valid. In `by_time` an invalid value is null, so training keeps an hour with both values present. `wps_wf1` also sets the wind speed and wind direction flags the wrong way round (`get_valid_flags` returns them in the other order); the null rule uses each value's own range instead.
- **Observation joins.** Training joined predictions to `hourly_actuals` in SQL, and ingest summed observed precipitation per station. Both now read `ACTUALS` from `by_time` once per run being published (`StationObservations` in `wps_weather_data/actuals.py`). Summing hours with a missing precip used to give NaN in Postgres. Now the 24 hour precip of a run's first day adds the hours that have a value, and a training day with an hour missing its precip has no total and is not learned from.
- **NAM precip.** `model_run_predictions` holds NAM's original precip value alongside the accumulated one. If anything needs it after ingest, `runs` needs a column for it.

## Main risks

Nothing here is built. The full list of what was and was not checked is in [station-weather-storage-evaluation.md](station-weather-storage-evaluation.md#what-is-and-isnt-verified). The ones that could change the design:

1. **Several Delta writers on ECS.** Checked on 2026-11-16 with `backend/scripts/object_store_delta_check.py`: four processes appending to one table at once lost no commits. That is one run, from one machine, on a tiny table, so the first real slice should keep checking for lost runs. The fallback is one table per writer.
2. **Latency against ECS.** A cold open of a tiny Delta table took 839 ms against our object store. Every other timing is from local disk, and no real read path has been timed.
3. **Delta Lake at full size.** `MERGE` was benchmarked on a small daily table only, not on `by_time` with hourly data.
4. **Station count.** The benchmarks assume 300; the dev deployment had 320. Sizes and row counts scale with it.
5. **The climatology screen.** What it shows is undecided, and one read, pooled hourly percentiles for a group over decades, is not served.
6. **Weaker guarantees than Postgres.** No transactions across tables, no unique constraints, and a colliding merge fails instead of waiting. Concurrent merges on ECS are untested and the jobs do not retry. See [Transaction guarantees](#transaction-guarantees).

## Plan

1. Done on 2026-11-16: `backend/scripts/object_store_delta_check.py` ran Delta Lake against ECS in a throwaway table. Four writers appending at once lost no commits, `MERGE`, `optimize`, `vacuum` and a checkpoint worked, and the storage option to use is `conditional_put: etag`. Shared tables are confirmed.
2. Done: the six model jobs write `runs` and `by_time`, and a daily cron job runs `optimize`, a checkpoint and `vacuum` on every table. Checked in a dev deployment on 2026-11-17: the maintenance job compacted both tables.
3. Done for MoreCast's model read in a dev deployment on 2026-11-16: `by_time` and Postgres agreed on all 6,936 values. Timings from inside the cluster are still to do; the MoreCast and fire watch reads log theirs.
4. Done: MoreCast reads its model values from `by_time`, fire watch reads its ECMWF run from `runs`, and training reads `runs` (see "Training reads `runs`" below). The `/weather_models` routes were removed separately (#6060). Nothing falls back to Postgres, so a deployment's tables must be filled with `backend/scripts/station_weather_backfill.py` before it serves users: `by_time` for the days MoreCast shows, and `runs` and `ACTUALS` for the 19 days training learns from.
5. and 6. Done: every model job stages runs in `staging` instead of `model_run_predictions`, keeps its bookkeeping in `staging` and `runs`, and no longer writes `weather_station_model_predictions`. Dropping the four legacy tables and retiring the `pgslice` job waits for the production backfill, as described under "What stays in Postgres".
7. Done: the WF1 jobs write `ACTUALS` and `FORECAST` to `wf1` and `by_time` only, training and ingest read `ACTUALS` from `by_time`, and the two noon forecast routes (`POST /forecasts/noon/` and `/forecasts/noon/summaries/`), which no web or mobile code called, are removed. `hourly_actuals` and `noon_forecasts` wait for the production backfill, with the other legacy tables.
8. Add the nightly job that writes `by_station`, `hourly_profile` and `leads`, and build the climatology reads on them. `by_station` is written, as a Delta table: built from three real years of data mart observations in local tables, a station's daily record matched `by_time`. It has not run against ECS. The first climatology read is built on it: `GET /api/climatology/daily?station_codes=…` returns, for each day of the year, the lowest, 25th, median, 75th, 90th and highest of the stations' daily actuals over every year but one, and that year's values to compare. Several stations, up to 150, are combined one of three ways: `average` takes each day's mean of the stations that reported it, `pooled` draws the distribution from every station's value and compares the year's mean, and `each` returns a climatology per station. Each day carries how many stations contributed, because a group's membership changes over the decades. The web page at `/insights/climatology` charts it as percentile bands with the median and the selected year, one chart per station for `each`, and offers fire centres, fire zones (`GET /api/climatology/fire-centres`, from WF1) and saved station groups as ways to choose stations. The statistics are computed on request from the stations' `by_station` rows, read in one pass over their partitions; a group read has not been timed against ECS. `hourly_profile`, `leads` and the group and hourly climatology reads are not built. The observations it needs from before these tables existed come from the BCWS data mart, which has hourly observations back to 1987: `backend/scripts/station_actuals_data_mart_backfill.py` copies them into `wf1` and `by_time` as `ACTUALS`, hourly and daily; the daily rows are the noon rows that carry WF1's daily precip total. Postgres never held the daily actuals, so `station_weather_backfill.py` copies hourly ones only. Tried on the 1987 file and three days of 2026 against local tables, not yet against ECS or for every year.

Steps 7 and 8 do not depend on steps 4 to 6. History only accumulates once `by_time` is being written, so steps 2 and 7 are worth starting early even if readers move later.

### Training reads `runs`

Bias adjustment learns, per station, from the model's own values paired with hourly observations over the last 19 days, and from every run's 24 hour precip prediction. The model values come from `runs` and the observations from `by_time`'s `ACTUALS`, each read once per run being processed:

- An observation is paired with the newest run's value at that time, among the rows the job did not interpolate. A row whose `is_interpolated` is unknown, as in a run backfilled after its `model_run_predictions` were deleted, counts as the model's own except at 20:00 UTC, the only hour the job interpolates.
- The SQL this replaces outer-joined observations to predictions but then filtered on the prediction's model, which dropped observations with no prediction. The new read keeps that behaviour, so the noon sample the training code builds for 3-hourly models still only appears where a run has a 20:00 value. Whether that sample was ever meant to be built is a question for a separate change.
- A run that is still downloading is not in `runs`, so it no longer contributes its first hours, as the old query could.
- Values are float32, so the fitted regressions differ from the Postgres ones in about the seventh significant digit.

## Open questions

1. **How do API pods avoid the cold open?** Opening a Delta table took 839 ms against our object store. The design says to keep table state in memory and refresh it; how, and how stale it may be, is not worked out.
2. **Which lead rules are worth keeping?** Undecided. Lead stays a free choice while we experiment with `leads`. Rules that prove useful should become their own sources in `by_time` and `by_station`.
3. **What does the climatology screen show?** Undecided. The design assumes percentiles by day of year for daily data, and statistics by month and hour of day for hourly data. A screen that needs pooled hourly percentiles for a group over decades is the one case this does not serve.
4. **Where will hourly forecasts come from, and will their history be recorded?**
5. **How long is the `vacuum` retention window?** It sets how far back Delta time travel reaches. 30 days is the proposed start.
