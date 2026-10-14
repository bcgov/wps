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
sfms_ng/runs/{run_datetime yyyy/mm/dd}/{run_type}/{for_date}_{run_datetime}_run.json
```

- `run_type` is `actual` or `forecast`.
- `yyyy/mm/dd` is the **run datetime's** date (UTC) — not the target date.
- `for_date` is the run's target date, ISO `YYYY-MM-DD`.
- the `run_datetime` in the file name is the same UTC datetime, compacted to
  `YYYYMMDDThhmmssffffffZ` (including six microsecond digits).

For example, an actuals run for 2026-10-13 that started at 20:45:00 UTC writes:

```
sfms_ng/runs/2026/10/13/actual/2026-10-13_20261013T204500000000Z_run.json
```

and that day's forecast run, processing 2026-10-14, writes:

```
sfms_ng/runs/2026/10/13/forecast/2026-10-14_20261013T211500000000Z_run.json
```

Because the folder is the run datetime, re-runs and backfills of the same target date never
overwrite an earlier manifest: each run lands under its own run datetime. A manifest's
`run_datetime` is the same value the run stored on its `sfms_run` row, so the two can be joined
on it.

Manifests are written at the end of a successful run. A run that fails writes no manifest; the
`sfms_run_log` rows for that run record which job failed.

## Schema

The schema is versioned. Every manifest records the `version` it was written with; the layout
below is version `1`. Parsers should read `version` first and ignore unknown fields, so later
versions can add to them.

```json
{
  "version": 1,
  "run_datetime": "2026-10-13T20:45:00Z",
  "run_type": "actual",
  "for_date": "2026-10-13",
  "input": {
    "station_codes": [122, 346],
    "fuel_raster": {
      "base": "sfms/static/fuel/2026/fbp2026_v1.tif",
      "temporal": "sfms_ng/fuel/temporal/2026/10/13/2/fbp2026_10_13_2.tif",
      "pc": "sfms/static/m12_2026.tif"
    },
    "seed_rasters": {
      "ffmc": "sfms_ng/actual/2026/10/12/ffmc_20261012.tif",
      "dmc": "sfms_ng/actual/2026/10/12/dmc_20261012.tif",
      "dc": "sfms_ng/actual/2026/10/12/dc_20261012.tif"
    },
    "static_rasters": {
      "dem": "sfms/static/bc_elevation.tif",
      "mask": "sfms/static/bc_mask.tif",
      "elevation": "sfms_ng/static/bc_elevation.tif",
      "latitude": "sfms_ng/static/latitude.tif",
      "longitude": "sfms_ng/static/longitude.tif",
      "slope": "sfms_ng/static/bc_slope.tif",
      "aspect": "sfms_ng/static/bc_aspect.tif"
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
    "fmc_raster": "sfms_ng/static/fmc/2026/10/13/fmc_20261013.tif"
  }
}
```

### Fields

| Field          | Type   | Notes                                                                                            |
| -------------- | ------ | ------------------------------------------------------------------------------------------------ |
| `version`      | int    | Schema version. `1` for the layout above; unknown top-level fields should be ignored by parsers. |
| `run_datetime` | string | ISO 8601 UTC instant the run was saved. Also names the manifest's folder and file.               |
| `run_type`     | string | `actual` or `forecast`.                                                                          |
| `for_date`     | string | ISO date the run's rasters are for.                                                              |
| `input`        | object | What the run read. See below.                                                                    |
| `output`       | object | What the run wrote, by product. See below.                                                       |

Every raster path is a plain object store key in the same bucket as the manifest, not a GDAL
`/vsis3/{bucket}/` path; a reader that wants the GDAL path prefixes the key with `/vsis3/{bucket}/`.
Weather, FWI, FBP and FMC rasters are overwritten in place by later runs of the same target date
and run type, which is what makes this manifest the durable record of which run used them.
Versioned rasters — the base fuel grid, the temporal fuel grid and the Julian archives — are unique
per version, so once a manifest records their keys, those keys keep naming the same bytes.

Only sections the run actually used are present. A field is absent — not null — when the run did
not record it, and groups that were recorded are objects keyed by parameter name. For example, a
run whose FWI calculation was skipped for missing previous-day rasters records
`input.station_codes`, `input.fuel_raster.base` and `output.weather`, leaves `input.seed_rasters`,
`output.fwi` and `output.fbp` as empty objects, and omits `output.fuel_raster`.

#### `input`

| Field            | Contents                                                                                                                        |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `station_codes`  | The station codes whose daily weather the run interpolated from WF1.                                                            |
| `fuel_raster`    | `base`: the base fuel grid selected for the run's year. `temporal`: the dated temporal fuel grid FBP ran on. `pc`: the percent-conifer raster paired with the base grid's year. |
| `seed_rasters`   | Previous-day FFMC/DMC/DC rasters the run calculated FWI forward from. Absent on April/May Monday re-interpolation days, which interpolate the base indices from stations instead, and for the derived ISI/BUI/FWI calculations that follow them. |
| `static_rasters` | Static rasters by role: `dem` and `mask` for interpolation, `elevation`, `latitude` and `longitude` for FMC, `slope` and `aspect` for primary FBP. `dem` is the legacy SFMS elevation raster and is distinct from `elevation`. |
| `julian_rasters` | The green-up and grass curing rasters the temporal fuel grid was built from, keyed by name. These are the **archive** keys (`sfms_ng/static/julian/archive/{name}/{sha256}.tif`), because the live `sfms_ng/static/julian/{name}.tif` keys are replaced over time and an archive key is the content-addressed copy of the exact bytes the grid was built from. |
| `fmc_raster`     | The shared FMC raster for the target date. Listed twice: it is an input to primary FBP, and it is a product of the run.         |

#### `output`

Rasters the run wrote, grouped by product:

- `weather`: interpolated weather parameters, keyed by parameter (`temperature`,
  `relative_humidity`, `wind_speed`, `wind_direction`, `precipitation`).
- `fwi`: FWI indices, keyed by parameter (`ffmc`, `dmc`, `dc`, `isi`, `bui`, `fwi`).
- `fbp`: primary FBP products, keyed by parameter (`sfc`, `ros`, `hfi`, `tfc`, `cfb`).
- `fuel_raster`: the dated temporal fuel grid, also listed as `input.fuel_raster.temporal`
  because primary FBP consumes it.
- `fmc_raster`: the shared FMC raster for the target date, also listed as `input.fmc_raster`.

Each published raster also has a cloud-optimized copy at the same key with `_cog.tif` in place
of `.tif` (see `SFMSNGRasterAddresser.get_cog_key`).

## Changing the schema

Additive changes go in the next `version`: bump `MANIFEST_SCHEMA_VERSION` in
`wps_sfms/run_manifest.py`, leave version `1` manifests as they are, and document the new
version's layout here. A breaking change to an existing field's meaning is not an additive
change — a run's manifest should always be readable against the version it records.
