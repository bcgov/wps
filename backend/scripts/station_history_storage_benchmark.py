# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "numpy==2.5.4",
#     "pandas==3.1.1",
#     "pyarrow==26.0.1",
#     "zarr==3.4.2",
# ]
# ///
"""Benchmark for the station history layouts in docs/architecture/station-weather-storage-evaluation.md.

Writes synthetic station history (observations, forecasts and the newest model value per time, at
hourly and daily resolution) in three layouts, then times the MoreCast and climatology reads:

- by_time:    Parquet, one file per source per month, all stations inside
- by_station: Parquet, one file per station per year, all sources inside
- zarr:       one (time, station, variable) array per source

The dependencies above are not project dependencies, so run it with uv:

    uv run backend/scripts/station_history_storage_benchmark.py --years 5 --stations 300

It runs on local disk only. Sizes and object counts carry over to object storage; latencies do not.
The floats are random at full precision, so sizes are an upper bound.
"""

import argparse
import json
import shutil
import statistics
import tempfile
import time
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import zarr

parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
parser.add_argument("--years", type=int, default=5, help="years of history to generate")
parser.add_argument("--stations", type=int, default=300, help="number of weather stations")
parser.add_argument(
    "--out",
    type=Path,
    default=Path(tempfile.gettempdir()) / "station_history_storage_benchmark",
    help="output directory; it is deleted and recreated when data is (re)written",
)
parser.add_argument("--rewrite", action="store_true", help="regenerate data even if --out has it")
ARGS = parser.parse_args()

ROOT: Path = ARGS.out
N_STATIONS: int = ARGS.stations
YEARS = list(range(2026, 2026 + ARGS.years))
STATIONS = np.arange(1, N_STATIONS + 1, dtype=np.int32) * 7
STATION_CHUNK = 25
rng = np.random.default_rng(42)

WX = ["temperature", "relative_humidity", "wind_speed", "wind_direction", "precipitation"]
BIAS = [f"bias_adjusted_{c}" for c in WX]
MODELS = ["GDPS", "RDPS", "HRDPS", "GFS", "NAM", "ECMWF"]
THREE_HOURLY = sorted({*range(0, 24, 3), 20})  # plus the interpolated 20:00 UTC row
# UTC hours of the day each source has a value for.
SOURCE_HOURS = {
    "hourly": {
        "OBSERVED": list(range(24)),
        "HRDPS": list(range(24)),
        "RDPS": list(range(24)),
        "GDPS": THREE_HOURLY,
        "ECMWF": THREE_HOURLY,
        "GFS": [18, 20, 21],  # the jobs only keep the hours around noon
        "NAM": [18, 20, 21],
    },
    "daily": {s: [20] for s in ["OBSERVED", "FORECAST", *MODELS]},
}
SCHEMA = pa.schema(
    [("station_code", pa.int32()), ("timestamp", pa.timestamp("us", tz="UTC"))]
    + [(c, pa.float32()) for c in WX + BIAS]
)


def times(hours, year):
    days = np.arange(f"{year}-01-01", f"{year + 1}-01-01", dtype="datetime64[D]")
    return (
        (days[:, None] + np.array(hours, dtype="timedelta64[h]")).ravel().astype("datetime64[us]")
    )


def to_table(t, cube):
    """Rows sorted by timestamp then station. cube is (time, station, variable)."""
    n = len(t) * N_STATIONS
    cols = {
        "station_code": np.tile(STATIONS, len(t)),
        "timestamp": pa.array(np.repeat(t, N_STATIONS), pa.timestamp("us", tz="UTC")),
    }
    for k, c in enumerate(WX + BIAS):
        cols[c] = cube[:, :, k].ravel() if k < cube.shape[2] else pa.nulls(n, pa.float32())
    return pa.table(cols, schema=SCHEMA)


def du(path):
    files = [p for p in Path(path).rglob("*") if p.is_file()]
    return sum(p.stat().st_size for p in files), len(files)


def write_all():
    shutil.rmtree(ROOT, ignore_errors=True)
    ROOT.mkdir(parents=True)
    root = zarr.open_group(zarr.storage.LocalStore(ROOT / "zarr"), mode="a")
    rows = dict.fromkeys(SOURCE_HOURS, 0)
    for res, sources in SOURCE_HOURS.items():
        for year in YEARS:
            year_tables = []
            for source, hours in sources.items():
                t = times(hours, year)
                n_var = 10 if source in MODELS else 5
                cube = rng.normal(20, 10, (len(t), N_STATIONS, n_var)).astype(np.float32)
                tbl = to_table(t, cube)
                rows[res] += tbl.num_rows

                # by_time: one file per source per month
                d = ROOT / "by_time" / f"resolution={res}" / f"source={source}"
                d.mkdir(parents=True, exist_ok=True)
                month = t.astype("datetime64[M]")
                for m in np.unique(month):
                    idx = np.flatnonzero(month == m)
                    part = tbl.slice(idx[0] * N_STATIONS, len(idx) * N_STATIONS)
                    pq.write_table(part, d / f"{m}.parquet", compression="zstd")

                # zarr: one (time, station, variable) array per source
                tc = len(hours) * 30
                g = root.require_group(f"{res}/{source}")
                if "data" not in g:
                    g.create_array("time", shape=(0,), chunks=(100_000,), dtype="i8")
                    g.create_array(
                        "data",
                        shape=(0, N_STATIONS, n_var),
                        chunks=(tc, STATION_CHUNK, n_var),
                        dtype="f4",
                        compressors=zarr.codecs.ZstdCodec(level=3),
                    )
                n0 = g["time"].shape[0]
                g["time"].resize((n0 + len(t),))
                g["time"][n0:] = t.astype("i8")
                g["data"].resize((n0 + len(t), N_STATIONS, n_var))
                g["data"][n0:] = cube

                year_tables.append(tbl.append_column("source", pa.array([source] * tbl.num_rows)))

            # by_station: one file per station per year, all sources, sorted by source then time
            allsrc = pa.concat_tables(year_tables)
            order = pc.sort_indices(
                allsrc,
                [
                    ("station_code", "ascending"),
                    ("source", "ascending"),
                    ("timestamp", "ascending"),
                ],
            )
            allsrc = allsrc.take(order)
            _, counts = np.unique(allsrc["station_code"].to_numpy(), return_counts=True)
            off = 0
            for code, cnt in zip(STATIONS.tolist(), counts.tolist(), strict=True):
                d = ROOT / "by_station" / f"resolution={res}" / f"station={code}"
                d.mkdir(parents=True, exist_ok=True)
                pq.write_table(allsrc.slice(off, cnt), d / f"{year}.parquet", compression="zstd")
                off += cnt
    (ROOT / "write.json").write_text(
        json.dumps({"rows": rows, "years": len(YEARS), "stations": N_STATIONS})
    )


# ---------------------------------------------------------------- reads
ONE_STATION = int(STATIONS[min(137, N_STATIONS - 1)])
GROUP = slice(50, 75) if N_STATIONS >= 75 else slice(0, min(25, N_STATIONS))  # "a fire centre"
GROUP_CODES = STATIONS[GROUP].tolist()


def ts(x):
    return pa.scalar(np.datetime64(x, "us").astype("datetime64[us]").item(), pa.timestamp("us"))


def tsz(x):
    return pc.assume_timezone(ts(x), "UTC")


def between(lo, hi):
    return (ds.field("timestamp") >= tsz(lo)) & (ds.field("timestamp") < tsz(hi))


def by_time_files(res, months):
    base = ROOT / "by_time" / f"resolution={res}"
    return [str(base / f"source={s}" / f"{m}.parquet") for s in SOURCE_HOURS[res] for m in months]


def by_station_files(res, codes, years):
    base = ROOT / "by_station" / f"resolution={res}"
    return [str(base / f"station={c}" / f"{y}.parquet") for c in codes for y in years]


def scan(files, flt):
    return ds.dataset(files, format="parquet").to_table(filter=flt).num_rows, len(files)


def zread(res, time_ranges, stations):
    """Read [lo, hi) time ranges for a station slice from every source's array."""
    root = zarr.open_group(zarr.storage.LocalStore(ROOT / "zarr"), mode="r")
    n = chunks = 0
    for source in SOURCE_HOURS[res]:
        g = root[f"{res}/{source}"]
        t, data = g["time"][:], g["data"]
        tc = data.chunks[0]
        s0, s1 = stations.start or 0, stations.stop or N_STATIONS
        for lo, hi in time_ranges:
            a = int(np.searchsorted(t, np.datetime64(lo, "us").astype("i8")))
            b = int(np.searchsorted(t, np.datetime64(hi, "us").astype("i8")))
            if b > a:
                n += data[a:b, stations].shape[0] * (s1 - s0)
                chunks += ((b - 1) // tc - a // tc + 1) * (
                    (s1 - 1) // STATION_CHUNK - s0 // STATION_CHUNK + 1
                )
    return n, chunks


ALL_MONTHS = [f"{y}-{m:02d}" for y in YEARS for m in range(1, 13)]
ALL_TIME = [(f"{YEARS[0]}-01-01", f"{YEARS[-1] + 1}-01-01")]
JULY_WINDOWS = [(f"{y}-07-01", f"{y}-07-15") for y in YEARS]
MORECAST = [(f"{YEARS[-1]}-07-10", f"{YEARS[-1]}-07-15")]
i1 = int(np.where(STATIONS == ONE_STATION)[0][0])


def or_ranges(ranges):
    flt = between(*ranges[0])
    for r in ranges[1:]:
        flt = flt | between(*r)
    return flt


def queries():
    one = ds.field("station_code") == ONE_STATION
    grp = ds.field("station_code").isin(GROUP_CODES)
    july = [f"{y}-07" for y in YEARS]
    return [
        (
            "C1 one station, hourly, all sources, all years",
            lambda: scan(by_time_files("hourly", ALL_MONTHS), one),
            lambda: scan(by_station_files("hourly", [ONE_STATION], YEARS), None),
            lambda: zread("hourly", ALL_TIME, slice(i1, i1 + 1)),
        ),
        (
            "C2 one station, daily, all sources, all years",
            lambda: scan(by_time_files("daily", ALL_MONTHS), one),
            lambda: scan(by_station_files("daily", [ONE_STATION], YEARS), None),
            lambda: zread("daily", ALL_TIME, slice(i1, i1 + 1)),
        ),
        (
            "C3 25 stations, hourly, 1-14 July of every year",
            lambda: scan(by_time_files("hourly", july), grp & or_ranges(JULY_WINDOWS)),
            lambda: scan(by_station_files("hourly", GROUP_CODES, YEARS), or_ranges(JULY_WINDOWS)),
            lambda: zread("hourly", JULY_WINDOWS, GROUP),
        ),
        (
            "C4 MoreCast: all stations, daily, 5 days, all sources",
            lambda: scan(by_time_files("daily", [f"{YEARS[-1]}-07"]), or_ranges(MORECAST)),
            lambda: scan(
                by_station_files("daily", STATIONS.tolist(), YEARS[-1:]), or_ranges(MORECAST)
            ),
            lambda: zread("daily", MORECAST, slice(0, N_STATIONS)),
        ),
    ]


def timeit(fn):
    fn()
    samples = []
    for _ in range(5):
        t = time.perf_counter()
        res = fn()
        samples.append(time.perf_counter() - t)
    return f"{statistics.median(samples) * 1000:8.1f} ms  rows={res[0]:<9,} objects={res[1]}"


def report():
    w = json.loads((ROOT / "write.json").read_text())
    if (w["years"], w["stations"]) != (len(YEARS), N_STATIONS):
        raise SystemExit(
            f"{ROOT} holds {w['years']} years, {w['stations']} stations; pass --rewrite"
        )
    print(f"years={len(YEARS)} stations={N_STATIONS} rows={w['rows']}")
    print("\n== storage ==")
    for layout in ["by_time", "by_station", "zarr"]:
        for res in SOURCE_HOURS:
            sub = ROOT / layout / (res if layout == "zarr" else f"resolution={res}")
            b, n = du(sub)
            print(
                f"{layout:11s} {res:7s} {b / 1e6:9.1f} MB  {n:6d} objects  {b / w['rows'][res]:5.1f} B/row"
            )
    print("\n== reads: median of 5 ==")
    for name, by_time, by_station, zarr_read in queries():
        print(name)
        print("   by_time    ", timeit(by_time))
        print("   by_station ", timeit(by_station))
        print("   zarr       ", timeit(zarr_read))


if __name__ == "__main__":
    if not (ROOT / "write.json").exists() or ARGS.rewrite:
        write_all()
    report()
