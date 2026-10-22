# SFMS Input/Output Tracing

Every SFMS run writes one JSON manifest recording the inputs and outputs it used. Rasters are
overwritten in place by every daily run and backfill, so a manifest is the durable record of what a
particular run read and wrote — which is what you need to trace and debug a run long after its
rasters are replaced.

A run is one `actual` or `forecast` SFMS run for one target date. A forecast job processes three
target dates, so it writes three manifests.

Nothing reads manifests yet — no API or frontend consumes them. They are written so a run can be
traced by hand, and so future tooling has a stable, documented record to parse; a new consumer
should read `version` first and ignore unknown fields rather than assuming this layout is the
latest.

## Where manifests are stored

Manifests live in the same object store as the rasters they describe, under the SFMSNG root:

```
sfms_ng/runs/{run_type}/{for_date yyyy/mm/dd}/target-{for_date}_run-{run_datetime}.json
```

- `run_type` is `actual` or `forecast`.
- `yyyy/mm/dd` is the **target date**, mirroring the rasters' `sfms_ng/{run_type}/yyyy/mm/dd/`
  layout, so a raster's manifests sit at the parallel path.
- `for_date` is the run's target date, ISO `YYYY-MM-DD`, repeated in the file name so a manifest
  still says which date it describes outside its folder.
- `run_datetime` is the UTC datetime the run was saved, as ISO 8601 with `-` in place of `:` and
  six microsecond digits (`YYYY-MM-DDThh-mm-ss.ffffffZ`).

For example, an actuals run for 2026-10-13 that started at 20:45:00 UTC writes:

```
sfms_ng/runs/actual/2026/10/13/target-2026-10-13_run-2026-10-13T20-45-00.000000Z.json
```

and that day's forecast run, processing 2026-10-14, writes:

```
sfms_ng/runs/forecast/2026/10/14/target-2026-10-14_run-2026-10-13T21-15-00.000000Z.json
```

Each run type's folder for a target date collects that type's runs of the date: the `forecast`
folder holds every forecast run that covered it, and the `actual` folder its actual run and any
re-runs and backfills. Each lands under its own run datetime, so none overwrites another, and the
fixed-width names list in the order the runs happened. A manifest's
`sfms_run_id` is its run's `sfms_run.id`, so it joins directly to that row and to the run's
`sfms_run_log` rows. Its `run_datetime` is also the value stored on that row, which identifies the
run where the id doesn't, such as against another environment's database.

Manifests are written when a run reaches a terminal state. A failed run's manifest contains the
inputs recorded so far and outputs from steps that completed successfully, plus the failing step
and exception type. Failures before an `SFMSRunContext` is created have no run manifest.

## Schema

The schema is versioned. Every manifest records the `version` it was written with; the layout
below is version `1`. Parsers should read `version` first and ignore unknown fields, so later
versions can add to them.

```json
{
  "version": 1,
  "sfms_run_id": 4211,
  "run_datetime": "2026-10-13T20:45:00Z",
  "run_type": "actual",
  "for_date": "2026-10-13",
  "status": "success",
  "input": {
    "station_codes": [122, 346],
    "fuel_raster": {
      "base": "sfms/static/fuel/2026/fbp2026_v1.tif",
      "temporal": "sfms_ng/fuel/temporal/2026/10/13/2/fbp2026_10_13_2.tif",
      "percent_conifer": "sfms/static/m12_2026.tif"
    },
    "seed_rasters": {
      "ffmc": "sfms_ng/actual/2026/10/12/ffmc_20261012.tif",
      "dmc": "sfms_ng/actual/2026/10/12/dmc_20261012.tif",
      "dc": "sfms_ng/actual/2026/10/12/dc_20261012.tif"
    },
    "static_rasters": {
      "dem": "sfms/static/bc_elevation.tif",
      "mask": "sfms/static/bc_mask.tif",
      "slope": "sfms_ng/static/bc_slope.tif",
      "aspect": "sfms_ng/static/bc_aspect.tif",
      "grass_curing": "sfms_ng/static/archive/percent_grass_curing/5e8d0f3a.tif"
    },
    "julian_rasters": {
      "green_up_on": "sfms_ng/static/julian/archive/green_up_on/9f2c1ab4.tif",
      "green_up_off": "sfms_ng/static/julian/archive/green_up_off/4b7ade91.tif",
      "grass_standing": "sfms_ng/static/julian/archive/grass_standing/c1d05e77.tif",
      "grass_matted": "sfms_ng/static/julian/archive/grass_matted/77e3b2c8.tif"
    },
    "fmc_raster": "sfms_ng/static/fmc/2026/10/13/fmc_20261013.tif"
  },
  "output": {
    "weather": {
      "temperature": "sfms_ng/actual/2026/10/13/temperature_20261013.tif",
      "relative_humidity": "sfms_ng/actual/2026/10/13/relative_humidity_20261013.tif",
      "wind_speed": "sfms_ng/actual/2026/10/13/wind_speed_20261013.tif",
      "wind_direction": "sfms_ng/actual/2026/10/13/wind_direction_20261013.tif",
      "precipitation": "sfms_ng/actual/2026/10/13/precipitation_20261013.tif"
    },
    "fwi": {
      "ffmc": "sfms_ng/actual/2026/10/13/ffmc_20261013.tif",
      "dmc": "sfms_ng/actual/2026/10/13/dmc_20261013.tif",
      "dc": "sfms_ng/actual/2026/10/13/dc_20261013.tif",
      "isi": "sfms_ng/actual/2026/10/13/isi_20261013.tif",
      "bui": "sfms_ng/actual/2026/10/13/bui_20261013.tif",
      "fwi": "sfms_ng/actual/2026/10/13/fwi_20261013.tif"
    },
    "fbp": {
      "sfc": "sfms_ng/actual/2026/10/13/sfc_20261013.tif",
      "ros": "sfms_ng/actual/2026/10/13/ros_20261013.tif",
      "hfi": "sfms_ng/actual/2026/10/13/hfi_20261013.tif",
      "tfc": "sfms_ng/actual/2026/10/13/tfc_20261013.tif",
      "cfb": "sfms_ng/actual/2026/10/13/cfb_20261013.tif"
    },
    "fuel_raster": "sfms_ng/fuel/temporal/2026/10/13/2/fbp2026_10_13_2.tif",
    "danger_rating_raster": "sfms_ng/actual/2026/10/13/danger_rating_20261013.tif"
  },
  "reused": {
    "fmc_raster": "sfms_ng/static/fmc/2026/10/13/fmc_20261013.tif"
  }
}
```

In this example the run built version 2 of the date's temporal fuel grid, so it is an output, and
reused the FMC raster an earlier run had calculated for the date.

### Fields

| Field          | Type   | Notes                                                                                            |
| -------------- | ------ | ------------------------------------------------------------------------------------------------ |
| `version`      | int    | Schema version. `1` for the layout above; unknown top-level fields should be ignored by parsers. |
| `sfms_run_id`  | int    | The run's `sfms_run.id`, so the manifest joins to its `sfms_run` row and `sfms_run_log` rows.    |
| `run_datetime` | string | ISO 8601 UTC instant the run was saved. Also names the manifest's file.                          |
| `run_type`     | string | `actual` or `forecast`.                                                                          |
| `for_date`     | string | ISO date the run's rasters are for.                                                              |
| `status`       | string | `success` or `failed`; manifests are written only for terminal runs whose `sfms_run` row was committed, so every manifest joins to one. |
| `failed_step`  | string | Present for failed runs; the step that raised.                                                   |
| `failure_type` | string | Present for failed runs; the exception class.                                                    |
| `failure_message` | string | Optional, truncated exception message for failed runs.                                       |
| `input`        | object | What the run read. See below.                                                                    |
| `output`       | object | What the run wrote, by product. See below.                                                       |
| `reused`       | object | Rasters the run would otherwise have produced, but which already existed. See below.             |

Every raster path is a plain object store key in the same bucket as the manifest, not a GDAL
`/vsis3/{bucket}/` path; a reader that wants the GDAL path prefixes the key with `/vsis3/{bucket}/`.
Weather, FWI, FBP and FMC rasters are overwritten in place by later runs of the same target date
and run type, which is what makes this manifest the durable record of which run used them.
Versioned rasters — the base fuel grid, the temporal fuel grid and the Julian archives — are unique
per version, so once a manifest records their keys, those keys keep naming the same bytes.

Only sections the run actually used are present. A field is absent — not null — when the run did
not record it, and groups that were recorded are objects keyed by parameter name. For example, a
run whose FWI calculation was skipped for missing previous-day rasters has `status` `failed` with
`failed_step` `fwi_seed_check`, records `input.station_codes`, `input.fuel_raster.base` and
`output.weather`, leaves `input.seed_rasters`, `output.fwi` and `output.fbp` as empty objects, and
records no temporal fuel grid in `input`, `output` or `reused`.

#### `input`

| Field            | Contents                                                                                                                        |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `station_codes`  | The station codes whose daily weather the run interpolated from WF1.                                                            |
| `fuel_raster`    | `base`: the base fuel grid selected for the run's year. `temporal`: the dated temporal fuel grid FBP ran on. `percent_conifer`: the percent-conifer raster paired with the base grid's year. |
| `seed_rasters`   | Previous-day FFMC/DMC/DC rasters the run calculated FWI forward from. An empty object on April/May Monday re-interpolation days, which interpolate the base indices from stations instead, and for the derived ISI/BUI/FWI calculations that follow them. |
| `static_rasters` | Static rasters by role: `dem` and `mask` for interpolation, `elevation`, `latitude` and `longitude` for FMC when the run calculated it rather than reusing it, `slope`, `aspect` and `grass_curing` for primary FBP. `grass_curing` is the archive key the raster was copied to by content hash, since its live key is replaced over time. `dem` is the legacy SFMS elevation raster and is distinct from `elevation`. |
| `julian_rasters` | The green-up and grass curing rasters the temporal fuel grid was built from, keyed by name. These are the **archive** keys (`sfms_ng/static/julian/archive/{name}/{sha256}.tif`), because the live `sfms_ng/static/julian/{name}.tif` keys are replaced over time and an archive key is the content-addressed copy of the exact bytes the grid was built from. |
| `fmc_raster`     | The shared FMC raster for the target date that primary FBP read, whether the run calculated it or reused it.                     |

#### `output`

Rasters the run wrote, grouped by product:

- `weather`: interpolated weather parameters, keyed by parameter (`temperature`,
  `relative_humidity`, `wind_speed`, `wind_direction`, `precipitation`).
- `fwi`: FWI indices, keyed by parameter (`ffmc`, `dmc`, `dc`, `isi`, `bui`, `fwi`).
- `fbp`: primary FBP products, keyed by parameter (`sfc`, `ros`, `hfi`, `tfc`, `cfb`).
- `fuel_raster`: the dated temporal fuel grid, when the run built a new version of it.
- `fmc_raster`: the shared FMC raster for the target date, when the run calculated it.
- `danger_rating_raster`: the station danger rating raster, when interpolation completed.

Each published raster also has a cloud-optimized copy at the same key with `_cog.tif` in place
of `.tif` (see `SFMSNGRasterAddresser.get_cog_key`).

#### `reused`

Rasters the run would otherwise have produced, but which an earlier run already had. A date is
processed by several forecast runs and then its actual run, and only the first to process it
produces these, so most runs reuse them:

- `fuel_raster`: the temporal fuel grid, when a stored version was built from the same base fuel
  grid and Julian rasters and still matches its recorded hash.
- `fmc_raster`: the FMC raster for the target date, when it already existed.

Each is in either `output` or `reused`, never both, and is always also in `input`, since primary
FBP reads it either way.

## Changing the schema

Additive changes go in the next `version`: bump `MANIFEST_SCHEMA_VERSION` in
`wps_sfms/run_manifest.py`, leave version `1` manifests as they are, and document the new
version's layout here. A breaking change to an existing field's meaning is not an additive
change — a run's manifest should always be readable against the version it records.
