# wps-nwp

Fetches numerical weather prediction model output straight from the agencies' public mirrors.

- **Only what you ask for.** Where a model publishes an index, just the bytes of the requested
  fields are downloaded, not the whole file.
- **Concurrent.** Every step and variable of a request is fetched at once over a shared
  connection pool.
- **Nothing on disk.** No download directory, cache or config file. Fields are held in memory
  and decoded on first use.
- **Mirrors.** Each model lists its mirrors in order. A mirror that is missing a file, returns
  errors or serves corrupt data is passed over for the next one, and a host that cannot be
  reached is skipped for five minutes rather than timing out on every request.

## Installing

| Depend on | To | Brings in |
| --- | --- | --- |
| `wps-nwp` | fetch fields and store or forward their GRIB | aiohttp, numpy |
| `wps-nwp[decode]` | also read values: `sample`, `values`, `grid`, `nwp.sample` | eccodes |

Without the extra, anything that decodes raises an `ImportError` naming it.

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
| `relative_to_grid` | whether a wind component is along the grid's axes rather than true east and north |

A field that is not published raises `NotAvailable`. Pass `skip_missing=True` to get back
whatever is published instead, which is the usual choice when polling a run that is still
coming in. A field that exists but could not be retrieved from any mirror always raises
`FetchError`.

### A whole run

`fetch` returns every field at once, which for a full run is hundreds of megabytes of GRIB.
`stream` takes the same arguments and hands over one step at a time, downloading no more than
`window` steps (8 by default) ahead of the loop, so memory stays flat however long the run is:

```python
async with nwp.Client() as client:
    async for fields in client.stream("hrdps", run, range(1, 49), ["t2m", "rh2m", "precip"]):
        for field, values in zip(fields, await nwp.sample(fields, lats, lons)):
            store(field.step, field.variable, values)
```

Each item is one step's fields, ordered by variable. Steps arrive in the order they finish
downloading, not the order requested.

`nwp.sample` is `Field.sample` for several fields at once, run in worker threads. ECMWF and
NOAA fields decode in a few milliseconds, but ECCC's are JPEG2000 and take 60 to 260 ms each.
Awaiting `nwp.sample` keeps the downloads going while they decode and uses more than one core;
`workers` (2 by default) sets how many decode at a time, each costing one decoded grid of
memory.

## Models

| Name | Model | Source | Runs (UTC) | Steps |
| --- | --- | --- | --- | --- |
| `ifs` | ECMWF IFS, 0.25° | [AWS](https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com), then [Google Cloud](https://storage.googleapis.com/ecmwf-open-data) | 00, 06, 12, 18 | 3-hourly to 144 h, then 6-hourly to 360 h |
| `aifs` | ECMWF AIFS Single, 0.25° | [AWS](https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com), then [Google Cloud](https://storage.googleapis.com/ecmwf-open-data) | 00, 06, 12, 18 | 6-hourly to 360 h |
| `gfs` | NOAA GFS, 0.25° | [AWS](https://noaa-gfs-bdp-pds.s3.amazonaws.com), then [NOMADS](https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod) | 00, 06, 12, 18 | hourly to 120 h, then 3-hourly to 384 h |
| `rrfs` | NOAA RRFS, 13 km North America | [AWS](https://noaa-rrfs-ops-pds.s3.amazonaws.com) | 00, 06, 12, 18 | hourly to 84 h |
| `nam` | NOAA NAM, 12 km CONUS | [AWS](https://noaa-nam-pds.s3.amazonaws.com) | 00, 06, 12, 18 | runs up to 2026-11-03 only |
| `gdps` | ECCC GDPS, 15 km | [HPFX](https://hpfx.collab.science.gc.ca), then [MSC Datamart](https://dd.weather.gc.ca) | 00, 12 | 3-hourly to 240 h |
| `rdps` | ECCC RDPS, 10 km | [HPFX](https://hpfx.collab.science.gc.ca), then [MSC Datamart](https://dd.weather.gc.ca) | 00, 06, 12, 18 | hourly to 84 h |
| `hrdps` | ECCC HRDPS continental, 2.5 km | [HPFX](https://hpfx.collab.science.gc.ca), then [MSC Datamart](https://dd.weather.gc.ca) | 00, 06, 12, 18 | hourly to 48 h |

NOAA stopped producing NAM after the 2026-11-03 runs, and RRFS replaces it. RRFS also
publishes 3 km grids, but the CONUS one covers only the south of British Columbia and the
Alaska one misses part of the east, so `rrfs` is the 13 km North America grid, which covers
the whole province. RRFS runs every hour, but only the four runs listed publish that grid.

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
| `wind_speed_10m` | wind speed at 10 m | m s-1 | ifs, aifs, gfs, nam, rrfs |
| `wind_dir_10m` | direction the wind blows from | degrees true | ifs, aifs, gfs, nam, rrfs |
| `precip` | precipitation since the start of the run | mm | nam |
| `surface_height` | height of the model's terrain above sea level | m | |

`wind_speed_10m` and `wind_dir_10m` come straight from the models that publish them. For the
others, use `nwp.wind`, below. RRFS publishes relative humidity, so only the ECMWF models lack
it, and it can be worked out from `t2m` and `d2m`.

`precip` is missing at step 0, where nothing has accumulated yet.

`surface_height` is the terrain the model sees, which can be hundreds of metres from a
station's real elevation: at Kamloops the models range from 434 m (HRDPS) to 863 m (GFS),
against 345 m at the airport. It does not change during a run, and IFS, AIFS, GDPS and RDPS
publish it only with step 0, so fetch it from there. ECMWF publishes it as geopotential,
which is converted to metres.

### Wind

`u10` and `v10` are as each model publishes them. On a rotated or projected grid (RDPS,
HRDPS, NAM and RRFS), that is along the grid's axes rather than true east and north, and a
direction worked out from them as they stand is wrong by as much as 35 degrees in British
Columbia. `nwp.wind` allows for that:

```python
u, v = await client.fetch("rrfs", run, 12, ["u10", "v10"])
speed, direction = nwp.wind(u, v, lats, lons)  # m s-1, and degrees true the wind blows from
```

On RDPS and HRDPS its directions agree with those ECCC publishes to within 0.2 degrees for
winds over 8 m/s. In lighter winds they differ by more, up to a few degrees, because RDPS
stores its components coarsely.

For anything else, name the field in the model's own vocabulary with `Native`. It is returned
as the model encodes it, with no unit conversion.

```python
nwp.Native("msl")                # ECMWF: param, or param:level such as "t:850"
nwp.Native(":TMP:850 mb:")       # NOAA: regex matched against the wgrib2 .idx line
nwp.Native("AirTemp_IsbL-0850")  # ECCC: variable and level from the file name
```

## Sampling

`Field.sample` and `Grid.nearest` pick the nearest grid point by great-circle distance on any
grid. A location outside a regional model's domain gets the closest point on its edge.

Every model here except NAM is on a regular or rotated lat/lon grid, where the nearest point
is found from the grid's layout in under a millisecond, without working out the coordinates
of its millions of points. Those are only computed if you ask for `grid.lats` or `grid.lons`,
or sample NAM. The search is done once per set of locations and reused for every field on the
same grid.

`sample` does not keep the decoded array; `values` does, for as long as the field is alive.

`Grid.x_axis_angle` gives the direction of the grid's x axis at grid points, in radians from
true east, which is what `nwp.wind` turns grid-relative components by. It uses the coordinates
of the grid's points, so the first call on a grid works them out.
