# Model grid storage spike: HRDPS in Zarr on Icechunk

Status: spike, run on local disk on 2026-11-19, and in a small test against our object store (ECS). Full read times on ECS are not yet measured.

## Question

The model jobs keep only each run's values at weather stations (`runs`, `by_time`, `by_station`). Could we also keep every run's whole grid, cropped to BC, as Zarr in Icechunk, alongside the station data and with nothing removed? And if so, what would it cost in storage, and how fast are the reads?

Keeping the grids would let us backfill a station added later, give forecasts at any location (fires, fire zones), recompute bias adjustment and lead-time rules from the raw fields, and feed SFMS from the same store. The [storage evaluation](station-weather-storage-evaluation.md#could-we-change-how-we-store-the-data-so-zarr-fits) rated this "the version worth doing, but a separate and much larger project that needs sizing first", with a rough estimate of 475 GB a year for HRDPS before compression. This spike measures it.

## Setup

Scripts: [`backend/scripts/model_grid_icechunk_spike.py`](../../backend/scripts/model_grid_icechunk_spike.py) writes and measures the stores, and [`backend/scripts/msc_grib_precision_check.py`](../../backend/scripts/msc_grib_precision_check.py) reports the precision MSC packs each field at. Their dependencies (zarr 3.4.2, icechunk 2.3.1, numcodecs 0.17.1 with pcodec, eccodes 2.48.0) are declared in the scripts, not added to the project.

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

What MSC packs each field at, from `msc_grib_precision_check.py` on the 18Z run's hour 24, against the `i16` variants:

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

Only sizes, compression and errors carry over to ECS. Read and write times on ECS depend on request latency and have not been measured.

## Findings

- **Storing the GRIB integers is the most compact lossless option.** It keeps exactly what MSC publishes in 110.7 MB a run, 3.7x, which is 162 GB a year for HRDPS at four runs a day with every hour kept. Lossless float32 needs 163 MB (2.5x).
- **The scaled int16 variants are not accurate against the source.** They are 7.4x (82 GB a year), but MSC packs every field more finely than the scales chosen here (temperature to 0.001 K against 0.05). Their error, half a step, is far larger than anything in the source. Open-Meteo's scales were chosen for a forecast API, not to keep the source exactly.
- **No one variable dominates the lossless size.** Temperature, stored to 0.001 K, is the largest at 25 MB a run, and the others are 16 to 23 MB. Keeping every variable exact leaves which runs and hours are kept as the remaining lever: each 49-hour run overlaps the next seven, so keeping only the first six hours of each run would store each hour once, roughly an eighth of the size. That has not been measured.
- **pcodec beats zstd** by 15 to 20 % for float32 and for int16, with no slower reads.
- **The point layout is the right default.** A point forecast is one chunk per variable. A map is about 110 chunks per variable, which was still fast here. The map layout makes maps ten times faster and point reads ten times slower. Which matters more on ECS, where each chunk is a ranged request, is the main thing left to measure.
- **Writing is cheap.** A run encodes and commits in under a second once it is in memory. The cost of a job is the download, which the HRDPS job already does.
- **The rough estimate held.** The evaluation's 475 GB a year for HRDPS before compression compares with 605 GB measured uncompressed (415 MB x 4 runs x 365 days).

## Open questions

- **Read times on ECS**, for a point forecast and for a map in each layout.
- **Icechunk on ECS works, with one setting.** A small test (3 hours of one run, one variant) wrote, committed and read back from ECS on 2026-11-19, with conditional writes on. Without the setting, the first commit failed: ECS answers Icechunk's conditional GET with a 304 that carries the object's checksum but no body, and the AWS SDK inside Icechunk rejects it ("expected body checksum to be 0c835fe8 but it was 00000000"). Setting `AWS_RESPONSE_CHECKSUM_VALIDATION` and `AWS_REQUEST_CHECKSUM_CALCULATION` to `when_required` fixes it, as the same incompatibility needed for botocore. The script sets both when it writes to S3. Any job writing Icechunk to ECS will need them.
- **The other models.** Only HRDPS was measured. RDPS (10 km), GDPS, GFS, NAM and ECMWF have coarser grids, so far fewer cells over BC, but more forecast hours. They need their own runs of the spike.
- **More runs.** One run was written. Compression is per run, so it should hold, but the object count and Icechunk's metadata over months of commits are not measured.
- **ECS quota and cost** for about 100 GB a year per model, and who approves it.
- **Where the writes go.** Inside the existing model jobs (more memory and time in jobs with tight limits), or a separate job reading the same downloaded files, so that a failure there cannot hold up the station data.

## Next steps

1. Run the spike against ECS with two or more runs:

   ```sh
   uv run scripts/model_grid_icechunk_spike.py --run 2026-11-19T18 --run 2026-11-20T00 --s3-prefix dev/zarr-spike
   ```

   from `./backend`, with `OBJECT_STORE_SERVER`, `OBJECT_STORE_USER_ID`, `OBJECT_STORE_SECRET` and `OBJECT_STORE_BUCKET` set as the deployments have them. Delete `dev/zarr-spike` afterwards. The datamart keeps about a day, so the runs must be recent.
2. If ECS reads are fast enough, run it for RDPS and GDPS to size the other models.
3. Decide on the layout, the precision per variable and where the writes run, then design the job.

## Open-Meteo's quantization

From the source of [om-file-format](https://github.com/open-meteo/om-file-format) (`c/src/om_common.c`, `c/include/om_common.h`) and [open-meteo](https://github.com/open-meteo/open-meteo) (`Sources/App/Gfs/GfsVariable.swift`, `Sources/App/Gem/GemVariable.swift`), read on 2026-11-19:

- Values are stored as int16: `round((value + add_offset) * scale_factor)`, clamped to the int16 range. Missing values are `INT16_MAX` (32767), so a real value that scales to 32767 also reads back as missing.
- Neighbouring values are delta coded in two dimensions and compressed with FastPFOR. Other compression types are int32 for wider ranges, `log10(1 + x)` before scaling for skewed values, and FPX for lossless floats.
- Surface scale factors for GFS and GEM: temperature 20, relative humidity and cloud cover 1, precipitation 10, wind and gusts 10, wind direction 1, pressure 10, snow depth 100, soil moisture 1000, CAPE 0.1. Pressure-level factors shrink with height, because upper-air fields vary more and compress worse.
- Which compression type each variable uses, the factors for ECMWF and other models, and the code that applies the factors were not found.
