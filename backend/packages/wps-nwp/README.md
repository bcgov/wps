# wps-nwp

Fetches numerical weather prediction model output straight from the agencies' public mirrors.

- **Only what you ask for.** Where a model publishes an index, just the bytes of the requested
  fields are downloaded, not the whole file.
- **Concurrent.** Every step and variable of a request is fetched at once over a shared
  connection pool.
- **Nothing on disk.** No download directory, cache or config file. Fields are held in memory
  and decoded with eccodes on first use.
- **Mirrors.** Each model lists its mirrors in order. A mirror that is missing a file, returns
  errors or serves corrupt data is passed over for the next one, and a host that cannot be
  reached is skipped for five minutes rather than timing out on every request.

## Usage

```python
import asyncio
import wps_nwp as nwp

async def main():
    async with nwp.Client() as client:
        run = await client.latest_run("ifs", step=24)  # newest run that has reached +24h
        fields = await client.fetch(
            "ifs", run, steps=range(0, 25, 3), variables=["t2m", "d2m", "u10", "v10", "precip"]
        )

    for field in fields:
        print(field.variable, field.valid_time, field.units, field.sample([53.92], [-122.75]))

asyncio.run(main())
```

`fetch` returns a list of `Field`, ordered by step and then by variable:

| | |
| --- | --- |
| `model`, `variable`, `run`, `step`, `valid_time`, `url` | what the field is and where it came from |
| `grib` | the raw GRIB2 message, for storing or forwarding without decoding |
| `values` | 2D array in the model's own row order, NaN where missing |
| `grid` | `lats` and `lons` of every point, and `nearest(lats, lons)` |
| `units` | units of `values` |
| `sample(lats, lons)` | values at the grid points nearest to each location |

A field that is not published raises `NotAvailable`. Pass `skip_missing=True` to get back
whatever is published instead, which is the usual choice when polling a run that is still
coming in. A field that exists but could not be retrieved from any mirror always raises
`FetchError`.

## Models

| Name | Model | Source | Runs (UTC) |
| --- | --- | --- | --- |
| `ifs` | ECMWF IFS, 0.25° | AWS, then Google Cloud | 00, 06, 12, 18 |
| `aifs` | ECMWF AIFS Single, 0.25° | AWS, then Google Cloud | 00, 06, 12, 18 |
| `gfs` | NOAA GFS, 0.25° | AWS, then NOMADS | 00, 06, 12, 18 |
| `nam` | NOAA NAM, 12 km CONUS | AWS | 00, 06, 12, 18 |
| `gdps` | ECCC GDPS, 15 km | HPFX, then MSC Datamart | 00, 12 |
| `rdps` | ECCC RDPS, 10 km | HPFX, then MSC Datamart | 00, 06, 12, 18 |
| `hrdps` | ECCC HRDPS continental, 2.5 km | HPFX, then MSC Datamart | 00, 06, 12, 18 |

NOAA stopped producing NAM after the 2026-11-03 runs; earlier runs remain on AWS.

To use different mirrors, or a product that is not listed, make your own model. They are
plain dataclasses:

```python
from dataclasses import replace

ifs_direct = replace(nwp.IFS, mirrors=("https://data.ecmwf.int/forecasts", *nwp.IFS.mirrors))

hrrr = nwp.NoaaIdx(
    name="hrrr",
    path="hrrr.{run:%Y%m%d}/conus/hrrr.t{run:%H}z.wrfsfcf{step:02d}.grib2",
    variables={nwp.Variable.T2M: ":TMP:2 m above ground:"},
    mirrors=("https://noaa-hrrr-bdp-pds.s3.amazonaws.com",),
    cycles=tuple(range(24)),
)
```

## Variables

`Variable` names mean the same thing, in the same units, for every model that has them.

| Variable | | Units | Not provided by |
| --- | --- | --- | --- |
| `t2m` | air temperature at 2 m | K | |
| `d2m` | dewpoint at 2 m | K | |
| `rh2m` | relative humidity at 2 m | % | ifs, aifs |
| `u10`, `v10` | wind components at 10 m | m s-1 | |
| `wind_speed_10m` | wind speed at 10 m | m s-1 | ifs, aifs, gfs, nam |
| `wind_dir_10m` | direction the wind blows from | degrees true | ifs, aifs, gfs, nam |
| `precip` | precipitation since the start of the run | mm | nam |

`u10` and `v10` are relative to the model grid rather than to true north on the rotated and
projected grids of RDPS, HRDPS and NAM. Use `wind_speed_10m` and `wind_dir_10m` there.

For anything else, name the field in the model's own vocabulary with `Native`. It is returned
as the model encodes it, with no unit conversion.

```python
nwp.Native("msl")                # ECMWF: param, or param:level such as "t:850"
nwp.Native(":TMP:850 mb:")       # NOAA: regex matched against the wgrib2 .idx line
nwp.Native("AirTemp_IsbL-0850")  # ECCC: variable and level from the file name
```

## Sampling

`Field.sample` and `Grid.nearest` pick the nearest grid point by great-circle distance on any
grid. The search is done once per set of points and reused for every field on the same grid.
A location outside a regional model's domain gets the closest point on its edge.
