# Station weather data on object storage

**Status:** draft for discussion · 2026-11-12

## Summary

This proposes moving station weather data out of Postgres and onto object storage. That covers model predictions, observations and forecasts at each weather station.

The layouts follow from the reads we need to support:

- **Every model run** is kept, for the `/weather_models` routes and training.
- **Station history**, one value per station, time and source, is kept in two layouts: by time for MoreCast, and by station for climatology. Climatology statistics are computed on demand from the station files, for one station or a group, over any number of years.

We compared Parquet, GeoParquet, Delta Lake, Zarr and Icechunk with four local benchmarks, written up in [station-weather-storage-evaluation.md](station-weather-storage-evaluation.md). The design uses two of them:

- **Delta Lake** for the two tables that jobs write to, `runs` and `by_time`. Several jobs write to each, and both need compaction. That is what Delta Lake is for.
- **Plain Parquet** for the files derived from them, which have a single writer and are read by screens.

GeoParquet and Icechunk are a poor fit. Zarr is a poor fit for model runs and a reasonable but second-best fit for station history.

Nothing here is built, and nothing has been timed against our object store. The largest unknown is whether our object store supports what Delta Lake needs for more than one writer per table. See [Main risks](#main-risks).

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

The first three use cases read the same logical table: one value per station, time and source, where the source is `OBSERVED`, `FORECAST` or a model. This is the shape MoreCast already uses in `WeatherIndeterminate`. For a model, the value at a given time is the one from the newest run that predicted it. The last two need every run.

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
  staging/model=HRDPS/2026111206/<invocation time>.parquet station values while a run downloads
  by_station/resolution=hourly/station=322/history.parquet the by_time rows, keyed by station
  hourly_profile/station=322.parquet                       hourly statistics by month and hour of day
  leads/station=322/2026.parquet                           every prediction at every lead, per station
```

`resolution` is `hourly` or `daily`. `source` is `OBSERVED`, `FORECAST` or a model.

| Dataset | Format | Serves | Written by |
|---|---|---|---|
| `runs` | Delta Lake | `/weather_models` routes, training | The six model jobs |
| `wf1` | Delta Lake | Rebuilding `by_time`; history of corrections | The WF1 jobs |
| `by_time` | Delta Lake | MoreCast, fire watch | The model jobs and the WF1 jobs |
| `by_station` | Parquet | Climatology for one station or a group | One nightly job |
| `hourly_profile` | Parquet | Hourly climatology for a group, on a screen | The same nightly job |
| `leads` | Parquet | Climatology at a chosen lead, while experimenting | The same nightly job |

The Parquet files have deterministic keys: a reader computes the key from the station and never lists the bucket. The Delta tables are read through their transaction log.

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

Every observation and forecaster's forecast as fetched from WF1. It is to observations what `runs` is to models: an append-only record that `by_time` is built from. It is a Delta table partitioned by `source` (`OBSERVED` or `FORECAST`), `resolution` and month, with the same columns as `by_time`.

The WF1 jobs append a row only when it is new or differs from the newest version already stored, with the `ingested_at` of that fetch. A corrected observation is therefore a second row with a later `ingested_at`, and the original stays.

A side effect is that it records forecast history from now on, even though WF1 itself keeps only the latest forecast: each time a forecast changes between fetches, the new value is appended. That history is only as fine as the fetch interval, and it covers forecasts published by any tool, not only MoreCast.

### `staging`

Replaces `model_run_predictions`. It holds a run that is still downloading.

A run arrives as hundreds of GRIB files, one per variable per forecast hour, published over a span of time. The cron job processes whatever is available, exits, and returns later for the rest. Bias adjustment needs the whole run, so the partial run has to be kept somewhere between invocations.

Each job invocation writes one Parquet file under the run's prefix, holding the station values from every GRIB file it processed:

| Column | Type | Notes |
|---|---|---|
| `station_code` | int32 | |
| `prediction_timestamp` | timestamp, UTC | |
| `variable` | string | Which model field the value is, such as `tmp_tgl_2`. |
| `value` | float32 | |

The names of the GRIB files the invocation covered are recorded in the Parquet file's metadata, so the job can tell what has been processed by reading the footers alone.

A run then has a handful of staging files, one per invocation, instead of one per GRIB, which would be roughly 245 objects for an HRDPS run and 405 for GDPS. The cost is that a crash loses the GRIB files processed so far in that invocation, and the next invocation fetches them again. An invocation that processes many files can write more than once to bound that.

When the run is complete, the job reads the staging files back, computes bias adjustments and derived precip in memory, appends the run to `runs`, merges it into `by_time`, and deletes the staging prefix. Staging files are plain Parquet with one writer.

### `by_time`

A Delta table partitioned by `resolution`, `source` and month. It holds one row per station and time.

| Column | Type | Notes |
|---|---|---|
| `station_code` | int32 | |
| `timestamp` | timestamp, UTC | The hour for `hourly`. The 20:00 UTC noon record for `daily`. |
| `temperature`, `relative_humidity`, `wind_speed`, `wind_direction` | float32 | |
| `precipitation` | float32 | The hour's precipitation for `hourly`, the 24-hour total for `daily`. |
| `bias_adjusted_temperature`, `bias_adjusted_relative_humidity`, `bias_adjusted_wind_speed`, `bias_adjusted_wind_direction`, `bias_adjusted_precipitation` | float32 | Models only, null otherwise. |
| `run_ts` | timestamp, UTC | Models only: the run the row came from. |
| `ingested_at` | timestamp, UTC | When the row was written. |

What each source holds:

| Source | Hourly | Daily | Replaces |
|---|---|---|---|
| `OBSERVED` | Hourly observations from WF1 | The noon observation | `hourly_actuals` |
| `FORECAST` | The latest forecaster's forecast per station and hour, once hourly forecasts exist | The latest forecaster's noon forecast per station and day | `noon_forecasts` |
| Each model | The newest run's value for each prediction time | The newest run's 20:00 UTC row per day | The MoreCast queries on `weather_station_model_predictions` |

`morecast_2_materialized_view` has a model but no reader in the Python code, so it can be dropped with the tables.

`FORECAST` is the forecaster's forecast as WF1 holds it. WF1 keeps only the latest: publishing a forecast overwrites the previous one, so WF1 cannot supply forecast history. MoreCast can, because it saves a new record with a timestamp every time a forecaster submits. That history goes into `leads`.

For a model, the table covers future times as well as past ones. After appending a run to `runs`, the model's job merges the run into `by_time`, replacing each row the run predicts. Once a time has passed, its row stops changing and holds the last prediction made for it. That settled row is what climatology reads.

Each write is a Delta `MERGE` on station, timestamp, resolution and source, limited to the partitions it touches. Jobs for different sources write to different partitions.

`by_time` is entirely derived. The model rows can be rebuilt from `runs`, and the `OBSERVED` and `FORECAST` rows from `wf1`, in each case by taking the newest version.

FWI indices are out of scope for now. Adding them later means adding columns, which older files simply lack.

### `by_station`

The same rows as `by_time`, with `source` as a column, keyed by station. Each station has two files per resolution:

- `history.parquet` holds every closed year.
- `<year>.parquet` holds the current year.

Both are sorted by source then time, with one row group per source per year. One source's whole history is a single contiguous byte range, so a reader wanting one source makes two requests per file, and a reader wanting everything fetches the file whole.

These are plain Parquet files. A nightly job is the only writer. It rebuilds each station's current-year file from `by_time`. At the end of a year it merges that year into the station's history file. After 30 years a history file is about 5 MB for daily data and about 56 MB for hourly.

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

`runs` and `by_time` each have several writers: the six model jobs, and for `by_time` the WF1 jobs as well. Delta Lake makes that safe by committing through its transaction log, where one of two colliding writers retries.

On an S3-compatible store that safety depends on the store. The `deltalake` library has three ways to commit safely: a conditional PUT that the store must enforce (`If-None-Match`), a copy that fails if the target exists, or a DynamoDB lock. We have no DynamoDB next to our object store, so this design depends on Dell ECS enforcing conditional PUTs. That has not been tested. The library's fourth mode, `AWS_S3_ALLOW_UNSAFE_RENAME`, is only safe with a single writer per table.

If ECS does not enforce conditional PUTs, the fallback is one table per writer: a `runs` and `by_time` table per model, and one `by_time` table for the WF1 jobs. Each then has a single writer, and readers combine them. Compaction still works.

Every other dataset has exactly one writer: each model's job for its `staging` prefix, and the nightly job for `by_station`, `hourly_profile` and `leads`.

Delta Lake uses its own S3 client, not the pinned `aiobotocore`. Delta Lake has worked against our object store in an earlier trial.

### Run bookkeeping

Three Postgres tables track ingest today. All three go, and the state they hold is read from object storage instead. After that the model jobs do not use the database for bookkeeping at all.

| Today, in Postgres | Question it answers | Replacement |
|---|---|---|
| `processed_model_run_urls` | Has this GRIB file been processed? | Is its name listed in the metadata of one of the run's `staging` files? |
| `prediction_model_run_timestamps.complete` | Has every GRIB file for the run been processed? | Do the run's `staging` files between them list every expected GRIB? Listing the prefix and reading a few footers answers this and the question above. |
| `prediction_model_run_timestamps.interpolated` | Has the run been bias-adjusted and published? | Is the run in `runs`, with its `staging` prefix gone? |
| `prediction_models` | What are the model's name and projection? | A constant in code, next to `ModelEnum` and `ProjectionEnum`. |
| The integer run ID | Which run does this row belong to? | The model and `run_ts`. |

A run moves through these states:

1. **Downloading.** Each invocation leaves one file under `staging`, listing the GRIB files it processed. The next invocation reads those lists and skips what is done.
2. **Complete.** Every expected GRIB file is listed. The job computes bias adjustments and derived precip in memory.
3. **Published.** The job appends the run to `runs`, merges it into `by_time`, then deletes the `staging` prefix, in that order.

Deleting `staging` last is what makes a crash safe. A run that is in `runs` but still has a `staging` prefix was interrupted, and the job repeats step 3 from the start. Repeating it is harmless: a second append is just a newer version of the same run, and the merge is keyed.

At the start of each invocation the job checks the handful of recent runs it might need to fetch. A run already in `runs` with no `staging` prefix is skipped outright. That check reads the Delta log's partition values and file statistics, not the data.

Reprocessing a published run is deliberate, not something the job does by itself: an operator asks for a model and run, the job downloads it again and appends it as a newer version.

The API has one bookkeeping read today: fire watch looks up the newest published run for a model. It reads `by_time` instead, where each row carries the `run_ts` it came from.

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
| Climatology, one station | `by_station` | 2 files, whole or one byte range each |
| Climatology, a group, daily | `by_station` | 2 files per station |
| Climatology, a group, hourly | `hourly_profile` | 1 per station |
| Climatology at a chosen lead | `leads`, with ranged GETs | Per station and year: 1 footer, plus 1 row group per model per month wanted |
| Fire watch | `by_time`, daily, one model | About 1 file per month after compaction |
| `/weather_models` routes | `runs`, for run dates in the window | About 12 files per model after compaction |
| Bias-adjustment training | `runs` for the 19-day window and `by_time` for the observations, loaded once per job | About 23 files for RDPS after compaction |
| Ingest | The run's `staging` files, and observed precipitation from `by_time` | A handful per run |

Reading a Delta table starts with its transaction log, which took about 200 ms cold in the benchmark. API pods should keep table state in memory and refresh it, not reopen the table on every request.

The Parquet files are fetched through the existing S3 client and filtered with `pyarrow`. Ranged GETs are used for single-source reads of `by_station` and for group reads of `leads`. The API computes climatology statistics on demand and can cache them.

### Retention

`by_time`, `by_station` and `hourly_profile` are kept indefinitely: they are the climatology record and cost about 1.1 GB a year together.

`runs` and `wf1` are kept indefinitely too. They are the only complete records, and everything else is rebuilt from them. `runs` is the large one, at about 4.5 GB a year as float32; `wf1` is small.

`leads` is about 6 GB a year. It can be dropped and rebuilt from `runs` and `morecast_forecast` at any time.

### What stays in Postgres

Nothing for model runs. The only related table that stays is:

- `morecast_forecast`, which holds forecasts as forecasters submit them in MoreCast. It is transactional application data. The nightly job reads it to build the `FORECAST` rows in `leads`.

### Behaviour to preserve

- **Which run wins.** Today the daily queries keep the most recently updated row per station, model and day. `by_time` keeps the newest run's row. These differ if an old run is reprocessed.
- **The integer run ID.** `ModelPredictionDetails` carries `prediction_model_run_timestamp_id`, and fire watch passes it between queries. It becomes the model and `run_ts`.
- **`id` and `update_date`.** The route `POST /weather_models/{model}/predictions/most_recent/{start_date}/{end_date}` returns the database row's `id` and `update_date` for each prediction. Neither exists once the table is gone. No caller of that route was found in the web or mobile code, so the plan is to drop both fields. The API is public, so an outside caller cannot be ruled out.
- **Training's noon value.** Training rebuilds the 20:00 UTC interpolation from the neighbouring raw rows, while `runs` already stores it. `test_machine_learning_golden.py` is the place to confirm training gives the same output from either source.
- **Observation validity.** `hourly_actuals` carries a validity flag per variable, and training filters on them. In `by_time` an invalid value is null, so the filter becomes a null check.
- **Observation joins.** Training joins predictions to `hourly_actuals` in SQL, and ingest sums observed precipitation per station. Both become reads of the `OBSERVED` files.
- **NAM precip.** `model_run_predictions` holds NAM's original precip value alongside the accumulated one. If anything needs it after ingest, `runs` needs a column for it.

## Main risks

Nothing here is built. The full list of what was and was not checked is in [station-weather-storage-evaluation.md](station-weather-storage-evaluation.md#what-is-and-isnt-verified). The ones that could change the design:

1. **Conditional PUTs on ECS.** Several writers per Delta table depend on ECS enforcing them. This is untested, and it is step 1 of the plan. The fallback is one table per writer.
2. **Latency against ECS.** Every timing is from local disk. Nothing has been read from or written to our object store.
3. **Delta Lake at full size.** `MERGE` was benchmarked on a small daily table only, not on `by_time` with hourly data.
4. **Station count.** 300 is an assumption. Sizes and row counts scale with it.
5. **The climatology screen.** What it shows is undecided, and one read, pooled hourly percentiles for a group over decades, is not served.

## Plan

1. Check conditional PUTs on ECS. `backend/scripts/object_store_conditional_put_check.py` tests, one request at a time, whether the store honours them. If it does, run it again with `--race-rounds` to test many writers at once, then follow up with two concurrent writers to one Delta table. The result decides between shared tables and one table per writer.
2. Have one model (GDPS) write to `runs` and `by_time` alongside its Postgres writes, with the maintenance job running.
3. Compare every read query's results between the two, and time each read against ECS.
4. Move the model readers over one at a time: `/weather_models` routes, fire watch, training, then MoreCast's model values.
5. Replace `model_run_predictions` with `staging` for that model, and switch its bookkeeping from the Postgres tables to `staging` and `runs`.
6. Extend to the other models, stop writing the two prediction tables and the three bookkeeping tables, and retire them along with the `pgslice` job.
7. Have the WF1 jobs write `OBSERVED` and `FORECAST` to `wf1` and `by_time` alongside Postgres, then move their readers and retire `hourly_actuals` and `noon_forecasts`.
8. Add the nightly job that writes `by_station`, `hourly_profile` and `leads`, and build the climatology reads on them.

Steps 7 and 8 do not depend on steps 4 to 6. History only accumulates once `by_time` is being written, so steps 2 and 7 are worth starting early even if readers move later.

Postgres remains the fallback for each table until its readers have moved.

## Open questions

1. **Does ECS enforce conditional PUTs?** Everything about shared Delta tables depends on it. This is step 1 of the plan.
2. **Which lead rules are worth keeping?** Undecided. Lead stays a free choice while we experiment with `leads`. Rules that prove useful should become their own sources in `by_time` and `by_station`.
3. **What does the climatology screen show?** Undecided. The design assumes percentiles by day of year for daily data, and statistics by month and hour of day for hourly data. A screen that needs pooled hourly percentiles for a group over decades is the one case this does not serve.
4. **Where will hourly forecasts come from, and will their history be recorded?**
5. **How long is the `vacuum` retention window?** It sets how far back Delta time travel reaches. 30 days is the proposed start.
