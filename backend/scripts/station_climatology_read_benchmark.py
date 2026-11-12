# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "numpy==2.5.4",
#     "pandas==3.1.1",
#     "pyarrow==26.0.1",
# ]
# ///
"""Benchmark for the climatology screen reads in docs/architecture/station-weather-storage-evaluation.md.

Tests whether a screen can compute climatology statistics on demand from raw station history,
rather than from a precomputed table. It writes one history file per station holding every year,
sorted by source then time with one row group per source per year, so one source's whole history
is a single contiguous byte range. It then times fetching and computing percentiles.

The dependencies above are not project dependencies, so run it with uv:

    uv run backend/scripts/station_climatology_read_benchmark.py --years 30

It runs on local disk only. Sizes and request counts carry over to object storage; latencies do
not. The floats are random at full precision, so sizes are an upper bound.
"""

import argparse
import shutil
import statistics
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
parser.add_argument("--years", type=int, default=30, help="years of history per station")
parser.add_argument("--group", type=int, default=25, help="stations in the group read")
parser.add_argument(
    "--out",
    type=Path,
    default=Path(tempfile.gettempdir()) / "station_climatology_read_benchmark",
    help="output directory; it is deleted and recreated on every run",
)
ARGS = parser.parse_args()

ROOT: Path = ARGS.out
YEARS = list(range(2026, 2026 + ARGS.years))
STATIONS = [7 * (i + 1) for i in range(ARGS.group)]
rng = np.random.default_rng(42)

WX = ["temperature", "relative_humidity", "wind_speed", "wind_direction", "precipitation"]
BIAS = [f"bias_adjusted_{c}" for c in WX]
MODELS = ["GDPS", "RDPS", "HRDPS", "GFS", "NAM", "ECMWF"]
THREE_HOURLY = sorted({*range(0, 24, 3), 20})
SOURCE_HOURS = {
    "hourly": {
        "OBSERVED": list(range(24)),
        "HRDPS": list(range(24)),
        "RDPS": list(range(24)),
        "GDPS": THREE_HOURLY,
        "ECMWF": THREE_HOURLY,
        "GFS": [18, 20, 21],
        "NAM": [18, 20, 21],
    },
    "daily": {s: [20] for s in ["OBSERVED", "FORECAST", *MODELS]},
}
TS = pa.timestamp("us", tz="UTC")
SCHEMA = pa.schema(
    [("source", pa.string()), ("timestamp", TS)] + [(c, pa.float32()) for c in WX + BIAS]
)
PERCENTILES = [0.1, 0.25, 0.5, 0.75, 0.9]


def history_file(res, station):
    return ROOT / f"resolution={res}" / f"station={station}" / "history.parquet"


def write_station(res, station):
    path = history_file(res, station)
    path.parent.mkdir(parents=True)
    with pq.ParquetWriter(path, SCHEMA, compression="zstd") as writer:
        for source, hours in SOURCE_HOURS[res].items():  # sorted by source, then time
            for year in YEARS:
                days = np.arange(f"{year}-01-01", f"{year + 1}-01-01", dtype="datetime64[D]")
                t = (days[:, None] + np.array(hours, dtype="timedelta64[h]")).ravel()
                n = len(t)
                cols = {
                    "source": pa.array([source] * n),
                    "timestamp": pa.array(t.astype("datetime64[us]"), TS),
                }
                n_var = 10 if source in MODELS else 5
                vals = rng.normal(20, 10, (n, n_var)).astype(np.float32)
                for k, c in enumerate(WX + BIAS):
                    cols[c] = vals[:, k] if k < n_var else pa.nulls(n, pa.float32())
                writer.write_table(pa.table(cols, schema=SCHEMA))  # one row group


def fetch(path, source=None):
    """Read a station's history, or one source's row groups. Returns (table, requests, bytes)."""
    pf = pq.ParquetFile(path)
    meta = pf.metadata
    if source is None:
        return pf.read(), 1, path.stat().st_size
    picked = [
        i
        for i in range(meta.num_row_groups)
        if meta.row_group(i).column(0).statistics.min == source
    ]
    assert picked == list(range(picked[0], picked[-1] + 1)), "a source must be one contiguous range"
    size = sum(
        meta.row_group(i).column(j).total_compressed_size
        for i in picked
        for j in range(meta.num_columns)
    )
    return pf.read_row_groups(picked), 2, size  # footer, then one contiguous range


def day_of_year_percentiles(df, window=7):
    """Percentiles of each weather variable per day of year, pooling +/- `window` days."""
    doy = df["timestamp"].dt.dayofyear.to_numpy()
    values = df[WX].to_numpy()
    out = np.empty((366, len(PERCENTILES), len(WX)), dtype=np.float32)
    for d in range(1, 367):
        dist = np.abs(doy - d)
        near = np.minimum(dist, 366 - dist) <= window
        out[d - 1] = np.quantile(values[near], PERCENTILES, axis=0)
    return out


def month_hour_percentiles(df):
    """Percentiles of each weather variable per month and hour of day."""
    keys = [df["timestamp"].dt.month, df["timestamp"].dt.hour]
    return df.groupby(keys)[WX].quantile(PERCENTILES)


def one_station_daily():
    tbl, req, size = fetch(history_file("daily", STATIONS[0]))
    df = tbl.to_pandas()
    t = time.perf_counter()
    for _, g in df.groupby("source"):
        day_of_year_percentiles(g)
    return req, size, tbl.num_rows, time.perf_counter() - t


def group_daily_one_source():
    frames, req, size = [], 0, 0
    for s in STATIONS:
        tbl, r, b = fetch(history_file("daily", s), "OBSERVED")
        frames.append(tbl.to_pandas())
        req, size = req + r, size + b
    t = time.perf_counter()
    for f in frames:  # each station's own climatology
        day_of_year_percentiles(f)
    pooled = pd.concat(frames)  # and the group's pooled climatology
    day_of_year_percentiles(pooled)
    return req, size, len(pooled), time.perf_counter() - t


def one_station_hourly_one_source():
    tbl, req, size = fetch(history_file("hourly", STATIONS[0]), "OBSERVED")
    df = tbl.to_pandas()
    t = time.perf_counter()
    month_hour_percentiles(df)
    return req, size, tbl.num_rows, time.perf_counter() - t


def group_hourly_one_source():
    frames, req, size = [], 0, 0
    for s in STATIONS:
        tbl, r, b = fetch(history_file("hourly", s), "OBSERVED")
        frames.append(tbl.to_pandas())
        req, size = req + r, size + b
    t = time.perf_counter()
    month_hour_percentiles(pd.concat(frames))
    return req, size, sum(len(f) for f in frames), time.perf_counter() - t


def timeit(fn):
    fn()
    total, compute = [], []
    for _ in range(3):
        t = time.perf_counter()
        req, size, rows, c = fn()
        total.append(time.perf_counter() - t)
        compute.append(c)
    tot, comp = statistics.median(total) * 1000, statistics.median(compute) * 1000
    return (
        f"requests={req:<4} fetched={size / 1e6:7.1f} MB  rows={rows:<10,} "
        f"read+decode={tot - comp:7.0f} ms  compute={comp:7.0f} ms"
    )


if __name__ == "__main__":
    shutil.rmtree(ROOT, ignore_errors=True)
    for station in STATIONS:
        write_station("daily", station)
        write_station("hourly", station)
    for res in SOURCE_HOURS:
        size = history_file(res, STATIONS[0]).stat().st_size
        print(f"{res} history file, {len(YEARS)} years, one station: {size / 1e6:.1f} MB")
    print(f"\n== reads: {len(YEARS)} years, group of {len(STATIONS)}, median of 3 ==")
    print("one station, daily, all sources, day-of-year percentiles")
    print("  ", timeit(one_station_daily))
    print("group, daily, one source, per-station and pooled day-of-year percentiles")
    print("  ", timeit(group_daily_one_source))
    print("one station, hourly, one source, month by hour-of-day percentiles")
    print("  ", timeit(one_station_hourly_one_source))
    print("group, hourly, one source, pooled month by hour-of-day percentiles")
    print("  ", timeit(group_hourly_one_source))
    shutil.rmtree(ROOT, ignore_errors=True)
