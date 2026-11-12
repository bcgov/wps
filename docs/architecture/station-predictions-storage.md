# Station weather data on object storage

**Status:** draft for discussion · 2026-11-12

## Summary

This proposes moving station weather data out of Postgres and onto object storage. That covers model predictions, observations and forecasts at each weather station.

The layouts follow from the reads we need to support:

- **Every model run** is kept, for the `/weather_models` routes, training and fire watch.
- **Station history**, one value per station, time and source, is kept in two layouts: by time for MoreCast, and by station for climatology. Climatology statistics are computed on demand from the station files, for one station or a group, over any number of years.

We compared Parquet, GeoParquet, Delta Lake, Zarr and Icechunk with four local benchmarks. The design uses two of them:

- **Delta Lake** for the two tables that jobs write to, `runs` and `by_time`. Several jobs write to each, and both need compaction. That is what Delta Lake is for.
- **Plain Parquet** for the files derived from them, which have a single writer and are read by screens.

GeoParquet and Icechunk are a poor fit. Zarr is a poor fit for model runs and a reasonable but second-best fit for station history.

Nothing here is built, and nothing has been timed against our object store. The largest unknown is whether our object store supports what Delta Lake needs for more than one writer per table. See [What is and isn't verified](#what-is-and-isnt-verified).

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

## Benchmark: formats

`backend/scripts/station_predictions_storage_benchmark.py` writes the same synthetic predictions to all five formats and times the reads our code makes. Run it with:

```bash
uv run backend/scripts/station_predictions_storage_benchmark.py --days 60 --stations 300
```

The data follows the six models' real run cadence and forecast hours, including the interpolated 20:00 UTC rows. The results below are for 60 days and an assumed 300 stations: 18.6 million rows in 1,200 model runs.

It runs on local disk. Sizes and object counts carry over to object storage; latencies do not, and on object storage the number of objects read matters more than local read time. The floats are random at full precision, so sizes are an upper bound.

Layouts tested:

| Format | Layout |
|---|---|
| Parquet | One file per run, under `model=…/run_date=…/`, sorted by station then prediction time. |
| GeoParquet | The same, with each station's point geometry on every row. |
| Delta Lake, runs table | One append per run, partitioned by model and run date. |
| Delta Lake, daily table | The 20:00 UTC row per station and day, updated by `MERGE` after each run. |
| Zarr | One group per model, one array per variable with dimensions (run, step, station), one chunk per run. |
| Icechunk | The same arrays, one commit per run. |

Storage and writes:

| Format | Size | Objects | Bytes per row | Write per run |
|---|---|---|---|---|
| Parquet | 1.53 GB | 1,200 | 82 | 6 ms |
| GeoParquet | 1.55 GB | 1,200 | 83 | 11 ms |
| Delta Lake, runs table | 1.63 GB | 2,413 | 88 | 39 ms |
| Delta Lake, daily table | 11 MB live, 1.22 GB on disk before `vacuum` | 2,413 | n/a | 51 ms |
| Zarr | 1.22 GB | 14,491 | 66 | 54 ms |
| Icechunk | 1.32 GB | 33,819 | 71 | 38 ms |

Reads, as median milliseconds with the number of objects read in brackets:

| Format | MoreCast: 20:00 UTC, 5 days, all stations, all models | 5 stations, HRDPS, 15-day window, all runs | Training: RDPS, 19 days, raw values | One RDPS run |
|---|---|---|---|---|
| Parquet | 129 (300) | 58 (48) | 68 (96) | 25 (4) |
| GeoParquet | 127 (300) | 60 (48) | 69 (96) | 24 (4) |
| Delta Lake, runs table | 279 (196) | 224 (46) | 231 (91) | 203 (1) |
| Delta Lake, runs table, after `optimize` | 123 (64) | 82 (12) | 88 (23) | 74 (1) |
| Delta Lake, daily table | 7 (6) | n/a | n/a | n/a |
| Zarr | 438 (2,800) | 85 (552) | 69 (455) | 10 (12) |
| Icechunk | 850 (2,800) | 168 (552) | 165 (455) | 21 (12) |

Each Delta read opens the table cold, so its figures include replaying the transaction log. The Zarr and Icechunk reads fetch whole-run chunks, so their window queries read somewhat more data than the Parquet ones.

## Which tool for the job

| Tool | Verdict | Why |
|---|---|---|
| Parquet | Yes | The data is a table keyed by station, run and prediction time, and every reader filters on those columns. One run is one file of about 1.3 MB, so a write is a single atomic PUT through the S3 client we already use. |
| Delta Lake | Yes, for the tables jobs write to | It gives several jobs safe writes to one table, and compaction. The costs are real: a cold open took about 200 ms of log replay locally, the daily `MERGE` left 1.2 GB of dead files behind 11 MB of live data in 60 days, so `vacuum` and `optimize` are required chores, and it brings its own S3 client. |
| GeoParquet | No | No reader makes a spatial query. Repeating a station's point on every row added 1.3% in size and doubled write time for no read benefit. |
| Zarr | No | A (run, step, station) cube works, but GFS, NAM and the interpolated 20:00 UTC rows have irregular steps that become NaN padding. It is 20% smaller because it stores no key columns, but it needs 12 times the objects, and "latest run per day" has to be written by hand in Python. |
| Icechunk | No | It is Zarr plus versioning. Runs are already immutable, so "as of" is a filter on run time. It produced 28 times the objects of Parquet and depends on conditional writes, which are untested on ECS. |

Plain Parquet won the format benchmark on speed and simplicity, and would be enough if every table had one writer. We chose Delta Lake for `runs` and `by_time` anyway, because we want several writers per table and managed compaction. The costs in the table above are the price, and the design below says how each is handled.

## Where Zarr would be the right tool

Zarr lost here because station predictions are a keyed table. It is the right tool when the data is a dense, regular N-dimensional array and readers want small slices of it along more than one axis.

The conditions that make Zarr win:

- **Every cell on the grid has a value.** Zarr stores no keys: position in the array is the key. That is why it was 20% smaller in the benchmark, and why the irregular GFS and NAM steps hurt, since missing cells become NaN padding.
- **Reads slice across axes.** "One pixel through time" and "one time step across space" can both be cheap from the same store, because the chunk shape is a choice. Parquet can only be sorted one way, and a GeoTIFF per date is only cheap for the whole-map read.
- **The array is far larger than any one read.** Chunking pays off when a reader wants kilobytes out of gigabytes. A run file here is 1.3 MB, so there is nothing to skip.
- **Readers already think in arrays.** With `xarray`, selecting by coordinates is the query, and no "latest run per station" logic has to be rebuilt in Python.

Where that applies in this project:

| Data | Fit | Why |
|---|---|---|
| SFMS rasters as a time series (FFMC, DC or HFI at a point over a season) | Strong | It is a dense (time, y, x) cube. A six-month point series opens about 180 GeoTIFFs today; with weekly time chunks it would read about 27 chunks. |
| Hourly FFMC | Strongest | The same shape with 24 times the time steps: about 4,400 rasters for six months today. |
| Gridded model output, if we ever keep it | Strong | It is a dense (run, step, y, x) cube per model. It would allow forecasts at any location and backfilling a new station, which station-only storage cannot do. |
| Station predictions | Weak | Sparse, irregular steps, small, and every query is a key filter. |
| Whole-raster downloads | Weak | A chunk layout tuned for time series scatters one date across every chunk. Cloud-optimized GeoTIFFs stay better here. |

The SFMS read counts are calculated from the grid dimensions and a chunk layout, not measured.

Costs that come with Zarr:

- **Object count.** Zarr writes one object per chunk per variable. It produced 12 times the objects of Parquet in the benchmark, and on object storage, latency follows request count.
- **Appends rewrite chunks.** Adding a date rewrites every chunk that covers it, so longer time chunks mean cheaper reads but costlier writes.
- **No transactions.** A reader can see a half-written append. Icechunk exists to fix that and adds versioning, which is where it earns its place: asking what a pixel's series looked like as of a past date. Whether Icechunk works against ECS is untested.

### Could we change how we store the data so Zarr fits?

There are two ways. Only the second gives Zarr a real advantage.

| | Reshape the station data | Store the model grids |
|---|---|---|
| What changes | Stack the variables into one (run, step, station, variable) array per model, and move the interpolated 20:00 UTC rows into their own (day, station, variable) array. | Keep each model's grid as a (run, step, y, x) cube instead of sampling it at stations and discarding it. |
| What it fixes | One object per run instead of twelve, and no NaN padding in the main cube. GFS and NAM would still need an index axis, because they only keep the hours around noon. | The data becomes a dense cube far larger than any one read, which is the case Zarr is built for. |
| What it gains over Parquet | Nothing. Every read is still a key filter, a run is still 1.3 MB, and atomic appends still need Icechunk. | Station predictions become a point read. A new station can be backfilled, forecasts are available at any location, and bias adjustment can be recomputed from raw history. SFMS already consumes grids (`model_run_for_sfms`), so one store could feed both. |
| Size | Expected to be close to Parquet. Not measured. | Roughly 475 GB a year before compression for a BC-only crop of HRDPS alone, against about 9 GB a year for all six models' station data. This is an order-of-magnitude estimate; the real grid dimensions have not been checked. |
| Verdict | Not worth doing. | The version worth doing, but a separate and much larger project that needs sizing first. |

Bias-adjusted values and the MoreCast daily rows are derived per-station tables, so a small tabular output would remain in either case.

## Versioning

Choosing Parquet over Icechunk gives up less versioning than it appears to, because the history that matters for this data is in the layout.

| Question | Plain Parquet | Icechunk | Delta Lake |
|---|---|---|---|
| What did a given run predict? | Yes. Each run is its own immutable file. | Yes | Yes |
| What was the latest prediction as of a past time? | Yes, by filtering on `run_ts`. The model files in `by_time` can be rebuilt the same way. | Yes, from a snapshot | Yes, within the `vacuum` retention window |
| What had actually been ingested by a past time? | Partly. `by_time` carries `ingested_at`. A `runs` file does not, so a run that arrived late looks as if it was always there. | Yes | Yes, within the retention window |
| What did a run look like before it was reprocessed? | No. The retry overwrites the same key. | Yes | Yes, within the retention window |
| Can the whole dataset be pinned, tagged or rolled back as one unit? | No | Yes | Partly: per table, by version number |

The gaps can be closed in Parquet without a new tool:

- **Add an `ingested_at` column.** This answers the arrival-time question. `by_time` has one; `runs` would need it added.
- **Never overwrite a run.** Put a content hash or processing time in the key and have readers take the newest. This keeps reprocessing history, at the cost of readers no longer being able to compute a key without listing or a small index.
- **Turn on bucket versioning.** Whether our ECS bucket supports it has not been checked.

We do need reprocessing history. With `runs` and `by_time` on Delta Lake, time travel covers the recent past, up to the `vacuum` retention window. For a permanent record, `runs` is append-only and each version of a run carries its own `ingested_at`. See [Reprocessing history](#reprocessing-history).

Icechunk's versioning matters more for the SFMS rasters. A chunk there is rewritten in place as new dates are added, so without snapshots the earlier values are gone.

## Indexing

None of these tools has an index in the Postgres sense. There is no B-tree and no secondary index that can be added after the fact. Each one offers a way to skip data instead, and it only works along the dimensions chosen when the data is laid out.

| Tool | What stands in for an index | What it can't do |
|---|---|---|
| Parquet | Min/max statistics per column in each file's footer, plus optional bloom filters. Partition paths (`model=…/run_date=…`) prune whole files. | Skip anything on a column the data isn't sorted or partitioned by. |
| Delta Lake | The same Parquet statistics, copied into the transaction log, so files are pruned without opening them. `optimize` with Z-ordering clusters files on several columns at once. | It prunes files, not rows. There is still no row-level or secondary index. |
| Zarr | Position is the index. A chunk's key is computed from its coordinates, so a read by (run, step, station) goes straight to the chunk. | Search by value: "where was temperature above 30" is a full scan. A lookup by label, such as a station code or a timestamp, needs the coordinate arrays loaded first. |
| Icechunk | Zarr's positional addressing, plus manifests that map each chunk to its object. | The manifest indexes chunks, not values. It adds nothing for lookups. |

What this means for `runs` in the design below:

- **The partition is the index.** `runs` is partitioned by model and run date, so a reader goes straight to the files it needs. That covers every current reader of model runs.
- **Within a file, indexing is moot.** A run is 1.3 MB sorted by station, so reading the whole file costs about the same as skipping within it.
- **We lose the `station_code` index across time.** "One station over two years" would open every run file in the range, about 7,300 a year across the six models. Climatology needs exactly that read.

The fix is the same in every one of these formats: a second copy laid out for the read. In these formats, layout takes the place of an index. The `by_station` layout below is that second copy.

Zarr is a partial exception. With a station axis, one station across all runs is a cheap slice if the chunks are shaped for it, but chunks shaped that way make each new run rewrite existing chunks.

## Use cases

The indexing section says layout takes the place of an index, so the layouts have to follow from the reads we need to support. There are four.

| Use case | Lookup key | Read shape | Data |
|---|---|---|---|
| MoreCast | Date range and source, across many stations | Wide and shallow: all stations, a few days, the newest value per day | Observations, forecasts and models, daily |
| Climatology, one station | Station, across all years | Narrow and deep | Observations, forecasts and models, daily and hourly, weather variables only for now |
| Climatology, a group of stations | Stations and a time-of-year window, across all years | A band through every year | The same |
| Climatology at a chosen lead | One station or a group, filtered by how far ahead each prediction was made | Either shape, with several predictions per time | Models, every run |
| Model run detail (`/weather_models` routes, training, fire watch) | Model and run | One run or a few weeks of runs, every prediction time | Models, every run |

Decisions behind this table:

- **MoreCast needs only the newest run per day.** Run is how the winning row is picked, not something MoreCast looks up.
- **Climatology history starts now.** There is no backfill, so the deep reads grow by a year per year.
- **Climatology needs both shapes**, one station and groups of stations.
- **Lead has to stay a free choice.** We want to experiment with which prediction counts as the historical one, so no single lead can be baked in. See [Lead time](#lead-time).

The first three use cases read the same logical table: one value per station, time and source, where the source is `OBSERVED`, `FORECAST` or a model. This is the shape MoreCast already uses in `WeatherIndeterminate`. For a model, the value at a given time is the one from the newest run that predicted it. Only the fourth use case needs every run.

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

### Station history benchmark

`backend/scripts/station_history_storage_benchmark.py` writes that table in three layouts and times the reads:

```bash
uv run backend/scripts/station_history_storage_benchmark.py --years 5 --stations 300
```

| Layout | Description |
|---|---|
| `by_time` | Parquet, one file per source per month, all stations inside, sorted by time then station. |
| `by_station` | Parquet, one file per station per year, all sources inside, sorted by source then time. |
| Zarr | One (time, station, variable) array per source, in chunks of about a month by 25 stations. |

The results are for 5 years and 300 stations: 52.6 million hourly rows and 4.4 million daily rows, stored as float32. The same caveats apply as for the first benchmark: local disk, random floats.

| Layout | Hourly | Daily | Objects |
|---|---|---|---|
| `by_time` | 2.57 GB | 204 MB | 900 |
| `by_station` | 2.66 GB | 207 MB | 3,000 |
| Zarr | 1.63 GB | 136 MB | 11,042 |

Reads, as median milliseconds with the number of objects read in brackets:

| Read | `by_time` | `by_station` | Zarr |
|---|---|---|---|
| One station, hourly, all sources, all 5 years | 246 (420) | 1.6 (5) | 91 (427) |
| One station, daily, all sources, all 5 years | 109 (480) | 1.0 (5) | 84 (488) |
| 25 stations, hourly, 1 to 14 July of every year | 22 (35) | 35 (125) | 32 (49) |
| MoreCast: all stations, daily, 5 days, all sources | 1.7 (8) | 49 (300) | 23 (96) |

What this shows:

- **Each Parquet layout is the best at its own read by a wide margin**, and the worst at the other's. The object counts are what matter on object storage: 5 against 420 for a station's history, and 8 against 300 for MoreCast.
- **Zarr is a single copy that is never the best and never the worst.** It is 36% smaller. This is the one place a station dataset has the dense, regular shape Zarr wants.
- **Zarr's chunk shape could be tuned towards either read, but not both.** It also has the costs already described: every append rewrites the current chunk for each station block, and a reader can see a half-written append without Icechunk.

The two Parquet layouts together are about 1.1 GB a year. Storing the table twice is cheaper than serving either read badly, so the design uses both.

### Lead benchmark

`backend/scripts/station_leads_storage_benchmark.py` tests whether reads at a chosen lead need two layouts, as the settled history does. It writes one year of every prediction at every lead in two Parquet layouts:

```bash
uv run backend/scripts/station_leads_storage_benchmark.py --stations 300
```

| Layout | Description |
|---|---|
| `leads_by_station` | One file per station per year, with one row group per model per month. |
| `leads_by_time` | One file per model per month, with one row group per station. |

A reader uses the statistics in each file's footer to fetch only the row groups it needs. On object storage each row group is one ranged GET.

To keep the run short it generates two models, HRDPS and GDPS: 39.2 million rows for 300 stations. Each layout is 2.08 GB, at 53 bytes per row.

| Read | `leads_by_station` | `leads_by_time` |
|---|---|---|
| One station, whole year, lead 18 to 30 hours | 1 file, 24 row groups, 6.9 MB, 3 ms | 24 files, 24 row groups, 6.9 MB, 51 ms |
| 25 scattered stations, 1 to 14 July, lead 18 to 30 hours | 25 files, 50 row groups, 14.6 MB, 18 ms | 2 files, 50 row groups, 14.6 MB, 11 ms |
| 25 scattered stations, 1 to 14 July, every lead | 25 files, 50 row groups, 14.6 MB, 17 ms | 2 files, 50 row groups, 14.6 MB, 10 ms |

What this shows:

- **Both layouts fetch exactly the same row groups and bytes.** Because the row groups are cut by station, model and month in each, the only difference is how many files hold them.
- **For one station, the station-keyed layout is far better**: one object, which can be fetched whole, against one file per model per month.
- **For a group, the two are close.** The cost is one ranged GET per station, model and month either way. Extrapolated to six models, the 25-station read is about 175 requests station-keyed (25 footers and 150 row groups) against about 156 time-keyed (6 footers and 150 row groups).
- **Either is much better than reading `runs`.** The same two-model group read from `runs` would open about 112 run files and fetch over 100 MB to use a fraction of it. That figure is calculated from the run cadence, not measured.

So a second, time-keyed copy with leads is not worth its 6 GB a year. One station-keyed copy with well-cut row groups serves both shapes. The settled history is different: its files are small enough to fetch whole, and MoreCast reads every station at once, so it keeps both layouts.

### Reads over 5, 10 and 30 years, for a screen

Climatology has to serve a screen someone waits on, for one station or a group, over 5, 10 or 30 years. History starts when this is built, so a 30-year read is decades away, but the layout has to hold up as the years accumulate.

The choice is between precomputing statistics and computing them on demand from raw history. Precomputing freezes the period, the statistic, the smoothing window and the grouping, which are the things we want to stay flexible. So the test is whether raw history can be made cheap enough to read that the API can compute on demand.

`backend/scripts/station_climatology_read_benchmark.py` tests that:

```bash
uv run backend/scripts/station_climatology_read_benchmark.py --years 30
```

It writes one history file per station holding every year, sorted by source then time, with one row group per source per year. One source's whole history is then a single contiguous byte range: one request for the footer and one for the data. It fetches the data and computes percentiles with `numpy` and `pandas`. The group is 25 stations.

| Read | 5 years | 10 years | 30 years |
|---|---|---|---|
| One station, daily, all sources, percentiles by day of year | 1 request, 0.8 MB, 0.07 s | 1 request, 1.6 MB, 0.09 s | 1 request, 4.7 MB, 0.18 s |
| Group, daily, one source, per-station and pooled percentiles by day of year | 50 requests, 1.5 MB, 0.3 s | 50 requests, 2.9 MB, 0.4 s | 50 requests, 8.7 MB, 1.0 s |
| One station, hourly, one source, percentiles by month and hour of day | 2 requests, 1.5 MB, 0.01 s | 2 requests, 3.0 MB, 0.01 s | 2 requests, 9.0 MB, 0.03 s |
| Group, hourly, one source, pooled percentiles by month and hour of day | 50 requests, 37 MB, 0.1 s | 50 requests, 75 MB, 0.2 s | 50 requests, 225 MB, 0.7 s |

The times are local read, decode and compute. They exclude the network, which on object storage will dominate.

What this shows:

- **Three of the four reads suit a screen at every horizon.** Request counts do not grow with the years, the data fetched stays under 10 MB, and the statistics take a second or less to compute.
- **Hourly data for a group is the exception.** It fetches 75 MB at 10 years and 225 MB at 30. The computation is fast; the download is the problem.
- **No statistics table is needed for the other three.** The API computes whatever the screen asks for, and can cache results, since closed years never change.

For hourly group reads, the design adds one small derived table, `hourly_profile`: the count, mean, minimum and maximum of each variable per station, source, year, month and hour of day. That is 288 rows per station, source and year against 8,760 raw, so about a thirtieth of the size. Counts, means and extremes combine exactly across any years and any group. Percentiles do not, so a pooled hourly percentile for a group over decades stays an offline read. `hourly_profile` has not been benchmarked.

Reads at a chosen lead follow the same pattern once the rule is stored as its own source. Before that, they go through `leads`, which holds every lead and is about ten times larger: 100 MB for one station over 5 years and 600 MB over 30. Experimenting with leads on a screen is practical for one station over a few years, and a batch job beyond that.

## Design

### Layout

The flow from sources to readers is drawn in [station-predictions-storage-diagram.md](station-predictions-storage-diagram.md).

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
| `runs` | Delta Lake | `/weather_models` routes, training, fire watch | The six model jobs |
| `wf1` | Delta Lake | Rebuilding `by_time`; history of corrections | The WF1 jobs |
| `by_time` | Delta Lake | MoreCast | The model jobs and the WF1 jobs |
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
| `run_ts` | timestamp, UTC | Model run start. Also in the key, kept in the file so a file is self-describing. |
| `prediction_timestamp` | timestamp, UTC | |
| `tmp_tgl_2`, `rh_tgl_2`, `apcp_sfc_0`, `wdir_tgl_10`, `wind_tgl_10` | float32 | Raw model values. |
| `bias_adjusted_temperature`, `bias_adjusted_rh`, `bias_adjusted_wdir`, `bias_adjusted_wind_speed` | float32 | |
| `delta_precip`, `precip_24h`, `bias_adjusted_precip_24h` | float32 | |
| `ingested_at` | timestamp, UTC | When this version of the run was written. A reprocessed run appears again with a later value. |
| `is_interpolated` | bool | New. Marks the 20:00 UTC rows the job interpolates for three-hourly models. |

Rows are sorted by `station_code`, then `prediction_timestamp`. Compression is zstd.

The surrogate `id`, `create_date` and `update_date` columns are not carried over. A row is identified by model, run, station, prediction time and `ingested_at`.

Each run arrives as one small file. `optimize` merges a closed day's runs into one file per model, which in the format benchmark cut the files read by about four times.

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

One file per station, holding the count, mean, minimum and maximum of each weather variable per source, year, month and hour of day. The nightly job derives it from the hourly `by_station` files. It exists so that a screen can show hourly climatology for a group of stations without downloading every hourly value. See [Reads over 5, 10 and 30 years, for a screen](#reads-over-5-10-and-30-years-for-a-screen).

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

This is the one dataset read with ranged GETs rather than whole files. The lead benchmark above is why there is no time-keyed copy.

The nightly job that writes `by_station` writes this too, from `runs`, rebuilding the current year's file each night.

This dataset exists for experimenting. Once a rule is settled, the cheaper form is to store that rule's result as another source in `by_time` and `by_station`, such as `HRDPS_DAY1`. Reads of a settled rule are then small whole-file reads, and `leads` can be dropped.

### Writes

`runs` and `by_time` each have several writers: the six model jobs, and for `by_time` the WF1 jobs as well. Delta Lake makes that safe by committing through its transaction log, where two writers that collide have one retry.

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

An earlier version of this design copied replaced rows into separate `_superseded` tables to keep readers free of version logic. With reprocessing rare and only two direct readers of `runs`, that was more machinery than the problem needs.

### Reads

| Reader | Reads | Objects |
|---|---|---|
| MoreCast grid | `by_time`, daily, every source | About 1 file per source and month after compaction |
| Climatology, one station | `by_station` | 2 files, whole or one byte range each |
| Climatology, a group, daily | `by_station` | 2 files per station |
| Climatology, a group, hourly | `hourly_profile` | 1 per station |
| Climatology at a chosen lead | `leads`, with ranged GETs | Per station and year: 1 footer, plus 1 row group per model per month wanted |
| Fire watch | The latest run in `runs` | 1 file |
| `/weather_models` routes | `runs`, for run dates in the window | About 12 files per model after compaction |
| Bias-adjustment training | `runs` for the 19-day window and `by_time` for the observations, loaded once per job | About 23 files for RDPS after compaction |
| Ingest | Nothing: the whole run is in memory before it is written | 0 |

Reading a Delta table starts with its transaction log, which took about 200 ms cold in the benchmark. API pods should keep table state in memory and refresh it, not reopen the table on every request.

The Parquet files are fetched through the existing S3 client and filtered with `pyarrow`. Ranged GETs are used for single-source reads of `by_station` and for group reads of `leads`. The API computes climatology statistics on demand and can cache them.

### Retention

`by_time`, `by_station` and `hourly_profile` are kept indefinitely: they are the climatology record and cost about 1.1 GB a year together.

`runs` is the large dataset, at about 4.5 GB a year as float32. It is kept indefinitely too, as is `wf1`, which is small. It is the only complete record of what each run predicted, and `by_time`, `by_station` and `leads` are all rebuilt from it.

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

## What is and isn't verified

**Checked:**

- The tables, queries and readers described above, read on `main` as of 2026-11-12.
- The figures from the four benchmarks, each from one local run with `deltalake` 1.6.6, `icechunk` 2.3.1, `zarr` 3.4.2 and `pyarrow` 26.0.1.

**Not checked:**

- **Conditional PUTs on ECS.** Several writers per Delta table depend on ECS enforcing `If-None-Match` on PUT. No Dell documentation was found that settles it. The check is to have two processes commit to one table on ECS at the same moment and confirm that one retries and neither commit is lost. The `deltalake` 1.6.6 library was confirmed to contain the conditional PUT, copy-if-not-exists, DynamoDB lock and unsafe-rename options; its documentation pages for them could not be loaded.
- **Which mode the earlier Delta Lake trial used.** If it ran with the unsafe-rename option, it showed only that a single writer works.
- **Delta Lake for `by_time` at full size.** The format benchmark ran `MERGE` on a small daily table only. `by_time` with hourly data and the maintenance job have not been benchmarked.
- **One Delta table for both history layouts.** Delta's Z-ordering might let a single table serve MoreCast and climatology. It was not tried; the design keeps the measured two-layout approach.
- **Latency against ECS.** No read or write has been timed against our object store. The `/weather_models` path, at about 50 GETs per request, is the one to time first.
- **Station count.** 300 is an assumption. Size and row counts scale linearly with it.
- **Real sizes.** At 300 stations, `runs` is about 113 million rows a year. The benchmark measured 82 bytes per row as float64, about 9 GB; the 4.5 GB float32 figure is half of that, not measured. Station history is about 11 million rows a year, or about 0.55 GB per layout as float32. Real values should compress better than random floats.
- **`hourly_profile`.** It has not been benchmarked. Its size is estimated from its row count.
- **Network time for the climatology reads.** The climatology benchmark measured local read and compute only.
- **The nightly rebuild.** Rebuilding every station's current-year file each night, and merging a year into the history files, have not been timed.
- **How observations arrive.** The WF1 job that writes `hourly_actuals` was not read in detail, including how far back each fetch reaches. That decides how many rows each fetch has to compare before appending to `wf1`.
- **The bookkeeping replacement.** The current lifecycle was read from the call sites in the model jobs, not traced end to end. Listing a `staging` prefix, reading its footers and checking `runs` for a run have not been timed against ECS. The staging file counts per run are calculated from the forecast-hour ranges, assuming one GRIB per variable per hour.
- **Hourly forecasts.** They do not exist in the code today. Where they will come from, and whether MoreCast will record their history as it does for daily forecasts, is not known.
- **Dependencies.** Neither `pyarrow` nor `deltalake` is a declared dependency of any backend package, and whether the production images install them cleanly has not been checked.
- **Other layouts.** Each format was tested with one layout. Different Zarr chunking or Delta partitioning would move the numbers, though not the object-count gap or the log-replay cost.

## Plan

1. Test two concurrent writers to one Delta table on ECS. The result decides between shared tables and one table per writer.
2. Have one model (GDPS) write to `runs` and `by_time` alongside its Postgres writes, with the maintenance job running.
3. Compare every read query's results between the two, and time each read against ECS.
4. Move the model readers over one at a time: `/weather_models` routes, fire watch, training, then MoreCast's model values.
5. Replace `model_run_predictions` with `staging` for that model, and switch its bookkeeping from the Postgres tables to `staging` and `runs`.
6. Extend to the other models, stop writing the two prediction tables and the three bookkeeping tables, and retire them along with the `pgslice` job.
7. Have the WF1 jobs write `OBSERVED` and `FORECAST` to `wf1` and `by_time` alongside Postgres, then move their readers and retire `hourly_actuals` and `noon_forecasts`.
8. Add the nightly job that writes `by_station`, `hourly_profile` and `leads`, and build the climatology reads on them.

Steps 7 and 8 do not depend on steps 4 to 6. History only accumulates once `by_time` is being written, so steps 2 and 7 are worth starting early even if readers move later.

Postgres remains the fallback for each table until its readers have moved.

## Decisions made

| Question | Decision |
|---|---|
| Plain Parquet or Delta Lake? | Delta Lake for `runs` and `by_time`, for several writers and compaction. Plain Parquet for the derived files. |
| Do forecasts need leads? | Yes. WF1 keeps only the latest forecaster's forecast, so forecast history comes from MoreCast's saved submissions and goes into `leads`. |
| float32 or float64? | float32 throughout. |
| What about `id` and `update_date`? | Drop them. They are database row fields returned by one route with no caller found. |
| Do we need reprocessing history? | Yes. `runs` and `wf1` are append-only, and each version carries its own `ingested_at`. |
| Will forecasts be hourly? | Yes. `FORECAST` has hourly rows once hourly forecasts exist. |
| Should we store the model grids? | Only if we have to. Not in this design. |
| Does run bookkeeping stay in Postgres? | No. It is read from `staging` and `runs`. |

## Open questions

1. **Does ECS enforce conditional PUTs?** Everything about shared Delta tables depends on it. This is step 1 of the plan.
2. **Which lead rules are worth keeping?** Undecided. Lead stays a free choice while we experiment with `leads`. Rules that prove useful should become their own sources in `by_time` and `by_station`.
3. **What does the climatology screen show?** Undecided. The design assumes percentiles by day of year for daily data, and statistics by month and hour of day for hourly data. A screen that needs pooled hourly percentiles for a group over decades is the one case this does not serve.
4. **Where will hourly forecasts come from, and will their history be recorded?**
5. **How long is the `vacuum` retention window?** It sets how far back Delta time travel reaches. 30 days is the proposed start.
