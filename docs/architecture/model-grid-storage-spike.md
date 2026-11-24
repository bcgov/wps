# Model grid storage spike: weather model grids in Zarr on Icechunk

Status: spike, run on 2026-11-19 on local disk for HRDPS, RDPS, GDPS, GFS and ECMWF, and against our object store (ECS) for HRDPS and RDPS. The design is now built for all five models in `wps_weather_data.grids` (see [As built](#as-built)). Read times from inside the cluster are not measured.

The decisions here and in the related documents are listed in [weather-data-decisions.md](weather-data-decisions.md).

## Summary

- Every model we ingest publishes integer-packed GRIB2, and storing those integers with each field's scales keeps exactly what the provider publishes. Compressed with pcodec, it is the smallest lossless form for every model, 25 to 50 % smaller than float32.
- Kept that way, with every hour of every run, BC crops of all five models come to about 200 GB a year. HRDPS is about 80 % of it (162 GB); RDPS is 27 GB and the other three under 6 GB each.
- Open-Meteo style scaled int16 is about half the size again for HRDPS, and 14 to 36 % smaller for the other models, but it rounds the published values a second time, to coarser steps, so it does not meet the requirement that every variable stays accurate. See [Accuracy and rounding](#accuracy-and-rounding).
- The runs overlap: a 49-hour HRDPS run covers the same hours as the next seven. The chosen [retention](#retention) keeps every run for about a day and one run per model per day after that, which is about 52 GB a year for all five models, every value exact.
- Icechunk works on ECS, garbage collection included, when it reaches ECS through the `object_store` crate (`icechunk.Storage.new_s3_object_store`). Through its default AWS SDK storage, garbage collection deletes nothing, because ECS rejects bulk deletes without `Content-MD5` and `object_store` is the client that still sends it. So `recent` can keep every run in one repository and reclaim old runs' space. Read times from inside the cluster are the main thing left to measure.
- Keeping the downloaded GRIB files instead would take about 1 TB a year under the same retention, about 20 times as much, because they cover each model's whole domain. [Cropped GRIB](#compared-with-keeping-the-grib-files) would be about Zarr's size but far slower for point reads.
- NAM is no longer published on NOMADS.

## Question

The model jobs keep only each run's values at weather stations (`runs`, `by_time`, `by_station`). Could we also keep every run's whole grid, cropped to BC, as Zarr in Icechunk, alongside the station data and with nothing removed? And if so, what would it cost in storage, and how fast are the reads?

Keeping the grids would let us backfill a station added later, give forecasts at any location (fires, fire zones), recompute bias adjustment and lead-time rules from the raw fields, and feed SFMS from the same store. The [storage evaluation](station-weather-storage-evaluation.md#could-we-change-how-we-store-the-data-so-zarr-fits) rated this "the version worth doing, but a separate and much larger project that needs sizing first", with a rough estimate of 475 GB a year for HRDPS before compression. This spike measures it.

## Setup

Scripts: [`backend/scripts/model_grid_icechunk_spike.py`](../../backend/scripts/model_grid_icechunk_spike.py) writes and measures the stores, for one model at a time (`--model`), and [`backend/scripts/grib_precision_check.py`](../../backend/scripts/grib_precision_check.py) reports the precision each GRIB field is packed at. Their dependencies (zarr 3.4.2, icechunk 2.3.1, numcodecs 0.17.1 with pcodec, eccodes 2.48.0, herbie-data 2026.10.0 for ECMWF) are declared in the scripts, not added to the project.

The setup and results below are HRDPS, which was measured first and in most detail. [The other models](#the-other-models) were run the same way.

- **Data.** HRDPS continental 2.5 km, the 2026-11-19 12Z run, forecast hours 0 to 48, downloaded from the MSC datamart. The same five variables the HRDPS job reads: 2 m temperature, 2 m relative humidity, 10 m wind speed and direction, and accumulated precipitation.
- **Crop.** HRDPS is a 2540 x 1290 rotated lat-lon grid. The rows and columns covering BC (latitude 48.2 to 60.1, longitude -139.2 to -114.0) are 622 x 680 = 422,960 cells. Uncompressed as float32, a run is 415 MB.
- **Layout.** One Zarr array per variable with dimensions (run, hour, y, x). Each run is appended along `run` in one Icechunk commit. Shards hold a whole run of one variable.
- **Variants.** The same run is written six ways:

| Variant | Values | Compression | Chunk |
|---|---|---|---|
| `f32-zstd-point` | float32, lossless | zstd level 3 | every hour of a 64 x 64 tile |
| `f32-pcodec-point` | float32, lossless | pcodec level 8 | every hour of a 64 x 64 tile |
| `i16-zstd-point` | scaled int16 | delta along x, then zstd | every hour of a 64 x 64 tile |
| `i16-pcodec-point` | scaled int16 | pcodec level 8 | every hour of a 64 x 64 tile |
| `i16-pcodec-map` | scaled int16 | pcodec level 8 | one hour of the whole crop |
| `grib-pcodec-point` | the GRIB file's own integers, lossless | pcodec level 8 | every hour of a 64 x 64 tile |

- **GRIB integers.** A GRIB2 field is stored as integers X, with value = (R + X x 2^E) / 10^D, where R is the field's reference value, E its binary scale and D its decimal scale. The `grib` variant stores X as int32 and each field's R, E and D in small (run, hour) arrays beside it. X is recovered from eccodes' decoded values; every value sits on the field's grid of steps to within float64 rounding (at most 2 x 10^-9 of a step) and decodes to the same float32, so it is exactly what MSC stored.

- **Scaled int16.** Each value is stored as `round((value - offset) * scale)` (Zarr's `FixedScaleOffset` filter). This is how Open-Meteo stores its data ([below](#open-meteos-quantization)). The scales follow Open-Meteo's, except relative humidity, which matches the station data's 0.1 %:

| Variable | GRIB units | Offset | Scale | Kept to |
|---|---|---|---|---|
| Temperature | K | 273.15 | 20 | 0.05 °C |
| Relative humidity | % | 0 | 10 | 0.1 % |
| Wind speed | m/s | 0 | 10 | 0.1 m/s |
| Wind direction | degrees | 0 | 1 | 1° |
| Precipitation | mm since the run started | 0 | 10 | 0.1 mm |

- **Reads**, from a freshly opened repository: a point forecast (all 49 hours of all five variables at one grid cell, at 20 random cells) and a map (one hour of temperature over the whole crop, at three hours). Each read value is compared with the source value.

## Results

On local disk, on a laptop:

| Variant | MB per run | Compression | GB a year | Objects | Write | Point read p50 / p90 | Map read | Largest error |
|---|---|---|---|---|---|---|---|---|
| `f32-zstd-point` | 193.7 | 2.1x | 283 | 28 | 0.3 s | 10 / 11 ms | 47 ms | none |
| `f32-pcodec-point` | 162.8 | 2.5x | 238 | 28 | 0.3 s | 9 / 9 ms | 32 ms | none |
| `i16-zstd-point` | 66.9 | 6.2x | 98 | 28 | 0.3 s | 12 / 15 ms | 41 ms | half a step |
| `i16-pcodec-point` | 55.8 | 7.4x | 82 | 28 | 0.3 s | 9 / 10 ms | 31 ms | half a step |
| `i16-pcodec-map` | 58.5 | 7.1x | 85 | 28 | 0.2 s | 104 / 115 ms | 3 ms | half a step |
| `grib-pcodec-point` | 110.7 | 3.7x | 162 | 39 | 0.3 s | 16 / 18 ms | 30 ms | none |

The `grib` row is the 18Z run of the same day; the others are the 12Z run. On the 18Z run, `f32-pcodec-point` and `i16-pcodec-point` measured within 0.5 MB of their 12Z sizes. A point read in the `grib` variant also reads the hour's scales, which is why it is slower.

What MSC packs each field at, from `grib_precision_check.py` on the 18Z run's hour 24, against the `i16` variants:

| Variable | Bits per value | MSC's step | `i16` step | `grib` MB per run (pcodec) |
|---|---|---|---|---|
| Temperature | 16 | 0.001 K | 0.05 | 25.4 |
| Relative humidity | 12 | 0.025 % | 0.1 | 21.0 |
| Wind speed | 12 | 0.01 m/s | 0.1 | 16.1 |
| Wind direction | 12 | 0.1° | 1 | 20.1 |
| Precipitation | 24 | 0.00001 mm | 0.1 | 23.0 |

- **GB a year** is HRDPS alone, at four runs a day.
- **Objects** is for one run, including Icechunk's own metadata.
- **Write** is encoding and committing a run already in memory. Downloading the run's 244 GRIB files (662 MB, for the whole continental grid) took 99 s. Reading them took most of the rest of the 2 minute 40 second total.
- **Half a step** is exactly half the stored precision, as rounding gives: temperature 0.025, relative humidity 0.049, wind speed 0.05, wind direction 0.5, precipitation 0.05.
- **Peak memory** was 1.17 GiB, because the script holds all five variables of a run at once.

Only sizes, compression and errors carry over to ECS. Read and write times there depend on request latency: see [Reads on ECS](#reads-on-ecs).

## Findings

- **Storing the GRIB integers is the most compact lossless option.** It keeps exactly what MSC publishes in 110.7 MB a run, 3.7x, which is 162 GB a year for HRDPS at four runs a day with every hour kept. Lossless float32 needs 163 MB (2.5x).
- **The scaled int16 variants are not accurate against the source.** They are 7.4x (82 GB a year), but MSC packs every field more finely than the scales chosen here (temperature to 0.001 K against 0.05). Their error, half a step, is far larger than anything in the source. Open-Meteo's scales were chosen for a forecast API, not to keep the source exactly.
- **No one variable dominates the lossless size.** Temperature, stored to 0.001 K, is the largest at 25 MB a run, and the others are 16 to 23 MB. Keeping every variable exact leaves which runs and hours are kept as the remaining lever: each 49-hour run overlaps the next seven, so keeping only the first six hours of each run would store each hour once, roughly an eighth of the size. That has not been measured.
- **pcodec beats zstd** by 15 to 20 % for float32 and for int16, with no slower reads.
- **The point layout is the right default.** A point forecast is one chunk per variable. A map is about 110 chunks per variable, which was still fast here. The map layout makes maps ten times faster and point reads ten times slower. Which matters more on ECS, where each chunk is a ranged request, is measured from a laptop in [Reads on ECS](#reads-on-ecs) but not from inside the cluster.
- **Writing is cheap.** A run encodes and commits in under a second once it is in memory. The cost of a job is the download, which the HRDPS job already does.
- **The rough estimate held.** The evaluation's 475 GB a year for HRDPS before compression compares with 605 GB measured uncompressed (415 MB x 4 runs x 365 days).

## Accuracy and rounding

There are two separate roundings, and the stores have only the first:

1. **The provider's, before publishing.** When MSC writes a GRIB file it rounds its model output to a step, such as 0.001 K, and packs it as integers with a scale. That precision is gone before we download the file. The `grib` variant keeps those integers and scales and adds no rounding of its own. So "lossless" here means the same as the published file, not the same as the model's internal values. The scales can change from hour to hour, so they are stored for every hour. GFS and ECMWF are kept the same way, with their own steps.
2. **Open-Meteo's, after downloading.** It rounds the published values again, to a coarser step chosen for each variable, and the finer value cannot be recovered. This is the loss the `grib` variant avoids.

For HRDPS:

| Variable | MSC's published step (what is stored) | Open-Meteo style step (rejected) | Largest error from the second rounding |
|---|---|---|---|
| Temperature | 0.001 K | 0.05 K | 0.025 K |
| Relative humidity | 0.025 % | 0.1 % | 0.049 % |
| Wind speed | 0.01 m/s | 0.1 m/s | 0.05 m/s |
| Wind direction | 0.1° | 1° | 0.5° |
| Precipitation, since the run started | 0.00001 mm | 0.1 mm | 0.05 mm |

- **The published steps** are from hour 24 of the 2026-11-19 18Z run and can differ at other hours. The errors were measured on the 12Z run against the published values. The `grib` variant's error against them is none.
- **The rejected steps are Open-Meteo's**, except relative humidity. Open-Meteo rounds that to 1 %, an error of up to 0.5 %, which was not measured.
- **Precipitation** is a total since the run started. With that rounding, a total under 0.05 mm becomes zero, and an hourly amount, the difference between two totals, can be off by up to 0.1 mm. This follows from the step and was not measured.
- **What it would save.** Scaled from the measured runs, the daily `history` of all five models would be about 29 GB a year instead of 52. Per run, the saving is 49 % for HRDPS, 36 % for RDPS, 24 % for GDPS, 26 % for GFS and 14 % for ECMWF.

## The other models

`grib_precision_check.py` was run on hour 24 of each model's 2026-11-19 12Z run, fetched the way its job fetches it. Every field is integer-packed GRIB2, and every field's integers were recovered exactly (at most 2 x 10^-9 of a step from a whole X). So the `grib` variant works unchanged for all of them.

| Model | Source | Packing | Temperature step | Relative humidity step | Wind step | Precipitation step |
|---|---|---|---|---|---|---|
| HRDPS | MSC datamart | JPEG 2000 | 0.001 K | 0.025 % | 0.01 m/s, 0.1° | 0.00001 mm |
| RDPS | MSC datamart | JPEG 2000 | 0.025 K | 0.025 % | 0.01 m/s, 0.1° | 0.000025 mm |
| GDPS | MSC datamart | JPEG 2000 | 0.025 K | 0.25 % | 0.05 m/s, 0.5° | 0.000025 mm |
| GFS | NOMADS filter, cropped to BC | simple | 0.01 K | 0.1 % | 0.01 m/s (u and v) | 0.0625 mm |
| ECMWF IFS 0.1° | open data, through herbie | CCSDS | 0.25 K | none: dew point, 0.25 K | 0.03125 m/s (u and v) | 0.00024 m |

- **NAM is gone.** NOMADS answers its NAM directory with "The model is no longer available on nomads.ncep.noaa.gov", and the NAM cron jobs are suspended in dev.
- **Precision differs by model.** Lossless means keeping what each provider publishes: ECMWF's open data has temperature in 0.25 K steps and GFS has precipitation in 0.0625 mm steps. A field's step can change by hour, so R, E and D are stored per hour.
- **What differs is the layout, not the encoding.** RDPS and HRDPS are rotated lat-lon and GDPS, GFS and ECMWF regular lat-lon, so each model needs its own store, crop and coordinates. GFS and ECMWF publish wind as u and v and ECMWF publishes dew point, not relative humidity: to stay lossless, store what is published and derive speed, direction and humidity when reading, as the station jobs do. GDPS is 3-hourly to 240 hours, RDPS hourly to 84 and GFS 3-hourly; the GFS job fetches only the hours around noon, so a grid store would fetch more than it does.
- **NOMADS repacks, and is almost but not exactly NOAA's file.** Its filter crops and re-encodes GFS with simple packing. Checked on 2026-11-23 against NOAA's full files on AWS (`noaa-gfs-bdp-pds`), for the 12Z run's hours 3, 9, 24, 27, 120, 123 and 240: the steps are the same for all 41 fields, and 37 fields are float32-equal over BC. The other 4 (three of temperature, one of v wind) differ by at most 2 x 10^-5 K and 6 x 10^-7 m/s, far under a step, which is what re-rounding the reference value to float32 would give. NOAA's own files can be read a field at a time by byte range, from the `.idx` file beside each.
- **GFS precipitation** has a field since the run started at every hour checked from 3 on, with a bucket (3 or 6 hours) beside it at most hours. Hour 0 has none.

### Sizes

`model_grid_icechunk_spike.py --model {hrdps,rdps,gdps,gfs,ecmwf}` fetches each model the way its job does and stores the variables as the provider publishes them. Each model's 2026-11-19 run (HRDPS 18Z, the others 12Z) was written on local disk:

| Model | Hours kept | BC crop (cells) | GRIB integers MB per run | Lossless float32 MB per run | int16 MB per run | Runs a day | GRIB integers GB a year |
|---|---|---|---|---|---|---|---|
| HRDPS | 0 to 48, hourly | 622 x 680 | 110.7 | 162.6 | 56.1 | 4 | 162 |
| RDPS | 0 to 84, hourly | 191 x 205 | 18.7 | 26.4 | 11.9 | 4 | 27 |
| GDPS | 0 to 240, 3-hourly | 79 x 168 | 5.4 | 8.9 | 4.1 | 2 | 3.9 |
| GFS | 0 to 240, 3-hourly | 48 x 101 | 2.3 | 4.4 | 1.7 | 4 | 3.3 |
| ECMWF | 0 to 240, 3- then 6-hourly | 119 x 252 | 5.0 | 6.6 | 4.3 | 4 | 5.4 |

- **ECMWF's year** counts its 06 and 18 UTC runs as the 31 hours to 90 they have, against 65 hours for 00 and 12 UTC. The script's own figure, 7.3 GB, counts all four runs as full.
- **All five models come to about 200 GB a year** lossless with every hour of every run kept, and HRDPS is about 80 % of it.
- **The GRIB integers are the smallest lossless form for every model**: 25 to 50 % smaller than float32. ECMWF's float32 compresses unusually well (5.9x) because its open data is packed coarsely (0.25 K for temperature), which leaves few distinct values.
- **Point reads** were 16 to 18 ms and map reads 3 to 6 ms on local disk for every model's `grib` variant. The coarser grids are a single 64 x 64 tile wide or a few, so a map is one or a few chunks.
- **Writing** took 0.1 s a run. Downloading took most of the time, and for GDPS and ECMWF it is the whole global field (820 and 799 MB a run) to keep a small BC crop. Peak memory was under 710 MiB.

## Retention

Decided on 2026-11-19: every run for the current day, and historically one fixed-hour run per model per day. Each model has two stores:

- **`recent`: every run for the last 48 hours.** One Icechunk repository, with each run its own group (for example `/2026-11-19T12/`), written in one commit. The job adds each new run and deletes the groups of runs older than 48 hours; a scheduled job expires old snapshots and runs garbage collection, as `vacuum` does for the Delta tables. The repository must reach ECS through `object_store` (see [the cycle on ECS](#the-recent-cycle-on-ecs)): this whole cycle worked on ECS that way. Through Icechunk's default AWS SDK storage, garbage collection deletes nothing on ECS. A repository per run, deleted by prefix one object at a time, was the workaround considered before `object_store` was tried, and is no longer needed.
- **`history`: one run per day, kept.** Laid out as `recent` is, a group per run, so that one piece of code reads and writes both. (The spike appended along a `run` axis instead.) The job writes the chosen run to both stores from one download. Nothing is deleted from `history`.

The run kept each day is each model's last full-length run:

| Model | Run kept | Why |
|---|---|---|
| HRDPS, RDPS, GFS | 18Z | the last run of the day, full length |
| GDPS | 12Z | GDPS runs only at 00Z and 12Z |
| ECMWF | 12Z | its 18Z run goes to 90 hours, its 12Z run to 240 |

Using 12Z for every model would make the models comparable run for run, at the cost of HRDPS, RDPS and GFS's last update of the day. The storage is the same.

Sizes, as GRIB integers, scaled from the measured runs in [Sizes](#sizes):

| Model | `history`, GB a year | `recent`, about a day of runs |
|---|---|---|
| HRDPS | 40.4 | about 440 MB |
| RDPS | 6.8 | about 75 MB |
| GDPS | 2.0 | about 11 MB |
| GFS | 0.8 | about 9 MB |
| ECMWF | 1.8 | about 15 MB |
| All five | about 52, or about 30 keeping April to October only | about 0.55 GB, up to about twice that before garbage collection |

- **`history` needs little garbage collection.** Nothing is deleted from it, and adding a run adds a group without rewriting another run's arrays. The nightly maintenance job covers it as well as `recent`. A retention window (two years, say) would be the deletion `recent` already does, with a longer cutoff.
- **`recent` at 48 hours** is about twice the table's figures, which are for about a day: roughly 1.1 GB for all five models and 1.0 GB for HRDPS and RDPS, plus deleted runs that maintenance has not reclaimed yet.
- **The current day is the last 48 hours**, not a calendar day, so there is never a gap after midnight.

### The recent cycle on ECS

`model_grid_icechunk_spike.py --recent-cycle 4` adds one run as four runs, each a group of one repository, deletes the older two, expires snapshots and garbage collects, measuring the store after each step. With the 2026-11-19 12Z RDPS run as GRIB integers:

| Step | Local disk | ECS, AWS SDK storage (`s3_storage`) | ECS, `object_store` storage (`Storage.new_s3_object_store`) |
|---|---|---|---|
| Four runs added | 73.7 MB, 99 objects | 73.7 MB, 99 objects | 73.7 MB, 99 objects |
| Two deleted (commit) | 73.7 MB | 73.7 MB | 73.7 MB |
| Snapshots expired | 73.7 MB | 73.7 MB | 73.7 MB |
| Garbage collected | 36.8 MB, 58 objects | 73.7 MB: nothing deleted | 36.8 MB, 58 objects, no delete errors |
| Kept runs read back exactly | yes | yes | yes |

Through the AWS SDK storage, garbage collection failed on every batch: `DeleteObjects failed: status 400, code InvalidRequest, message Missing required header for this request: Content-MD5`. S3 requires a checksum on `DeleteObjects`; the AWS SDK inside Icechunk sends CRC32, and ECS accepts only `Content-MD5`. It is the same limit that rejects boto3's bulk delete. Configuration does not help: Icechunk's `checksum_algorithm` offers CRC32, CRC32C, CRC64-NVME, SHA-1 and SHA-256 but not MD5, and the checksum environment settings that fixed reads do not apply to a call that always needs one. Deleting objects one at a time works on ECS, and was used to clean up.

Why the SDK cannot be told to use MD5, and the ways around it. The first point and the Icechunk options were checked in this spike; the rest is from memory and not verified:

- **The AWS SDKs dropped MD5 in early 2025.** Their default integrity protections replaced `Content-MD5` with CRC checksums on the operations where S3 requires a checksum, `DeleteObjects` among them. `when_required` does not change that, because this operation always requires one.
- **Icechunk's default S3 storage (the Rust `aws-sdk-s3`, 1.127.0 in Icechunk 2.3.1)** has no MD5 option.
- **Icechunk's other S3 storage, `Storage.new_s3_object_store`, uses Apache's `object_store` crate (0.14.2 in Icechunk 2.3.1), which always sends `Content-MD5` on `DeleteObjects`** (`src/aws/client.rs`: "S3 *requires* DeleteObjects to include a Content-MD5 header"). With it, garbage collection worked on ECS, as the table shows. It takes `icechunk.S3Options` (region, endpoint, path-style addressing) and `icechunk.s3_static_credentials`; the spike now uses it for every S3 store, and no longer has the AWS SDK storage or its checksum settings.
- **botocore** has no setting either, but an event handler that computes `Content-MD5` before signing is the known workaround. It would let our own Python code bulk-delete on ECS with a current botocore, as an alternative to the aiobotocore pin. Not tried.
- **ECS** may accept CRC checksums in newer releases. That is a question for its administrators.

- **Others hit the same limit.** The ECS Community Edition issue [#584](https://github.com/EMCECS/ECS-CommunityEdition/issues/584) reports this exact error with current AWS SDKs; it was closed in 2025 with no comment. Elasticsearch ([#162197](https://github.com/elastic/elasticsearch/pull/162197)) and ClickHouse ([#125566](https://github.com/ClickHouse/ClickHouse/pull/125566)) added MD5 settings for it, and AWS's Java and C++ SDKs have MD5 fallbacks. ECS's release notes are behind Dell's sign-in and were not read; no public statement that any ECS or ObjectScale release accepts CRC32 here was found.

The AWS SDK storage has a second problem on ECS. Its first commit failed, because ECS answers a conditional GET with a 304 that carries the object's checksum but no body, and the SDK rejects it ("expected body checksum to be 0c835fe8 but it was 00000000"). Setting `AWS_RESPONSE_CHECKSUM_VALIDATION` and `AWS_REQUEST_CHECKSUM_CALCULATION` to `when_required` fixes that, and the `object_store` storage needs neither.

So Icechunk on ECS should use the `object_store` storage. Its garbage collection then reclaims space, and `recent` can be one repository.

### Reads on ECS

The 2026-11-19 18Z HRDPS run was written to ECS through each storage and read back, from a laptop outside the cluster:

| HRDPS 18Z | `object_store` | AWS SDK |
|---|---|---|
| Point forecast p50 / p90, GRIB integers, point layout | 898 / 1,085 ms | 957 / 1,113 ms |
| Point forecast, float32, point layout | 1,236 / 1,565 ms | 1,013 / 1,665 ms |
| One map, GRIB integers, point layout | 4,406 ms | 4,683 ms |
| One map, int16, map layout | 144 ms | 196 ms |
| Point forecast, int16, map layout | 14,973 ms | 16,265 ms |
| Writing a run, GRIB integers | 19.7 s | 20.6 s |

- **The two storages are as fast as each other.** `object_store` costs nothing and is the only one whose garbage collection works on ECS.
- **`object_store` needs no checksum settings.** It wrote, committed and read with `AWS_RESPONSE_CHECKSUM_VALIDATION` and `AWS_REQUEST_CHECKSUM_CALCULATION` unset.
- **The times are mostly round trips from the laptop to ECS,** not the storage. A point forecast is a handful of requests (a chunk per variable, plus the per-hour scales for GRIB integers); a map in the point layout is about 110 chunk requests, and a point forecast in the map layout reads 49 whole fields per variable. Local disk took 16 ms and 30 ms for the GRIB integers. Read times from inside the cluster were not measured, and they decide whether these reads are fast enough for an API.
- **Writing** is the laptop's upload, about 6 MB/s.

## As built

`wps_weather_data.grids`, described in the [package README](../../backend/packages/wps-weather-data/README.md#grids), implements this for all five models:

- **A separate job, hourly for each model**, not part of the station jobs, so that a failure in one cannot hold up the other. It downloads the files again for itself.
- **Sources.** HRDPS, RDPS and GDPS come from the MSC datamart, GFS from NOAA's files on AWS and ECMWF from its open data on Google. NOAA and ECMWF fields are fetched as byte ranges found in the index beside each file. GFS is NOAA's own encoding, not NOMADS's. ECMWF's 06 and 18 UTC runs are now kept to 144 hours, which is how far they go (90 when the spike was run).
- **A run is stored only once all of it is published**, checked before anything is downloaded, and committed once. A file that disappears part way leaves nothing committed, and the run is tried again the next hour.
- **One variable at a time.** Each is downloaded, cropped, converted to GRIB integers, written to every store that needs the run, and its files deleted. Cropping comes before the conversion. HRDPS peaked at 508 MiB, against 826 MiB holding the whole run, measured on a laptop writing to local disk. The cron job's limit is 1 GiB.
- **The stores are independent.** `history` is committed first, and a store that fails is left alone for the rest of that hour's job while the other is kept. The job then fails, with the errors. Icechunk retries a refused update 15 times, about half a minute, instead of its default of 100 times, over an hour. The job is stopped after 30 minutes. On 2026-11-23 ECS refused every update of HRDPS `recent` for about 12 hours, with nothing else writing to it, and before these changes that blocked the whole HRDPS job. Deleting the store cleared it; the cause is not known.
- **Maintenance** is the nightly `station-weather-maintenance` job. It expires snapshots older than a day and garbage collects objects older than an hour, so a grid store cannot be read as it was more than about a day ago.

HRDPS and RDPS have run in dev since 2026-11-20, and `backend/scripts/model_grid_check.py` checks what is stored against the datamart. GDPS, GFS and ECMWF have been stored and checked on local disk: on 2026-11-23, every field compared with what was published was exact (30 for GDPS, 48 for GFS, 100 for two ECMWF runs), and the peaks were 443, 146 and 368 MiB.

## Compared with keeping the GRIB files

Keeping the downloaded GRIB files instead of Zarr would take about 20 times the space, because they cover each model's whole domain, not BC:

| Model | GRIB as downloaded, per run | Covers | Zarr GRIB integers, BC crop, per run |
|---|---|---|---|
| HRDPS | 662 MB | continental grid | 110.7 MB |
| RDPS | 487 MB | North America | 18.7 MB |
| GDPS | 820 MB | the globe | 5.4 MB |
| GFS | 4 MB | BC, cropped by NOMADS | 2.3 MB |
| ECMWF | 799 MB | the globe | 5.0 MB |

Under the chosen [retention](#retention), one run per model per day, that is about 1 TB a year of GRIB (HRDPS 242 GB, GDPS 299, ECMWF 292, RDPS 178, GFS 1.5) against about 52 GB of Zarr. The GRIB sizes are as measured in the spike's downloads.

GRIB files cropped to BC would be about the same size as Zarr, possibly smaller: MSC's JPEG 2000 packing compresses each field well. Scaling by the share of cells inside BC, which was not measured, gives about 85 MB a run for HRDPS against 111 MB, and about 4 MB for GDPS against 5.4 MB. GFS's simple packing does not compress, so Zarr is smaller there (2.3 MB against 4). Cropping means re-encoding every file and checking that the values survive exactly.

Cropped GRIB would still be worse to use:

- **Objects.** A file per variable per hour: about 245 per HRDPS run and 425 per RDPS run, against 25 to 40 in Zarr.
- **Point reads.** One location's forecast decodes a whole field from every hour's file, 49 per variable for HRDPS. Zarr's point layout reads one small chunk per variable.
- **No commits or versions.** A reader can see a half-written run, and history is kept by hand.

## Open questions

- **Read times on ECS from inside the cluster.** From a laptop, a point forecast took about 1 s and a map about 4.5 s in the point layout (see [Reads on ECS](#reads-on-ecs)).
- **More models on ECS.** GDPS, GFS and ECMWF have not been written to ECS; their sizes are in [Sizes](#sizes).
- **More runs.** One run was written. Compression is per run, so it should hold, but the object count and Icechunk's metadata over months of commits are not measured.
- **ECS quota and cost** for about 52 GB a year for all five models under the chosen [retention](#retention), and who approves it.

## Next steps

1. Run the spike against ECS with two or more runs of a model, for example RDPS:

   ```sh
   uv run scripts/model_grid_icechunk_spike.py --model rdps --run 2026-11-19T12 --run 2026-11-19T18 --variant f32-pcodec-point --variant grib-pcodec-point --s3-prefix dev/zarr-spike
   ```

   from `./backend`, with `OBJECT_STORE_SERVER`, `OBJECT_STORE_USER_ID`, `OBJECT_STORE_SECRET` and `OBJECT_STORE_BUCKET` set as the deployments have them. Stores go under `dev/zarr-spike/{model}/{variant}`. Delete `dev/zarr-spike` afterwards, one object at a time: ECS rejects boto3's bulk `DeleteObjects` without a `Content-MD5` header. The MSC datamart keeps about a day, so MSC runs must be recent.
2. Measure reads from inside the cluster, from a pod reading the `object_store` stores, to separate ECS's own latency from the laptop's network path.
3. Ask the object storage team whether ECS will accept the AWS SDKs' CRC checksums, which would also let our own Python code drop the aiobotocore pin.
4. Add endpoints that read a whole field. The Station Weather API reads one location's forecast (`/grids/{model}/point`).

## Open-Meteo's quantization

From the source of [om-file-format](https://github.com/open-meteo/om-file-format) (`c/src/om_common.c`, `c/include/om_common.h`) and [open-meteo](https://github.com/open-meteo/open-meteo) (`Sources/App/Gfs/GfsVariable.swift`, `Sources/App/Gem/GemVariable.swift`), read on 2026-11-19:

What this rounding loses against the published values is under [Accuracy and rounding](#accuracy-and-rounding).

- Values are stored as int16: `round((value + add_offset) * scale_factor)`, clamped to the int16 range. Missing values are `INT16_MAX` (32767), so a real value that scales to 32767 also reads back as missing.
- Neighbouring values are delta coded in two dimensions and compressed with FastPFOR. Other compression types are int32 for wider ranges, `log10(1 + x)` before scaling for skewed values, and FPX for lossless floats.
- Surface scale factors for GFS and GEM: temperature 20, relative humidity and cloud cover 1, precipitation 10, wind and gusts 10, wind direction 1, pressure 10, snow depth 100, soil moisture 1000, CAPE 0.1. Pressure-level factors shrink with height, because upper-air fields vary more and compress worse.
- Which compression type each variable uses, the factors for ECMWF and other models, and the code that applies the factors were not found.
