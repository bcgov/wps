# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "boto3==1.40.61",
#     "eccodes==2.48.0",
#     "herbie-data==2026.10.0",
#     "icechunk==2.3.1",
#     "numcodecs[pcodec]==0.17.1",
#     "numpy==2.3.5",
#     "zarr==3.4.2",
# ]
# ///
"""Spike: store weather model grids, cropped to BC, as Zarr 3 in Icechunk, and measure the cost.

The model jobs keep only the values at weather stations. This tries keeping each run's whole grid
as well, alongside them, to answer: how many bytes a run takes (and so a year), how long a point's
forecast and a whole map take to read back, and what writing a run costs. Nothing else reads or
writes these stores.

It supports HRDPS, RDPS and GDPS (MSC datamart, which keeps about a day), GFS (NOMADS, cropped
to BC there, kept about ten days) and ECMWF IFS 0.1 degree (open data through herbie, as the
ECMWF job fetches it). It downloads a model's runs, crops each field to BC and writes the same
runs once per variant: lossless float32; Open-Meteo style scaled int16
(round((value - offset) * scale)); or the GRIB file's own packed integers with each field's
scales, which is lossless against what the provider publishes. Each variant is compressed with
zstd or pcodec, in chunks laid out for point reads or for map reads. Each run is one Icechunk
commit, and runs are appended along a `run` axis. Each model's variables are stored as the
provider publishes them (GFS and ECMWF wind as u and v, ECMWF dew point rather than humidity),
so that nothing is converted before storing.

The dependencies above are not project dependencies, so run it with uv, from ./backend:

    uv run scripts/model_grid_icechunk_spike.py --model hrdps --run 2026-11-19T12

That writes to local disk. To write to our object store, set OBJECT_STORE_SERVER,
OBJECT_STORE_USER_ID, OBJECT_STORE_SECRET and OBJECT_STORE_BUCKET as the deployments do and add
`--s3-prefix dev/zarr-spike` (any prefix outside the station weather tables). Stores go under
`{prefix}/{model}/{variant}`. Add `--no-conditional-writes` if the store rejects Icechunk's
conditional writes. Delete the prefix afterwards. Read times are only meaningful against the
object store.

Design: docs/architecture/model-grid-storage-spike.md
"""

import argparse
import os
import random
import resource
import statistics
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import boto3
import eccodes
import icechunk
import numpy as np
import zarr
from zarr.codecs import ZstdCodec
from zarr.codecs.numcodecs import Delta, FixedScaleOffset, PCodec

# Generous BC bounds; a rotated grid makes the crop a little larger.
BC = {"lat": (48.2, 60.1), "lon": (-139.2, -114.0)}
POINT_CHUNK = 64  # cells per side of a point-layout chunk


@dataclass(frozen=True)
class Variable:
    name: str
    units: str
    # Scaled int16: round((value - offset) * scale), so values are kept to 1 / scale.
    offset: float
    scale: float
    # MSC models: the layer in the file name, one file per variable and hour.
    layer: str | None = None
    # Files holding several variables: eccodes keys and values that pick this one's message.
    select: tuple[tuple[str, object], ...] = ()
    # Accumulated since the run started, so zero at hour 0, where there may be no field.
    accumulated: bool = False


@dataclass(frozen=True)
class Model:
    name: str
    variables: tuple[Variable, ...]
    runs_per_day: int
    # The forecast hours kept for a run starting at the given UTC hour.
    hours: Callable[[int], list[int]]
    # The local file holding a variable at an hour (or every variable, if `variable` is None),
    # downloaded if it is not there yet.
    fetch: Callable[[datetime, int, "Variable | None", Path], Path]
    # Whether there is one file per variable and hour, or one per hour holding them all.
    per_variable: bool
    threads: int = 8


def download(url: str, path: Path, attempts: int = 3) -> Path:
    partial = path.with_suffix(".part")
    for attempt in range(1, attempts + 1):
        if path.exists():
            break
        try:
            urllib.request.urlretrieve(url, partial)
            partial.rename(path)
        except urllib.error.HTTPError:
            raise
        except urllib.error.URLError:
            # The datamart sometimes ends a download early.
            if attempt == attempts:
                raise
            time.sleep(attempt)
    return path


def msc_fetch(folder: str, model: str, grid: str) -> Callable:
    def fetch(run: datetime, hour: int, variable: Variable, downloads: Path) -> Path:
        name = f"{run:%Y%m%dT%H}Z_MSC_{model}_{variable.layer}_{grid}_PT{hour:03d}H.grib2"
        url = f"https://dd.weather.gc.ca/today/{folder}/{run:%H}/{hour:03d}/{name}"
        return download(url, downloads / name)

    return fetch


def gfs_fetch(run: datetime, hour: int, _: None, downloads: Path) -> Path:
    # The same NOMADS filter the GFS job uses, cropped to BC on the server.
    query = (
        f"dir=%2Fgfs.{run:%Y%m%d}%2F{run:%H}%2Fatmos&file=gfs.t{run:%H}z.pgrb2.0p25.f{hour:03d}"
        "&var_APCP=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&lev_surface=on"
        "&lev_2_m_above_ground=on&lev_10_m_above_ground=on&subregion=&toplat=60.1"
        "&leftlon=-139.1&rightlon=-114&bottomlat=48"
    )
    path = downloads / f"gfs.{run:%Y%m%d}.t{run:%H}z.f{hour:03d}.grib2"
    return download(f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?{query}", path)


def ecmwf_fetch(run: datetime, hour: int, _: None, downloads: Path) -> Path:
    # As the ECMWF job fetches it: IFS open data at 0.1 degree, through herbie.
    from herbie import Herbie

    herbie = Herbie(
        f"{run:%Y-%m-%d %H}",
        model="ifs",
        product="oper",
        resolution="0p1",
        levtype="sfc",
        fxx=hour,
        save_dir=downloads,
        verbose=False,
    )
    if herbie.grib is None:
        raise FileNotFoundError(f"ECMWF {run:%Y-%m-%dT%H}Z hour {hour} is not published")
    return Path(herbie.download(":(2t|2d|10u|10v|tp):", verbose=False))


def every(step: int, last: int) -> Callable[[int], list[int]]:
    return lambda _: list(range(0, last + 1, step))


def ecmwf_hours(run_hour: int) -> list[int]:
    # 00 and 12 UTC run 3-hourly to 144 hours, then 6-hourly to 240; 06 and 18 UTC to 90.
    if run_hour in (0, 12):
        return list(range(0, 145, 3)) + list(range(150, 241, 6))
    return list(range(0, 91, 3))


def msc_variables(names: dict[str, str]) -> tuple[Variable, ...]:
    """The five variables the MSC jobs read, by layer name. Scales follow Open-Meteo's, with
    relative humidity at 0.1 % to match the station data."""
    return (
        Variable("temperature", "K", 273.15, 20, layer=names["temperature"]),
        Variable("relative_humidity", "%", 0, 10, layer=names["relative_humidity"]),
        Variable("wind_speed", "m/s", 0, 10, layer=names["wind_speed"]),
        Variable("wind_direction", "degrees", 0, 1, layer=names["wind_direction"]),
        Variable(
            "precipitation",
            "mm since the run started",
            0,
            10,
            layer=names["precipitation"],
            accumulated=True,
        ),
    )


# The GDPS and RDPS layer names, as in wps_shared.weather_models.
MSC_NAMES = {
    "temperature": "AirTemp_AGL-2m",
    "relative_humidity": "RelativeHumidity_AGL-2m",
    "wind_speed": "WindSpeed_AGL-10m",
    "wind_direction": "WindDir_AGL-10m",
    "precipitation": "Precip-Accum_Sfc",
}

MODELS = {
    "hrdps": Model(
        "hrdps",
        msc_variables(
            {
                "temperature": "TMP_AGL-2m",
                "relative_humidity": "RH_AGL-2m",
                "wind_speed": "WIND_AGL-10m",
                "wind_direction": "WDIR_AGL-10m",
                "precipitation": "APCP_Sfc",
            }
        ),
        runs_per_day=4,
        hours=every(1, 48),
        fetch=msc_fetch("model_hrdps/continental/2.5km", "HRDPS", "RLatLon0.0225"),
        per_variable=True,
    ),
    "rdps": Model(
        "rdps",
        msc_variables(MSC_NAMES),
        runs_per_day=4,
        hours=every(1, 84),
        fetch=msc_fetch("model_rdps/10km", "RDPS", "RLatLon0.09"),
        per_variable=True,
    ),
    "gdps": Model(
        "gdps",
        msc_variables(MSC_NAMES),
        runs_per_day=2,
        hours=every(3, 240),
        fetch=msc_fetch("model_gdps/15km", "GDPS", "LatLon0.15"),
        per_variable=True,
    ),
    "gfs": Model(
        "gfs",
        (
            Variable("temperature", "K", 273.15, 20, select=(("shortName", "2t"),)),
            Variable("relative_humidity", "%", 0, 10, select=(("shortName", "2r"),)),
            Variable("wind_u", "m/s", 0, 10, select=(("shortName", "10u"),)),
            Variable("wind_v", "m/s", 0, 10, select=(("shortName", "10v"),)),
            Variable(
                "precipitation",
                "mm since the run started",
                0,
                10,
                # GFS also has the last few hours' total; the one from the start is wanted.
                select=(("shortName", "tp"), ("startStep", 0)),
                accumulated=True,
            ),
        ),
        runs_per_day=4,
        # GFS runs to 384 hours; ten days, as MoreCast uses, 3-hourly.
        hours=every(3, 240),
        fetch=gfs_fetch,
        per_variable=False,
        # NOMADS limits how fast one client may ask.
        threads=4,
    ),
    "ecmwf": Model(
        "ecmwf",
        (
            Variable("temperature", "K", 273.15, 20, select=(("shortName", "2t"),)),
            Variable("dewpoint", "K", 273.15, 20, select=(("shortName", "2d"),)),
            Variable("wind_u", "m/s", 0, 10, select=(("shortName", "10u"),)),
            Variable("wind_v", "m/s", 0, 10, select=(("shortName", "10v"),)),
            Variable(
                "precipitation",
                "m since the run started",
                0,
                10_000,
                select=(("shortName", "tp"),),
                accumulated=True,
            ),
        ),
        runs_per_day=4,
        hours=ecmwf_hours,
        fetch=ecmwf_fetch,
        per_variable=False,
        threads=4,
    ),
}


@dataclass(frozen=True)
class Variant:
    name: str
    # f32: the decoded values, lossless. i16: Open-Meteo style scaled int16, see Variable.
    # grib: the GRIB file's own packed integers with each field's scales, so lossless against
    # what the provider publishes.
    encoding: str
    compressor: str  # zstd or pcodec
    layout: str  # point: small tiles of every hour; map: one whole field per hour

    @property
    def int16(self) -> bool:
        return self.encoding == "i16"


VARIANTS = (
    Variant("f32-zstd-point", "f32", compressor="zstd", layout="point"),
    Variant("f32-pcodec-point", "f32", compressor="pcodec", layout="point"),
    Variant("i16-zstd-point", "i16", compressor="zstd", layout="point"),
    Variant("i16-pcodec-point", "i16", compressor="pcodec", layout="point"),
    Variant("i16-pcodec-map", "i16", compressor="pcodec", layout="map"),
    Variant("grib-pcodec-point", "grib", compressor="pcodec", layout="point"),
)

# A GRIB2 field's values are stored as integers X, with value = (R + X * 2**E) / 10**D. R, E and
# D are the field's reference value, binary scale and decimal scale, and can differ by hour.
GRIB_SCALES = {"reference": "float64", "binary_scale": "int16", "decimal_scale": "int16"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--model", choices=sorted(MODELS), default="hrdps")
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        help="model run as YYYY-MM-DDTHH; repeatable. The MSC datamart keeps about a day.",
    )
    parser.add_argument("--hours", type=int, help="last forecast hour to keep; all if not given")
    parser.add_argument(
        "--variant",
        action="append",
        choices=[variant.name for variant in VARIANTS],
        help="variants to write; all if not given",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path(os.environ.get("TMPDIR", "/tmp")) / "model_grid_icechunk_spike",
        help="downloads are kept here, and local stores written here",
    )
    parser.add_argument("--s3-prefix", help="write to the object store under this prefix")
    parser.add_argument("--no-conditional-writes", action="store_true")
    parser.add_argument("--points", type=int, default=20, help="point series to time")
    parser.add_argument(
        "--recent-cycle",
        type=int,
        metavar="RUNS",
        help="instead of the variants, try the `recent` store's cycle with the first run: add it "
        "as this many runs, each its own group, delete the older half, expire snapshots and "
        "garbage collect, measuring the store after each step",
    )
    return parser.parse_args()


# --- Reading the GRIB files -------------------------------------------------------------------


def find_message(grib, select: tuple) -> int | None:
    """The next message in an open file whose keys match `select`, or None."""
    while (handle := eccodes.codes_grib_new_from_file(grib)) is not None:
        if all(
            eccodes.codes_is_defined(handle, key) and eccodes.codes_get(handle, key) == value
            for key, value in select
        ):
            return handle
        eccodes.codes_release(handle)
    return None


def read_field(path: Path, select: tuple) -> tuple[np.ndarray, dict] | None:
    """The selected field as (Nj, Ni) float64 and its GRIB packing scales, or None if the file
    has no such field."""
    with open(path, "rb") as grib:
        handle = find_message(grib, select)
        if handle is None:
            return None
        try:
            nj, ni = eccodes.codes_get(handle, "Nj"), eccodes.codes_get(handle, "Ni")
            values = eccodes.codes_get_values(handle).reshape(nj, ni)
            scales = {
                "reference": eccodes.codes_get(handle, "referenceValue"),
                "binary_scale": eccodes.codes_get(handle, "binaryScaleFactor"),
                "decimal_scale": eccodes.codes_get(handle, "decimalScaleFactor"),
            }
        finally:
            eccodes.codes_release(handle)
    return values, scales


def grib_integers(values: np.ndarray, scales: dict) -> np.ndarray:
    """The integers the GRIB file stored for `values`. Decoding them gives `values` back."""
    unrounded = (values * 10.0 ** scales["decimal_scale"] - scales["reference"]) / 2.0 ** scales[
        "binary_scale"
    ]
    integers = np.rint(unrounded)
    # Each value sits on the field's grid of steps, to within float64 rounding, and decodes to
    # the same float32 (see grib_precision_check.py).
    if np.abs(unrounded - integers).max() > 1e-6 or not np.array_equal(
        decode_grib(integers, scales).astype(np.float32), values.astype(np.float32)
    ):
        raise ValueError("the field does not round-trip through its GRIB integers")
    return integers.astype(np.int32)


def decode_grib(integers: np.ndarray, scales: dict) -> np.ndarray:
    return (scales["reference"] + integers * 2.0 ** scales["binary_scale"]) / 10.0 ** scales[
        "decimal_scale"
    ]


def bc_crop(path: Path, select: tuple) -> tuple[slice, slice, np.ndarray, np.ndarray]:
    """The grid rows and columns covering BC, and their latitudes and longitudes."""
    with open(path, "rb") as grib:
        handle = find_message(grib, select)
        try:
            nj, ni = eccodes.codes_get(handle, "Nj"), eccodes.codes_get(handle, "Ni")
            lat = eccodes.codes_get_array(handle, "latitudes").reshape(nj, ni)
            lon = eccodes.codes_get_array(handle, "longitudes").reshape(nj, ni)
        finally:
            eccodes.codes_release(handle)
    lon = np.where(lon > 180, lon - 360, lon)
    inside = (
        (lat >= BC["lat"][0])
        & (lat <= BC["lat"][1])
        & (lon >= BC["lon"][0])
        & (lon <= BC["lon"][1])
    )
    rows = np.flatnonzero(inside.any(axis=1))
    cols = np.flatnonzero(inside.any(axis=0))
    y, x = slice(rows[0], rows[-1] + 1), slice(cols[0], cols[-1] + 1)
    return y, x, lat[y, x].astype(np.float32), lon[y, x].astype(np.float32)


def load_run(
    model: Model, run: datetime, hours: list[int], folder: Path, packed: bool
) -> tuple[dict, dict, dict, int]:
    """Download a run and return {variable: (hours, y, x) float32}, the same as GRIB integers
    with their scales if `packed`, the crop's coordinates and the bytes of GRIB downloaded."""
    if model.per_variable:
        wanted = [
            (variable, hour)
            for variable in model.variables
            for hour in hours
            # MSC publishes no accumulated precipitation for hour 0.
            if not (variable.accumulated and hour == 0)
        ]
    else:
        wanted = [(None, hour) for hour in hours]
    started = time.perf_counter()
    with ThreadPoolExecutor(model.threads) as pool:
        paths = list(pool.map(lambda item: model.fetch(run, item[1], item[0], folder), wanted))
    grib_bytes = sum(path.stat().st_size for path in set(paths))
    print(
        f"  downloaded {len(set(paths))} files, {grib_bytes / 1e6:.0f} MB, "
        f"{time.perf_counter() - started:.0f}s"
    )

    first = model.variables[0]
    y, x, lat, lon = bc_crop(paths[0], first.select)
    shape = (len(hours), y.stop - y.start, x.stop - x.start)
    # Where an accumulated variable has no field at hour 0: zeros, which zero scales decode to.
    fields = {v.name: np.zeros(shape, np.float32) for v in model.variables}
    integers = {
        v.name: {
            "integers": np.zeros(shape, np.int32),
            **{name: np.zeros(len(hours), kind) for name, kind in GRIB_SCALES.items()},
        }
        for v in model.variables
        if packed
    }
    for (variable, hour), path in zip(wanted, paths):
        for v in [variable] if variable else model.variables:
            field = read_field(path, v.select)
            if field is None:
                if v.accumulated and hour == 0:
                    continue
                raise ValueError(f"{path.name} has no {v.name} field")
            values, scales = field
            index = hours.index(hour)
            fields[v.name][index] = values[y, x]
            if packed:
                stored = integers[v.name]
                stored["integers"][index] = grib_integers(values, scales)[y, x]
                for name in GRIB_SCALES:
                    stored[name][index] = scales[name]
    return fields, integers, {"latitude": lat, "longitude": lon}, grib_bytes


# --- Writing the stores -----------------------------------------------------------------------


def storage(args: argparse.Namespace, variant: Variant | str) -> icechunk.Storage:
    """The store of a variant, or of any other name under the model."""
    name = variant if isinstance(variant, str) else variant.name
    if not args.s3_prefix:
        return icechunk.local_filesystem_storage(str(args.work_dir / "stores" / args.model / name))
    # Icechunk's AWS SDK checks response checksums and sends request checksums by default. ECS
    # answers a conditional GET with 304 and the object's checksum but no body, which fails the
    # check ("expected body checksum to be ... but it was 00000000"). As with botocore (see the
    # aiobotocore pin), only do either when an operation requires it. The SDK reads these when
    # the client is built.
    os.environ.setdefault("AWS_RESPONSE_CHECKSUM_VALIDATION", "when_required")
    os.environ.setdefault("AWS_REQUEST_CHECKSUM_CALCULATION", "when_required")
    return icechunk.s3_storage(
        bucket=os.environ["OBJECT_STORE_BUCKET"],
        prefix=f"{args.s3_prefix}/{args.model}/{name}",
        endpoint_url=f"https://{os.environ['OBJECT_STORE_SERVER']}",
        access_key_id=os.environ["OBJECT_STORE_USER_ID"],
        secret_access_key=os.environ["OBJECT_STORE_SECRET"],
        region="us-east-1",
        force_path_style=True,
    )


def repository(args: argparse.Namespace, variant: Variant | str) -> icechunk.Repository:
    config = icechunk.RepositoryConfig.default()
    if args.no_conditional_writes:
        config.storage = icechunk.StorageSettings(
            unsafe_use_conditional_update=False, unsafe_use_conditional_create=False
        )
    return icechunk.Repository.open_or_create(storage(args, variant), config=config)


def codecs(variant: Variant, variable: Variable) -> dict:
    if variant.encoding == "grib":
        return {"filters": None, "serializer": PCodec(level=8), "compressors": None}
    filters = []
    if variant.int16:
        filters.append(
            FixedScaleOffset(
                offset=variable.offset, scale=variable.scale, dtype="<f4", astype="<i2"
            )
        )
    if variant.compressor == "pcodec":
        # pcodec finds the deltas itself.
        return {"filters": filters, "serializer": PCodec(level=8), "compressors": None}
    if variant.int16:
        # Neighbouring cells along x differ by little, so their differences compress better.
        filters.append(Delta(dtype="<i2"))
    return {"filters": filters, "compressors": ZstdCodec(level=3)}


def chunking(variant: Variant, hours: int, ny: int, nx: int) -> dict:
    if variant.layout == "map":
        # A chunk is one hour's whole field; a shard is the whole run.
        return {"chunks": (1, 1, ny, nx), "shards": (1, hours, ny, nx)}

    def whole(n: int) -> int:
        return -(-n // POINT_CHUNK) * POINT_CHUNK

    # A chunk is every hour of a 64 x 64 tile; a shard is the whole run.
    return {
        "chunks": (1, hours, POINT_CHUNK, POINT_CHUNK),
        "shards": (1, hours, whole(ny), whole(nx)),
    }


def write_run(
    repo: icechunk.Repository,
    model: Model,
    variant: Variant,
    run: datetime,
    hours: list[int],
    fields: dict,
    integers: dict,
    coordinates: dict,
) -> float | None:
    """Append one run as one commit. Returns the seconds it took, or None if the store already
    has the run."""
    started = time.perf_counter()
    session = repo.writable_session("main")
    root = zarr.open_group(session.store, mode="a")
    ny, nx = coordinates["latitude"].shape
    grib = variant.encoding == "grib"
    if "run_time" not in root:
        root.create_array("run_time", shape=(0,), chunks=(1024,), dtype="int64")
        root.create_array("forecast_hour", data=np.array(hours, np.int16))
        for name, values in coordinates.items():
            root.create_array(name, data=values, compressors=ZstdCodec(level=3))
        for variable in model.variables:
            root.create_array(
                variable.name,
                shape=(0, len(hours), ny, nx),
                dtype="int32" if grib else "float32",
                # Zarr pads the chunks at the crop's edges with the fill value before encoding.
                # NaN has no int16, so a scaled array uses its offset, which encodes as 0.
                fill_value=0 if grib else variable.offset if variant.int16 else float("nan"),
                dimension_names=("run", "hour", "y", "x"),
                attributes={"units": variable.units, "scale": variable.scale},
                **chunking(variant, len(hours), ny, nx),
                **codecs(variant, variable),
            )
            if grib:
                for name, kind in GRIB_SCALES.items():
                    root.create_array(
                        f"{variable.name}_{name}",
                        shape=(0, len(hours)),
                        chunks=(256, len(hours)),
                        dtype=kind,
                        dimension_names=("run", "hour"),
                    )
    if root["forecast_hour"].shape[0] != len(hours):
        raise ValueError(
            f"the store keeps {root['forecast_hour'].shape[0]} hours a run, this run "
            f"{len(hours)}: use another --s3-prefix or --work-dir"
        )
    run_times = root["run_time"]
    if int(run.timestamp()) in run_times[:]:
        return None
    index = run_times.shape[0]
    run_times.resize((index + 1,))
    run_times[index] = int(run.timestamp())
    for variable in model.variables:
        array = root[variable.name]
        array.resize((index + 1, *array.shape[1:]))
        if not grib:
            array[index] = fields[variable.name]
            continue
        stored = integers[variable.name]
        array[index] = stored["integers"]
        for name in GRIB_SCALES:
            scale = root[f"{variable.name}_{name}"]
            scale.resize((index + 1, scale.shape[1]))
            scale[index] = stored[name]
    session.commit(f"{model.name.upper()} run {run:%Y-%m-%dT%H}Z")
    return time.perf_counter() - started


# --- Measuring --------------------------------------------------------------------------------


def stored_bytes(args: argparse.Namespace, variant: Variant | str) -> tuple[int, int]:
    """Bytes and objects the variant's (or named) store holds."""
    name = variant if isinstance(variant, str) else variant.name
    if not args.s3_prefix:
        folder = args.work_dir / "stores" / args.model / name
        files = [p for p in folder.rglob("*") if p.is_file()]
        return sum(p.stat().st_size for p in files), len(files)
    client = boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['OBJECT_STORE_SERVER']}",
        aws_access_key_id=os.environ["OBJECT_STORE_USER_ID"],
        aws_secret_access_key=os.environ["OBJECT_STORE_SECRET"],
        region_name="us-east-1",
    )
    size = count = 0
    pages = client.get_paginator("list_objects_v2").paginate(
        Bucket=os.environ["OBJECT_STORE_BUCKET"],
        Prefix=f"{args.s3_prefix}/{args.model}/{name}/",
    )
    for page in pages:
        for item in page.get("Contents", []):
            size += item["Size"]
            count += 1
    return size, count


def timed_ms(read) -> float:
    started = time.perf_counter()
    read()
    return (time.perf_counter() - started) * 1000


def measure_reads(
    args,
    model: Model,
    variant: Variant,
    points: list[tuple[int, int]],
    run_time: datetime,
    source: dict,
) -> dict:
    """Read times for one run from a freshly opened repository, the largest error of each
    variable against the run's `source` values, and how many runs the store holds."""
    root = zarr.open_group(repository(args, variant).readonly_session("main").store, mode="r")
    run_times = root["run_time"][:]
    run = int(np.flatnonzero(run_times == int(run_time.timestamp()))[0])
    hours = root["forecast_hour"].shape[0]
    grib = variant.encoding == "grib"

    def read(name: str, *at) -> np.ndarray:
        """Values of a variable for this run at `at` (hour, y, x selections), decoded."""
        values = root[name][(run, *at)]
        if not grib:
            return values
        hour = at[0] if at else slice(None)
        scales = {s: root[f"{name}_{s}"][run, hour] for s in GRIB_SCALES}
        # The scales are per hour, so line them up with the hour axis of the values.
        if np.ndim(scales["reference"]):
            extra = (slice(None),) + (np.newaxis,) * (values.ndim - 1)
            scales = {s: v[extra] for s, v in scales.items()}
        return decode_grib(values, scales).astype(np.float32)

    names = [v.name for v in model.variables]
    # One point's forecast: every hour of every variable at one grid cell.
    point_ms = [
        timed_ms(lambda y=y, x=x: [read(name, slice(None), y, x) for name in names])
        for y, x in points
    ]
    # One map: a single hour of one variable over all of BC.
    map_ms = [timed_ms(lambda h=h: read(names[0], h)) for h in sorted({0, hours // 2, hours - 1})]
    errors = {name: float(np.nanmax(np.abs(read(name) - source[name]))) for name in names}
    return {"point_ms": point_ms, "map_ms": map_ms, "errors": errors, "runs": len(run_times)}


# --- The `recent` store's cycle ---------------------------------------------------------------

RECENT = "recent-check"


def recent_cycle(
    args, model: Model, run: datetime, hours: list[int], integers: dict, coordinates: dict
) -> int:
    """Add `run` as `args.recent_cycle` runs six hours apart, each its own group of GRIB
    integers, then delete the older half, expire snapshots and garbage collect. Prints the
    store's size after each step and checks the kept runs read back exactly."""
    variant = next(v for v in VARIANTS if v.encoding == "grib")
    ny, nx = coordinates["latitude"].shape
    count = args.recent_cycle
    labels = [f"{run - timedelta(hours=6 * (count - 1 - i)):%Y-%m-%dT%H}" for i in range(count)]

    def report(step: str) -> None:
        size, objects = stored_bytes(args, RECENT)
        print(f"  {step:44s} {size / 1e6:8.1f} MB {objects:6d} objects")

    print(f"Recent cycle: {count} runs of {model.name.upper()} as GRIB integers")
    repo = repository(args, RECENT)
    try:
        existing = list(zarr.open_group(repo.readonly_session("main").store, mode="r"))
    except zarr.errors.GroupNotFoundError:
        # A new repository has no root group yet.
        existing = []
    if existing:
        print("  the store is not empty: use another --s3-prefix or --work-dir")
        return 1
    chunks = chunking(variant, len(hours), ny, nx)
    for label in labels:
        session = repo.writable_session("main")
        group = zarr.open_group(session.store, mode="a").create_group(label)
        for variable in model.variables:
            stored = integers[variable.name]
            array = group.create_array(
                variable.name,
                shape=(len(hours), ny, nx),
                dtype="int32",
                fill_value=0,
                dimension_names=("hour", "y", "x"),
                chunks=chunks["chunks"][1:],
                shards=chunks["shards"][1:],
                **codecs(variant, variable),
            )
            array[:] = stored["integers"]
            for name in GRIB_SCALES:
                group.create_array(f"{variable.name}_{name}", data=stored[name])
        session.commit(f"add {label}")
        report(f"added {label}")

    deleted, kept = labels[: count // 2], labels[count // 2 :]
    session = repo.writable_session("main")
    root = zarr.open_group(session.store, mode="a")
    for label in deleted:
        del root[label]
    session.commit(f"delete {', '.join(deleted)}")
    report(f"deleted {', '.join(deleted)}")

    # Only the newest snapshot is kept: the deleted runs are in none of what survives.
    cutoff = datetime.now(UTC)
    expired = repo.expire_snapshots(older_than=cutoff)
    report(f"expired {len(expired)} snapshots")
    summary = repo.garbage_collect(delete_object_older_than=cutoff)
    report("garbage collected")
    print(
        f"  garbage collection deleted {summary.chunks_deleted} chunks, "
        f"{summary.manifests_deleted} manifests, {summary.snapshots_deleted} snapshots, "
        f"{summary.transaction_logs_deleted} transaction logs, "
        f"{summary.bytes_deleted / 1e6:.1f} MB; delete errors {summary.delete_errors}, "
        f"failed to delete {summary.objects_failed_to_delete}"
    )

    root = zarr.open_group(repository(args, RECENT).readonly_session("main").store, mode="r")
    present = sorted(root.group_keys())
    exact = all(
        np.array_equal(root[label][v.name][:], integers[v.name]["integers"])
        for label in kept
        for v in model.variables
    )
    print(f"  runs in the store: {', '.join(present)}; kept runs read back exactly: {exact}")
    ok = present == kept and exact and not summary.objects_failed_to_delete
    print("  cycle " + ("worked" if ok else "FAILED"))
    return 0 if ok else 1


def main() -> int:
    args = parse_args()
    model = MODELS[args.model]
    runs = [datetime.fromisoformat(run + ":00+00:00") for run in args.run]
    variants = [v for v in VARIANTS if not args.variant or v.name in args.variant]
    downloads = args.work_dir / "grib" / model.name
    downloads.mkdir(parents=True, exist_ok=True)

    write_seconds = {variant.name: [] for variant in variants}
    grib_bytes = raw_bytes = 0
    loaded = []
    for run in runs:
        hours = [h for h in model.hours(run.hour) if args.hours is None or h <= args.hours]
        print(f"{model.name.upper()} run {run:%Y-%m-%dT%H}Z, {len(hours)} hours to {hours[-1]}")
        try:
            packed = args.recent_cycle or any(v.encoding == "grib" for v in variants)
            fields, integers, coordinates, grib = load_run(model, run, hours, downloads, packed)
        except (urllib.error.HTTPError, FileNotFoundError) as error:
            if isinstance(error, urllib.error.HTTPError) and error.code != 404:
                raise
            # A run is published hour by hour over several hours, and kept for a while.
            print(f"  skipped: not all of it is published ({error})")
            continue
        loaded.append(run)
        if args.recent_cycle:
            return recent_cycle(args, model, run, hours, integers, coordinates)
        grib_bytes += grib
        raw_bytes += sum(values.nbytes for values in fields.values())
        for variant in variants:
            seconds = write_run(
                repository(args, variant),
                model,
                variant,
                run,
                hours,
                fields,
                integers,
                coordinates,
            )
            if seconds is None:
                print(f"  {variant.name} already has it")
                continue
            write_seconds[variant.name].append(seconds)
            print(f"  wrote {variant.name} in {seconds:.1f}s")

    if not loaded:
        print("No run could be loaded, so there is nothing to measure.")
        return 1
    runs = loaded
    ny, nx = coordinates["latitude"].shape
    random.seed(1)
    points = [(random.randrange(ny), random.randrange(nx)) for _ in range(args.points)]
    per_run = raw_bytes / len(runs)
    print()
    print(
        f"{model.name.upper()}: {len(runs)} runs, {len(hours)} hours each, BC crop {ny} x {nx} "
        f"cells. Per run: GRIB {grib_bytes / len(runs) / 1e6:.0f} MB as downloaded, float32 "
        f"{per_run / 1e6:.0f} MB uncompressed. GB a year at {model.runs_per_day} runs a day."
    )
    print(
        f"{'variant':18s} {'MB/run':>7s} {'ratio':>6s} {'GB/yr':>6s} {'objects':>7s} "
        f"{'write s':>7s} {'point ms p50/p90':>17s} {'map ms':>7s}  largest error"
    )
    for variant in variants:
        size, objects = stored_bytes(args, variant)
        # The last run read is compared with its source values, which are still in memory.
        reads = measure_reads(args, model, variant, points, runs[-1], fields)
        point = sorted(reads["point_ms"])
        p90 = point[min(len(point) - 1, int(len(point) * 0.9))]
        errors = ", ".join(f"{name} {error:.3g}" for name, error in reads["errors"].items())
        # Per run of what the store holds, which can include runs from earlier invocations.
        stored_per_run = size / reads["runs"]
        writes = write_seconds[variant.name]
        print(
            f"{variant.name:18s} {stored_per_run / 1e6:7.1f} {per_run / stored_per_run:6.1f} "
            f"{stored_per_run * model.runs_per_day * 365 / 1e9:6.1f} {objects:7d} "
            f"{statistics.median(writes) if writes else float('nan'):7.1f} "
            f"{statistics.median(point):8.0f}/{p90:<8.0f} {statistics.median(reads['map_ms']):7.0f}"
            f"  {errors}"
        )
    # ru_maxrss is bytes on macOS and KiB on Linux.
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_mib = peak / 2**20 if os.uname().sysname == "Darwin" else peak / 1024
    print(f"\nPeak memory {peak_mib:.0f} MiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
