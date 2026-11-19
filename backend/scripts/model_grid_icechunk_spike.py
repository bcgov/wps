# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "boto3==1.40.61",
#     "eccodes==2.48.0",
#     "icechunk==2.3.1",
#     "numcodecs[pcodec]==0.17.1",
#     "numpy==2.3.5",
#     "zarr==3.4.2",
# ]
# ///
"""Spike: store HRDPS model grids, cropped to BC, as Zarr 3 in Icechunk, and measure the cost.

The model jobs keep only the values at weather stations. This tries keeping each run's whole grid
as well, alongside them, to answer: how many bytes a run takes (and so a year), how long a point's
forecast and a whole map take to read back, and what writing a run costs. Nothing else reads or
writes these stores.

It downloads HRDPS runs from the MSC datamart (which keeps about a day), crops each field to BC
and writes the same runs once per variant: lossless float32, or Open-Meteo style scaled int16
(round((value - offset) * scale)), compressed with zstd or pcodec, in chunks laid out for point
reads or for map reads. Each run is one Icechunk commit, and runs are appended along a `run` axis.

The dependencies above are not project dependencies, so run it with uv, from ./backend:

    uv run scripts/model_grid_icechunk_spike.py --run 2026-11-19T12 --run 2026-11-19T18

That writes to local disk. To write to our object store, set OBJECT_STORE_SERVER,
OBJECT_STORE_USER_ID, OBJECT_STORE_SECRET and OBJECT_STORE_BUCKET as the deployments do and add
`--s3-prefix dev/zarr-spike` (any prefix outside the station weather tables). Add
`--no-conditional-writes` if the store rejects Icechunk's conditional writes. Delete the prefix
afterwards. Read times are only meaningful against the object store.

Design: docs/architecture/station-weather-storage-evaluation.md ("Store the model grids")
"""

import argparse
import os
import random
import resource
import statistics
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import boto3
import eccodes
import icechunk
import numpy as np
import zarr
from zarr.codecs import ZstdCodec
from zarr.codecs.numcodecs import Delta, FixedScaleOffset, PCodec

DATAMART = "https://dd.weather.gc.ca/today/model_hrdps/continental/2.5km"
# Generous BC bounds; the rotated grid makes the crop a little larger.
BC = {"lat": (48.2, 60.1), "lon": (-139.2, -114.0)}
POINT_CHUNK = 64  # cells per side of a point-layout chunk


@dataclass(frozen=True)
class Variable:
    name: str
    layer: str  # as in the datamart file name
    units: str
    # Scaled int16: round((value - offset) * scale), so values are kept to 1 / scale.
    offset: float
    scale: float


# Units as the GRIB files have them. Scales follow Open-Meteo's (temperature 0.05, wind 0.1,
# precipitation 0.1), with relative humidity at 0.1 % to match the station data.
VARIABLES = (
    Variable("temperature", "TMP_AGL-2m", "K", 273.15, 20),
    Variable("relative_humidity", "RH_AGL-2m", "%", 0, 10),
    Variable("wind_speed", "WIND_AGL-10m", "m/s", 0, 10),
    Variable("wind_direction", "WDIR_AGL-10m", "degrees", 0, 1),
    Variable("precipitation", "APCP_Sfc", "mm since the run started", 0, 10),
)


@dataclass(frozen=True)
class Variant:
    name: str
    # f32: the decoded values, lossless. i16: Open-Meteo style scaled int16, see Variable.
    # grib: the GRIB file's own packed integers with each field's scales, so lossless against
    # what MSC publishes.
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
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        help="model run as YYYY-MM-DDTHH (00, 06, 12 or 18 UTC) from the last day; repeatable",
    )
    parser.add_argument("--hours", type=int, default=48, help="last forecast hour to keep")
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
    return parser.parse_args()


# --- Reading the GRIB files -------------------------------------------------------------------


def file_url(run: datetime, hour: int, variable: Variable) -> str:
    return (
        f"{DATAMART}/{run:%H}/{hour:03d}/"
        f"{run:%Y%m%dT%H}Z_MSC_HRDPS_{variable.layer}_RLatLon0.0225_PT{hour:03d}H.grib2"
    )


def download(url: str, folder: Path, attempts: int = 3) -> Path:
    path = folder / url.rsplit("/", 1)[1]
    partial = path.with_suffix(".part")
    for attempt in range(1, attempts + 1):
        if path.exists():
            break
        try:
            urllib.request.urlretrieve(url, partial)
            partial.rename(path)
        except urllib.error.URLError:
            # The datamart sometimes ends a download early.
            if attempt == attempts:
                raise
            time.sleep(attempt)
    return path


def read_field(path: Path) -> tuple[np.ndarray, dict]:
    """The file's first field as (Nj, Ni) float64, and its GRIB packing scales."""
    with open(path, "rb") as grib:
        handle = eccodes.codes_grib_new_from_file(grib)
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


def bc_crop(path: Path) -> tuple[slice, slice, np.ndarray, np.ndarray]:
    """The grid rows and columns covering BC, and their latitudes and longitudes."""
    with open(path, "rb") as grib:
        handle = eccodes.codes_grib_new_from_file(grib)
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
    run: datetime, hours: list[int], folder: Path, packed: bool
) -> tuple[dict, dict, dict, int]:
    """Download a run and return {variable: (hours, y, x) float32}, the same as GRIB integers
    with their scales if `packed`, the crop's coordinates and the bytes of GRIB downloaded."""
    urls = [
        (variable, hour, file_url(run, hour, variable))
        for variable in VARIABLES
        for hour in hours
        # Accumulated precipitation has no file for hour 0.
        if not (variable.layer == "APCP_Sfc" and hour == 0)
    ]
    started = time.perf_counter()
    with ThreadPoolExecutor(8) as pool:
        paths = list(pool.map(lambda item: download(item[2], folder), urls))
    grib_bytes = sum(path.stat().st_size for path in paths)
    print(
        f"  downloaded {len(paths)} files, {grib_bytes / 1e6:.0f} MB, {time.perf_counter() - started:.0f}s"
    )

    y, x, lat, lon = bc_crop(paths[0])
    shape = (len(hours), y.stop - y.start, x.stop - x.start)
    # Nothing has accumulated at hour 0: zeros, which the zero scales also decode to.
    fields = {v.name: np.zeros(shape, np.float32) for v in VARIABLES}
    integers = {
        v.name: {
            "integers": np.zeros(shape, np.int32),
            **{name: np.zeros(len(hours), kind) for name, kind in GRIB_SCALES.items()},
        }
        for v in VARIABLES
        if packed
    }
    for (variable, hour, _), path in zip(urls, paths):
        values, scales = read_field(path)
        index = hours.index(hour)
        fields[variable.name][index] = values[y, x]
        if packed:
            stored = integers[variable.name]
            stored["integers"][index] = grib_integers(values, scales)[y, x]
            for name in GRIB_SCALES:
                stored[name][index] = scales[name]
    return fields, integers, {"latitude": lat, "longitude": lon}, grib_bytes


# --- Writing the stores -----------------------------------------------------------------------


def storage(args: argparse.Namespace, variant: Variant) -> icechunk.Storage:
    if not args.s3_prefix:
        return icechunk.local_filesystem_storage(str(args.work_dir / "stores" / variant.name))
    # Icechunk's AWS SDK checks response checksums and sends request checksums by default. ECS
    # answers a conditional GET with 304 and the object's checksum but no body, which fails the
    # check ("expected body checksum to be ... but it was 00000000"). As with botocore (see the
    # aiobotocore pin), only do either when an operation requires it. The SDK reads these when
    # the client is built.
    os.environ.setdefault("AWS_RESPONSE_CHECKSUM_VALIDATION", "when_required")
    os.environ.setdefault("AWS_REQUEST_CHECKSUM_CALCULATION", "when_required")
    return icechunk.s3_storage(
        bucket=os.environ["OBJECT_STORE_BUCKET"],
        prefix=f"{args.s3_prefix}/{variant.name}",
        endpoint_url=f"https://{os.environ['OBJECT_STORE_SERVER']}",
        access_key_id=os.environ["OBJECT_STORE_USER_ID"],
        secret_access_key=os.environ["OBJECT_STORE_SECRET"],
        region="us-east-1",
        force_path_style=True,
    )


def repository(args: argparse.Namespace, variant: Variant) -> icechunk.Repository:
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
    if "run_time" not in root:
        root.create_array("run_time", shape=(0,), chunks=(1024,), dtype="int64")
        root.create_array("forecast_hour", data=np.array(hours, np.int16))
        for name, values in coordinates.items():
            root.create_array(name, data=values, compressors=ZstdCodec(level=3))
        for variable in VARIABLES:
            grib = variant.encoding == "grib"
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
    run_times = root["run_time"]
    if int(run.timestamp()) in run_times[:]:
        return None
    index = run_times.shape[0]
    run_times.resize((index + 1,))
    run_times[index] = int(run.timestamp())
    for variable in VARIABLES:
        array = root[variable.name]
        array.resize((index + 1, *array.shape[1:]))
        if variant.encoding != "grib":
            array[index] = fields[variable.name]
            continue
        stored = integers[variable.name]
        array[index] = stored["integers"]
        for name in GRIB_SCALES:
            scale = root[f"{variable.name}_{name}"]
            scale.resize((index + 1, scale.shape[1]))
            scale[index] = stored[name]
    session.commit(f"HRDPS run {run:%Y-%m-%dT%H}Z")
    return time.perf_counter() - started


# --- Measuring --------------------------------------------------------------------------------


def stored_bytes(args: argparse.Namespace, variant: Variant) -> tuple[int, int]:
    """Bytes and objects the variant's store holds."""
    if not args.s3_prefix:
        files = [p for p in (args.work_dir / "stores" / variant.name).rglob("*") if p.is_file()]
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
        Bucket=os.environ["OBJECT_STORE_BUCKET"], Prefix=f"{args.s3_prefix}/{variant.name}/"
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
    args, variant: Variant, points: list[tuple[int, int]], run_time: datetime, source: dict
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

    # One point's forecast: every hour of every variable at one grid cell.
    point_ms = [
        timed_ms(lambda y=y, x=x: [read(v.name, slice(None), y, x) for v in VARIABLES])
        for y, x in points
    ]
    # One map: a single hour of one variable over all of BC.
    map_ms = [
        timed_ms(lambda h=h: read("temperature", h)) for h in sorted({0, hours // 2, hours - 1})
    ]
    errors = {v.name: float(np.nanmax(np.abs(read(v.name) - source[v.name]))) for v in VARIABLES}
    return {"point_ms": point_ms, "map_ms": map_ms, "errors": errors, "runs": len(run_times)}


def main() -> int:
    args = parse_args()
    runs = [datetime.fromisoformat(run + ":00+00:00") for run in args.run]
    hours = list(range(0, args.hours + 1))
    variants = [v for v in VARIANTS if not args.variant or v.name in args.variant]
    downloads = args.work_dir / "grib"
    downloads.mkdir(parents=True, exist_ok=True)

    write_seconds = {variant.name: [] for variant in variants}
    grib_bytes = raw_bytes = 0
    loaded = []
    for run in runs:
        print(f"Run {run:%Y-%m-%dT%H}Z")
        try:
            packed = any(variant.encoding == "grib" for variant in variants)
            fields, integers, coordinates, grib = load_run(run, hours, downloads, packed)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            # A run is published hour by hour over several hours, and kept for about a day.
            print(f"  skipped: not all of its files are on the datamart ({error.url})")
            continue
        loaded.append(run)
        grib_bytes += grib
        raw_bytes += sum(values.nbytes for values in fields.values())
        for variant in variants:
            seconds = write_run(
                repository(args, variant), variant, run, hours, fields, integers, coordinates
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
        f"{len(runs)} runs, hours 0-{args.hours}, BC crop {ny} x {nx} cells. Per run: GRIB "
        f"{grib_bytes / len(runs) / 1e6:.0f} MB (whole continental grid), float32 "
        f"{per_run / 1e6:.0f} MB uncompressed."
    )
    print(
        f"{'variant':18s} {'MB/run':>7s} {'ratio':>6s} {'GB/yr':>6s} {'objects':>7s} "
        f"{'write s':>7s} {'point ms p50/p90':>17s} {'map ms':>7s}  largest error"
    )
    for variant in variants:
        size, objects = stored_bytes(args, variant)
        # The last run read is compared with its source values, which are still in memory.
        reads = measure_reads(args, variant, points, runs[-1], fields)
        point = sorted(reads["point_ms"])
        p90 = point[min(len(point) - 1, int(len(point) * 0.9))]
        errors = ", ".join(f"{name} {error:.3g}" for name, error in reads["errors"].items())
        # Per run of what the store holds, which can include runs from earlier invocations.
        stored_per_run = size / reads["runs"]
        writes = write_seconds[variant.name]
        print(
            f"{variant.name:18s} {stored_per_run / 1e6:7.1f} {per_run / stored_per_run:6.1f} "
            # Four runs a day.
            f"{stored_per_run * 4 * 365 / 1e9:6.0f} {objects:7d} "
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
