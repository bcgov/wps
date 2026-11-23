# Weather data: storage and processing decisions

What we decided for station weather, model grids and the Station Weather API, and why. The detail and the measurements are in the documents each section names.

As of 2026-11-23. The station tables and the Station Weather API run in a dev deployment. The model grid job is written and tested but has not been checked in a cluster. Production has not been backfilled.

| Data | Where | Detail |
|---|---|---|
| Station observations, forecasts and model values | Delta Lake on object storage (ECS) | [station-weather-storage.md](station-weather-storage.md), [evaluation](station-weather-storage-evaluation.md) |
| Model grids over BC | Zarr on Icechunk, on the same object storage | [model-grid-storage-spike.md](model-grid-storage-spike.md) |
| Forecasts entered in MoreCast | Postgres (`morecast_forecast`) | It is transactional application data |

## Station data

| Decision | Why |
|---|---|
| Station weather moves from Postgres to object storage | Postgres needed monthly partitions, `pg_dump` archives that could not be queried, and pruning |
| Delta Lake | Several jobs write the same tables, and the tables need compaction. It was not chosen on speed: plain Parquet was faster |
| Not Zarr, Icechunk or GeoParquet for station data | Zarr and Icechunk needed 12 and 28 times the objects; GeoParquet added size and write time for no faster reads |
| `runs` and `wf1` are append-only and kept forever | They are the source record, and everything else is rebuilt from them. Reprocessing appends a version with a later `ingested_at`, and readers take the newest |
| `by_time`: the newest value per station, time, resolution and source | MoreCast reads a few days across every station. It is derived, so it can be rebuilt |
| `by_station`: the same rows partitioned by resolution, station and year | Climatology and the Station Weather API read a few stations across years. One sort order cannot serve both reads |
| A nightly job replaces `by_station`'s current year; earlier years only when asked | They rarely change. A backfill must be followed by a rebuild with `--from-year` |
| `staging`: one table per model, with a marker row for each processed file | A run downloads over several job runs. Values and marker are one commit, so a file is either done or not |
| Publish in order: append to `runs`, merge into `by_time`, delete from `staging` | There are no transactions across tables. Every step is safe to repeat, and deleting last makes a crash safe |
| `stations` is a copy of WF1's station list | The public API can list stations without calling WF1 |
| Values are float32, except in `staging` (float64) | Half the size, and more precision than the sources have. `staging` feeds calculations |
| Invalid and missing values are null | Replaces a validity flag per variable |
| FWI indices are stored as published, not calculated | WF1 and the data mart already have them |
| Commits use conditional PUT (`conditional_put: etag`) | Makes several writers per table safe. Four concurrent writers lost no commits on ECS |
| Observations back to 1987 come from the BCWS data mart | It never replaces a value the hourly actuals job fetched from WF1 |
| Legacy Postgres tables stay until production is backfilled and checked | A later migration drops them |

### Upkeep and memory

| Decision | Why |
|---|---|
| A nightly job compacts, checkpoints and vacuums every table, with 30 days' retention | Small files, long logs and unreferenced files otherwise build up |
| Tables checkpoint every 10 commits | Opening a table replays its log. 73 commits took a `by_station` open from 150 to 760 MiB |
| One compaction task at a time | The default is one per CPU, and a pod sees its node's 48. The maintenance job ran out of memory |
| Maintenance opens one table at a time, with a 2 GiB limit | An open table holds its log state. Compacting `wf1` after the backfill peaked at 1.7 GiB |
| OpenShift builds use `SkipLayers` | Layers kept several copies of the 1.1 GB venv on disk, and builds were evicted at the 15 GiB local storage limit |

## Model grids

| Decision | Why |
|---|---|
| Keep the grids as well as the station values | A station added later can be given history, forecasts can be read anywhere in BC, and adjustments can be recomputed |
| Store the GRIB file's own integers and each field's scales, with pcodec | Every variable must stay accurate. This keeps exactly what was published and is 25 to 50 % smaller than float32 |
| Not Open-Meteo's scaled int16 | It would be about 29 GB a year, not 52, but it rounds the published values a second time, to [coarser steps](model-grid-storage-spike.md#accuracy-and-rounding) |
| Crop to BC, and do not keep the GRIB files | About 52 GB a year for all five models, against about 1 TB |
| `recent`: every run for 48 hours. `history`: one run a day, kept | Runs overlap heavily; keeping every run would be about 200 GB a year. 48 hours, not a calendar day, leaves no gap after midnight |
| `history` keeps 18Z for HRDPS, RDPS and GFS, and 12Z for GDPS and ECMWF | Each model's last full-length run of the day |
| A group per run, written in one commit | A reader never sees part of a run, and an old run is dropped by deleting its group |
| Chunks are 64 x 64 cells with every hour; a variable's run is one object | A point forecast is one chunk per variable. Maps are slower |
| Reach ECS through the `object_store` crate, not the AWS SDK | ECS requires `Content-MD5` on bulk deletes. Through the SDK, garbage collection deletes nothing. `object_store` was as fast |
| A separate hourly job per model | A failure cannot hold up the station data. It downloads the files again for itself |
| A run is stored only once the datamart has all of it | Nothing is downloaded for an incomplete run, and nothing is committed if a file vanishes |
| One variable at a time, cropped before conversion, files deleted once read | Peak memory 508 MiB for HRDPS, down from 826 MiB. The limit is 1 GiB |
| One download feeds both stores | The daily run is needed by both |
| Nightly maintenance expires snapshots after a day, then garbage collects | Reclaims deleted runs' space. Grids cannot be read as they were further back than that |
| HRDPS and RDPS first | Both come from the MSC datamart, and they are about 47 of the 52 GB a year |

## Station Weather API

| Decision | Why |
|---|---|
| Its own process, from the main API's image | The other gateway APIs work this way. A smaller image would first need the code moved to its own package |
| Public only through the APS gateway, with an API key | The gateway checks the key and limits requests to 60 a minute per consumer |
| One worker per pod, two pods, 2 GiB limit | Each worker holds its own open tables, about 1 GiB. Requests are async, so one worker serves several |
| `by_station` for dates before the last 2 UTC days, `by_time` after | `by_station` is rebuilt nightly, and `by_time` is written as data arrives |
| Resources by kind: `stations`, `observations`, `forecasts`, `models` | Each returns only the fields it has |
| Dates and station codes are query parameters | They narrow a collection. Dates are optional, and paging only moves `start` |
| Default dates: the last 7 days of observations, the next 10 of forecasts and models | A request needs only station codes |
| Long requests are paged, not refused | Whole days, about 50,000 rows a page, with `next` in the body and a `Link` header |
| `next` is a relative URL that names `end` | The app sees only its internal host name, and a default `end` would otherwise move |
| CSV through `Accept: text/csv` | The same URL serves both formats |
| Errors use FastAPI's shape, not RFC 9457 | FastAPI supports it and documents it. RFC 9457 would be our own code |
| No ETags or cache headers for now | Stale data was the worry. ETags built from table versions with `no-cache` would avoid it, if caching is needed |
| Stays in Python | Delta Lake's reader is already Rust, and holds most of the memory |

## Still open

- Read times for the grids inside the cluster. From a laptop, a point forecast took about 1 s and a map about 4.5 s.
- Endpoints that read the grids, and grid jobs for GDPS, GFS and ECMWF.
- Whether NOMADS keeps NOAA's original GFS scales. NAM is no longer on NOMADS.
- ECS quota and cost approval for the grids, and whether ECS will accept CRC checksums.
- Merges into `by_time` by two jobs at once, or during compaction: untested on ECS, and the jobs do not retry.
- `hourly_profile` and `leads`: designed, not built.
- The production backfill, and dropping the legacy Postgres tables after it.
