# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "numpy==2.5.4",
#     "pyarrow==26.0.1",
# ]
# ///
"""Benchmark for the lead-aware layouts in docs/architecture/station-predictions-storage.md.

Writes one year of every model prediction at every lead, for two models, in two Parquet layouts,
then times climatology reads that choose a lead at read time:

- leads_by_station: one file per station per year, one row group per model per month
- leads_by_time:    one file per model per month, one row group per station

A reader uses the row group statistics to fetch only the row groups it needs, so each row group
read stands for one ranged GET on object storage.

Only HRDPS (hourly, 48 hours, 4 runs a day) and GDPS (3-hourly, 240 hours, 2 runs a day) are
generated, to keep the run short. The two layouts hold the same rows with different random values.

The dependencies above are not project dependencies, so run it with uv:

    uv run backend/scripts/station_leads_storage_benchmark.py --stations 300

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
import pyarrow.parquet as pq

parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
parser.add_argument("--stations", type=int, default=300, help="number of weather stations")
parser.add_argument(
    "--out",
    type=Path,
    default=Path(tempfile.gettempdir()) / "station_leads_storage_benchmark",
    help="output directory; it is deleted and recreated when data is (re)written",
)
parser.add_argument("--rewrite", action="store_true", help="regenerate data even if --out has it")
ARGS = parser.parse_args()

ROOT: Path = ARGS.out
N_STATIONS: int = ARGS.stations
YEAR = 2026
STATIONS = np.arange(1, N_STATIONS + 1, dtype=np.int32) * 7
rng = np.random.default_rng(42)

# model: (run hours of the day, forecast step hours)
MODELS = {
    "HRDPS": ([0, 6, 12, 18], list(range(49))),
    "GDPS": ([0, 12], list(range(0, 241, 3))),
}
VALUES = [
    "temperature",
    "relative_humidity",
    "wind_speed",
    "wind_direction",
    "precipitation",
    "bias_adjusted_temperature",
    "bias_adjusted_relative_humidity",
    "bias_adjusted_wind_speed",
    "bias_adjusted_wind_direction",
    "bias_adjusted_precipitation",
]
TS = pa.timestamp("us", tz="UTC")
SCHEMA = pa.schema(
    [
        ("station_code", pa.int32()),
        ("source", pa.string()),
        ("timestamp", TS),
        ("run_ts", TS),
        ("lead_hours", pa.int16()),
    ]
    + [(c, pa.float32()) for c in VALUES]
)


def base_rows(model):
    """Every (timestamp, run_ts, lead) one station has for a model in YEAR, sorted by time, lead."""
    run_hours, steps = MODELS[model]
    days = np.arange(f"{YEAR - 1}-12-20", f"{YEAR + 1}-01-01", dtype="datetime64[D]")
    runs = (days[:, None] + np.array(run_hours, dtype="timedelta64[h]")).ravel()
    lead = np.tile(np.array(steps, dtype=np.int16), len(runs))
    run_ts = np.repeat(runs, len(steps)).astype("datetime64[h]")
    valid = run_ts + lead.astype("timedelta64[h]")
    keep = (valid >= np.datetime64(f"{YEAR}-01-01")) & (valid < np.datetime64(f"{YEAR + 1}-01-01"))
    valid, run_ts, lead = valid[keep], run_ts[keep], lead[keep]
    order = np.lexsort((lead, valid))
    valid, run_ts, lead = valid[order], run_ts[order], lead[order]
    return valid.astype("datetime64[us]"), run_ts.astype("datetime64[us]"), lead


def table(station, model, valid, run_ts, lead):
    n = len(valid)
    cols = {
        "station_code": np.full(n, station, dtype=np.int32),
        "source": pa.array([model] * n),
        "timestamp": pa.array(valid, TS),
        "run_ts": pa.array(run_ts, TS),
        "lead_hours": lead,
    }
    vals = rng.normal(20, 10, (n, len(VALUES))).astype(np.float32)
    for k, c in enumerate(VALUES):
        cols[c] = vals[:, k]
    return pa.table(cols, schema=SCHEMA)


def write_all():
    shutil.rmtree(ROOT, ignore_errors=True)
    base = {m: base_rows(m) for m in MODELS}
    months = {m: base[m][0].astype("datetime64[M]") for m in MODELS}
    rows = 0

    # leads_by_station: one file per station, one row group per model per month
    for station in STATIONS.tolist():
        d = ROOT / "leads_by_station" / f"station={station}"
        d.mkdir(parents=True)
        with pq.ParquetWriter(d / f"{YEAR}.parquet", SCHEMA, compression="zstd") as writer:
            for model, (valid, run_ts, lead) in base.items():
                for m in np.unique(months[model]):
                    sel = months[model] == m
                    writer.write_table(table(station, model, valid[sel], run_ts[sel], lead[sel]))
                    rows += int(sel.sum())

    # leads_by_time: one file per model per month, one row group per station
    for model, (valid, run_ts, lead) in base.items():
        d = ROOT / "leads_by_time" / f"source={model}"
        d.mkdir(parents=True)
        for m in np.unique(months[model]):
            sel = months[model] == m
            with pq.ParquetWriter(d / f"{m}.parquet", SCHEMA, compression="zstd") as writer:
                for station in STATIONS.tolist():
                    writer.write_table(table(station, model, valid[sel], run_ts[sel], lead[sel]))

    (ROOT / "write.json").write_text(json.dumps({"rows": rows, "stations": N_STATIONS}))


# ---------------------------------------------------------------- reads
COL = {name: i for i, name in enumerate(SCHEMA.names)}
ONE_STATION = int(STATIONS[min(137, N_STATIONS - 1)])
GROUP = sorted(rng.choice(STATIONS, size=min(25, N_STATIONS), replace=False).tolist())  # scattered
WINDOW = (np.datetime64(f"{YEAR}-07-01", "us"), np.datetime64(f"{YEAR}-07-15", "us"))
LEAD = (18, 30)  # "the prediction made about a day ahead"


def stat(rg, name):
    s = rg.column(COL[name]).statistics
    return s.min, s.max


def compressed_size(rg):
    return sum(rg.column(i).total_compressed_size for i in range(rg.num_columns))


def read(files, want_row_group, flt):
    """Read only the row groups whose statistics pass, then filter rows."""
    n_rows = n_groups = n_bytes = 0
    for f in files:
        pf = pq.ParquetFile(f)
        meta = pf.metadata
        picked = [i for i in range(meta.num_row_groups) if want_row_group(meta.row_group(i))]
        if not picked:
            continue
        n_groups += len(picked)
        n_bytes += sum(compressed_size(meta.row_group(i)) for i in picked)
        n_rows += pf.read_row_groups(picked).filter(flt).num_rows
    return n_rows, len(files), n_groups, n_bytes


def in_window(rg):
    lo, hi = stat(rg, "timestamp")
    return np.datetime64(hi.replace(tzinfo=None), "us") >= WINDOW[0] and (
        np.datetime64(lo.replace(tzinfo=None), "us") < WINDOW[1]
    )


def lead_filter():
    return (pc.field("lead_hours") >= LEAD[0]) & (pc.field("lead_hours") <= LEAD[1])


def window_filter():
    lo = pa.scalar(WINDOW[0].item(), pa.timestamp("us")).cast(TS)
    hi = pa.scalar(WINDOW[1].item(), pa.timestamp("us")).cast(TS)
    return (pc.field("timestamp") >= lo) & (pc.field("timestamp") < hi)


def station_files(codes):
    return [ROOT / "leads_by_station" / f"station={c}" / f"{YEAR}.parquet" for c in codes]


def time_files(months):
    return [
        ROOT / "leads_by_time" / f"source={m}" / f"{YEAR}-{mo:02d}.parquet"
        for m in MODELS
        for mo in months
    ]


def queries():
    group = set(GROUP)
    return [
        (
            f"L1 one station, both models, whole year, lead {LEAD[0]}-{LEAD[1]}h",
            lambda: read(station_files([ONE_STATION]), lambda rg: True, lead_filter()),
            lambda: read(
                time_files(range(1, 13)),
                lambda rg: stat(rg, "station_code")[0] == ONE_STATION,
                lead_filter(),
            ),
        ),
        (
            f"L2 25 scattered stations, both models, 1-14 July, lead {LEAD[0]}-{LEAD[1]}h",
            lambda: read(station_files(GROUP), in_window, lead_filter() & window_filter()),
            lambda: read(
                time_files([7]),
                lambda rg: stat(rg, "station_code")[0] in group,
                lead_filter() & window_filter(),
            ),
        ),
        (
            "L3 25 scattered stations, both models, 1-14 July, every lead",
            lambda: read(station_files(GROUP), in_window, window_filter()),
            lambda: read(
                time_files([7]), lambda rg: stat(rg, "station_code")[0] in group, window_filter()
            ),
        ),
    ]


def timeit(fn):
    fn()
    samples = []
    for _ in range(5):
        t = time.perf_counter()
        rows, files, groups, nbytes = fn()
        samples.append(time.perf_counter() - t)
    ms = statistics.median(samples) * 1000
    return f"{ms:8.1f} ms  rows={rows:<9,} files={files:<4} row groups={groups:<4} fetched={nbytes / 1e6:.1f} MB"


def report():
    w = json.loads((ROOT / "write.json").read_text())
    if w["stations"] != N_STATIONS:
        raise SystemExit(f"{ROOT} holds {w['stations']} stations; pass --rewrite")
    print(f"year={YEAR} stations={N_STATIONS} models={list(MODELS)} rows={w['rows']:,}")
    print("\n== storage ==")
    for layout in ["leads_by_station", "leads_by_time"]:
        files = [p for p in (ROOT / layout).rglob("*.parquet")]
        size = sum(p.stat().st_size for p in files)
        print(
            f"{layout:17s} {size / 1e6:8.1f} MB  {len(files):5d} objects  "
            f"{size / w['rows']:5.1f} B/row  {size / len(files) / 1e6:6.1f} MB/object"
        )
    print("\n== reads: median of 5 ==")
    for name, by_station, by_time in queries():
        print(name)
        print("   leads_by_station", timeit(by_station))
        print("   leads_by_time   ", timeit(by_time))


if __name__ == "__main__":
    if not (ROOT / "write.json").exists() or ARGS.rewrite:
        write_all()
    report()
