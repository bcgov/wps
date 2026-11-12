# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "deltalake==1.6.6",
#     "geopandas==1.2.0",
#     "icechunk==2.3.1",
#     "numpy==2.5.4",
#     "pandas==3.1.1",
#     "pyarrow==26.0.1",
#     "zarr==3.4.2",
# ]
# ///
"""Benchmark for docs/architecture/station-predictions-storage.md.

Writes the same synthetic station model predictions to Parquet, GeoParquet, Delta Lake, Zarr and
Icechunk, then reports storage size, object count and read times for the queries our readers make.

The dependencies above are not project dependencies, so run it with uv:

    uv run backend/scripts/station_predictions_storage_benchmark.py --days 60 --stations 300

It runs on local disk only. Sizes and object counts carry over to object storage; latencies do not.
The floats are random at full precision, so sizes are an upper bound.
"""

import argparse
import json
import shutil
import statistics
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import geopandas as gpd
import icechunk
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import zarr
from deltalake import DeltaTable, write_deltalake

parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
parser.add_argument("--days", type=int, default=60, help="days of model runs to generate")
parser.add_argument("--stations", type=int, default=300, help="number of weather stations")
parser.add_argument(
    "--out",
    type=Path,
    default=Path(tempfile.gettempdir()) / "station_predictions_storage_benchmark",
    help="output directory; it is deleted and recreated when data is (re)written",
)
parser.add_argument("--rewrite", action="store_true", help="regenerate data even if --out has it")
ARGS = parser.parse_args()
if ARGS.days < 6:
    parser.error("--days must be at least 6: the queries read around a point 5 days before the end")

ROOT: Path = ARGS.out
N_STATIONS: int = ARGS.stations
N_DAYS: int = ARGS.days
START = datetime(2026, 5, 1, tzinfo=UTC)
rng = np.random.default_rng(42)

FLOAT_COLS = [
    "tmp_tgl_2",
    "rh_tgl_2",
    "apcp_sfc_0",
    "wdir_tgl_10",
    "wind_tgl_10",
    "bias_adjusted_temperature",
    "bias_adjusted_rh",
    "bias_adjusted_wdir",
    "bias_adjusted_wind_speed",
    "delta_precip",
    "precip_24h",
    "bias_adjusted_precip_24h",
]
RAW_COLS = FLOAT_COLS[:5]
STATIONS = np.arange(1, N_STATIONS + 1, dtype=np.int32) * 7
LAT = rng.uniform(48.3, 60.0, N_STATIONS)
LON = rng.uniform(-139.0, -114.0, N_STATIONS)


def noon_pairs(run_hour, max_h):
    before = list(range((18 - run_hour) % 24, max_h + 1, 24))
    return sorted(set(before + [b + 3 for b in before if b + 3 <= max_h]))


def with_2000(steps, run_hour, max_h):
    """Add the interpolated 20:00 UTC rows that the ingest job writes for 3-hourly models."""
    extra = [s for s in range(max_h + 1) if (run_hour + s) % 24 == 20]
    return sorted(set(steps) | set(extra))


MODELS = {
    "GDPS": ([0, 12], lambda h: with_2000(range(0, 241, 3), h, 240)),
    "RDPS": ([0, 6, 12, 18], lambda h: list(range(85))),
    "HRDPS": ([0, 6, 12, 18], lambda h: list(range(49))),
    "GFS": ([0, 6, 12, 18], lambda h: with_2000(noon_pairs(h, 240), h, 240)),
    "NAM": ([0, 6, 12, 18], lambda h: with_2000(noon_pairs(h, 84), h, 84)),
    "ECMWF": (
        [0, 12],
        lambda h: with_2000(list(range(0, 145, 3)) + list(range(150, 241, 6)), h, 240),
    ),
}
ZSTEPS = {m: sorted({s for h in hrs for s in fn(h)}) for m, (hrs, fn) in MODELS.items()}

SCHEMA = pa.schema(
    [
        ("station_code", pa.int32()),
        ("run_ts", pa.timestamp("us", tz="UTC")),
        ("prediction_timestamp", pa.timestamp("us", tz="UTC")),
    ]
    + [(c, pa.float64()) for c in FLOAT_COLS]
)


def make_run(model, run_ts):
    """Return (steps, cube[var, step, station]) of plausible full-precision floats."""
    steps = MODELS[model][1](run_ts.hour)
    n = len(steps)
    base = {
        "tmp": 15
        + 10 * np.sin(np.array(steps)[:, None] / 24 * 2 * np.pi)
        + rng.normal(0, 3, (n, N_STATIONS)),
        "rh": np.clip(50 + rng.normal(0, 20, (n, N_STATIONS)), 5, 100),
        "apcp": np.cumsum(np.maximum(rng.normal(-1, 1, (n, N_STATIONS)), 0), axis=0),
        "wdir": rng.uniform(0, 360, (n, N_STATIONS)),
        "wind": np.abs(rng.normal(8, 5, (n, N_STATIONS))),
    }
    cube = np.stack(
        [
            base["tmp"],
            base["rh"],
            base["apcp"],
            base["wdir"],
            base["wind"],
            base["tmp"] + rng.normal(0, 1, (n, N_STATIONS)),
            base["rh"] + rng.normal(0, 3, (n, N_STATIONS)),
            base["wdir"] + rng.normal(0, 5, (n, N_STATIONS)),
            base["wind"] + rng.normal(0, 1, (n, N_STATIONS)),
            np.diff(base["apcp"], axis=0, prepend=0),
            base["apcp"],
            base["apcp"] * 1.05,
        ]
    )
    return steps, cube


def to_table(run_ts, steps, cube):
    n = len(steps)
    # sorted by station_code, then prediction_timestamp
    pts = np.array(
        [np.datetime64(int((run_ts + timedelta(hours=s)).timestamp() * 1e6), "us") for s in steps]
    )
    cols = {
        "station_code": np.repeat(STATIONS, n),
        "run_ts": pa.array(
            np.full(n * N_STATIONS, np.datetime64(int(run_ts.timestamp() * 1e6), "us")),
            pa.timestamp("us", tz="UTC"),
        ),
        "prediction_timestamp": pa.array(np.tile(pts, N_STATIONS), pa.timestamp("us", tz="UTC")),
    }
    for i, c in enumerate(FLOAT_COLS):
        cols[c] = cube[i].T.reshape(-1)
    return pa.table(cols, schema=SCHEMA)


def du(path):
    files = [p for p in Path(path).rglob("*") if p.is_file()]
    return sum(p.stat().st_size for p in files), len(files)


class ZarrSink:
    def __init__(self, store):
        self.root = zarr.open_group(store, mode="a")
        self.n = {}

    def append(self, model, run_ts, steps, cube):
        zsteps = ZSTEPS[model]
        if model not in self.n:
            g = self.root.create_group(model)
            g.attrs["steps"] = zsteps
            g.attrs["stations"] = STATIONS.tolist()
            g.create_array("run", shape=(0,), chunks=(4096,), dtype="i8")
            for c in FLOAT_COLS:
                g.create_array(
                    c,
                    shape=(0, len(zsteps), N_STATIONS),
                    chunks=(1, len(zsteps), N_STATIONS),
                    dtype="f8",
                    fill_value=np.nan,
                    compressors=zarr.codecs.ZstdCodec(level=3),
                )
            self.n[model] = 0
        g, i = self.root[model], self.n[model]
        idx = [zsteps.index(s) for s in steps]
        g["run"].resize((i + 1,))
        g["run"][i] = int(run_ts.timestamp())
        for k, c in enumerate(FLOAT_COLS):
            dense = np.full((len(zsteps), N_STATIONS), np.nan)
            dense[idx] = cube[k]
            g[c].resize((i + 1, len(zsteps), N_STATIONS))
            g[c][i] = dense
        self.n[model] = i + 1


def write_all():
    shutil.rmtree(ROOT, ignore_errors=True)
    ROOT.mkdir(parents=True)
    wt = dict.fromkeys(
        ["parquet", "geoparquet", "delta_runs", "delta_daily", "zarr", "icechunk"], 0.0
    )
    zs = ZarrSink(zarr.storage.LocalStore(ROOT / "zarr"))
    repo = icechunk.Repository.create(icechunk.local_filesystem_storage(str(ROOT / "icechunk")))
    ice_n = {}
    geom = gpd.points_from_xy(LON, LAT)
    rows = 0
    runs = sorted(
        (START + timedelta(days=d, hours=h), m)
        for d in range(N_DAYS)
        for m, (hrs, _) in MODELS.items()
        for h in hrs
    )
    for run_ts, model in runs:
        steps, cube = make_run(model, run_ts)
        tbl = to_table(run_ts, steps, cube)
        rows += tbl.num_rows
        tag = run_ts.strftime("%Y%m%d%H")

        t = time.perf_counter()
        d = ROOT / "parquet" / f"model={model}" / f"run_date={run_ts:%Y-%m-%d}"
        d.mkdir(parents=True, exist_ok=True)
        pq.write_table(tbl, d / f"{tag}.parquet", compression="zstd")
        wt["parquet"] += time.perf_counter() - t

        t = time.perf_counter()
        d = ROOT / "geoparquet" / f"model={model}" / f"run_date={run_ts:%Y-%m-%d}"
        d.mkdir(parents=True, exist_ok=True)
        gdf = gpd.GeoDataFrame(
            tbl.to_pandas(), geometry=np.repeat(geom, len(steps)), crs="EPSG:4326"
        )
        gdf.to_parquet(d / f"{tag}.parquet", compression="zstd")
        wt["geoparquet"] += time.perf_counter() - t

        t = time.perf_counter()
        dtbl = tbl.append_column("model", pa.array([model] * tbl.num_rows)).append_column(
            "run_date", pa.array([run_ts.date()] * tbl.num_rows, pa.date32())
        )
        write_deltalake(
            str(ROOT / "delta_runs"), dtbl, mode="append", partition_by=["model", "run_date"]
        )
        wt["delta_runs"] += time.perf_counter() - t

        t = time.perf_counter()
        daily = dtbl.filter(pc.equal(pc.hour(dtbl["prediction_timestamp"]), 20)).drop_columns(
            ["run_date"]
        )
        dpath = str(ROOT / "delta_daily")
        if not DeltaTable.is_deltatable(dpath):
            write_deltalake(dpath, daily, partition_by=["model"])
        else:
            (
                DeltaTable(dpath)
                .merge(
                    daily,
                    "t.model = s.model AND t.station_code = s.station_code AND t.prediction_timestamp = s.prediction_timestamp",
                    source_alias="s",
                    target_alias="t",
                )
                .when_matched_update_all(predicate="s.run_ts >= t.run_ts")
                .when_not_matched_insert_all()
                .execute()
            )
        wt["delta_daily"] += time.perf_counter() - t

        t = time.perf_counter()
        zs.append(model, run_ts, steps, cube)
        wt["zarr"] += time.perf_counter() - t

        t = time.perf_counter()
        session = repo.writable_session("main")
        sink = ZarrSink(session.store)
        sink.n = ice_n
        sink.append(model, run_ts, steps, cube)
        session.commit(f"{model} {tag}")
        wt["icechunk"] += time.perf_counter() - t

    # geoparquet stations dimension
    gpd.GeoDataFrame({"station_code": STATIONS}, geometry=geom, crs="EPSG:4326").to_parquet(
        ROOT / "stations.parquet"
    )
    meta = {"rows": rows, "runs": len(runs), "write_s": wt, "days": N_DAYS, "stations": N_STATIONS}
    (ROOT / "write.json").write_text(json.dumps(meta))


# ---------------------------------------------------------------- queries
T0 = START + timedelta(days=N_DAYS - 5, hours=12)
Q1_TS = [(T0 + timedelta(days=i)).replace(hour=20) for i in range(5)]
Q2_STATIONS = (
    STATIONS[[3, 50, 120, 200, 280]].tolist() if N_STATIONS >= 281 else STATIONS[:5].tolist()
)
MC_COLS = [
    "station_code",
    "run_ts",
    "prediction_timestamp",
    "tmp_tgl_2",
    "rh_tgl_2",
    "wdir_tgl_10",
    "wind_tgl_10",
    "bias_adjusted_temperature",
    "bias_adjusted_rh",
    "bias_adjusted_wind_speed",
    "bias_adjusted_wdir",
    "precip_24h",
    "bias_adjusted_precip_24h",
]


def TS(x):
    return pa.scalar(x, pa.timestamp("us", tz="UTC"))


def latest(tbl):
    df = tbl.to_pandas().sort_values("run_ts")
    return df.drop_duplicates(["model", "station_code", "prediction_timestamp"], keep="last")


def pds(kind):
    if kind == "delta":
        return DeltaTable(str(ROOT / "delta_runs")).to_pyarrow_dataset()
    part = ds.partitioning(
        pa.schema([("model", pa.string()), ("run_date", pa.date32())]), flavor="hive"
    )
    return ds.dataset(ROOT / kind, partitioning=part)


def scan(kind, flt, cols):
    d = pds(kind)
    nfrag = sum(1 for _ in d.get_fragments(filter=flt))
    return d.to_table(filter=flt, columns=cols), nfrag


def rd(x):  # run_date bound
    return pa.scalar(x.date(), pa.date32())


def q1(kind):
    f = (ds.field("run_date") >= rd(Q1_TS[0] - timedelta(days=10))) & ds.field(
        "prediction_timestamp"
    ).isin(pa.array(Q1_TS, pa.timestamp("us", tz="UTC")))
    t, n = scan(kind, f, MC_COLS + ["model"])
    return len(latest(t)), n


def q1_daily():
    dt = DeltaTable(str(ROOT / "delta_daily")).to_pyarrow_dataset()
    f = ds.field("prediction_timestamp").isin(pa.array(Q1_TS, pa.timestamp("us", tz="UTC")))
    return dt.to_table(filter=f, columns=MC_COLS + ["model"]).num_rows, sum(
        1 for _ in dt.get_fragments(filter=f)
    )


def q2(kind):
    lo, hi = T0 - timedelta(days=5), T0 + timedelta(days=10)
    f = (
        (ds.field("model") == "HRDPS")
        & (ds.field("run_date") >= rd(lo - timedelta(days=2)))
        & (ds.field("prediction_timestamp") >= TS(lo))
        & (ds.field("prediction_timestamp") <= TS(hi))
        & ds.field("station_code").isin(Q2_STATIONS)
    )
    t, n = scan(kind, f, None)
    return t.num_rows, n


def q3(kind):
    lo = T0 - timedelta(days=19)
    f = (
        (ds.field("model") == "RDPS")
        & (ds.field("run_date") >= rd(lo - timedelta(days=4)))
        & (ds.field("run_date") <= rd(T0))
        & (ds.field("prediction_timestamp") >= TS(lo))
        & (ds.field("prediction_timestamp") <= TS(T0))
    )
    t, n = scan(kind, f, ["station_code", "run_ts", "prediction_timestamp"] + RAW_COLS)
    return t.num_rows, n


def q4(kind):
    run = (T0 - timedelta(days=1)).replace(hour=12)
    f = (
        (ds.field("model") == "RDPS")
        & (ds.field("run_date") == rd(run))
        & (ds.field("run_ts") == TS(run))
    )
    t, n = scan(kind, f, None)
    return t.num_rows, n


def zopen(kind):
    if kind == "zarr":
        return zarr.open_group(zarr.storage.LocalStore(ROOT / "zarr"), mode="r")
    repo = icechunk.Repository.open(icechunk.local_filesystem_storage(str(ROOT / "icechunk")))
    return zarr.open_group(repo.readonly_session("main").store, mode="r")


def zruns(g, lo, hi):
    run = g["run"][:]
    return (
        run,
        int(np.searchsorted(run, lo.timestamp())),
        int(np.searchsorted(run, hi.timestamp(), side="right")),
    )


def zq1(kind):
    root, n, chunks = zopen(kind), 0, 0
    for m in MODELS:
        g = root[m]
        steps = np.array(g.attrs["steps"])
        run, a, b = zruns(g, Q1_TS[0] - timedelta(days=10), Q1_TS[-1])
        out = {}
        for c in MC_COLS[3:]:
            slab = g[c][a:b]
            chunks += b - a
            for ts in Q1_TS:
                st = (ts.timestamp() - run[a:b]) / 3600
                best = None
                for r in np.argsort(run[a:b])[::-1]:
                    k = np.searchsorted(steps, st[r])
                    if (
                        st[r] >= 0
                        and k < len(steps)
                        and steps[k] == st[r]
                        and not np.isnan(slab[r, k, 0])
                    ):
                        best = slab[r, k]
                        break
                out[(c, ts)] = best
        n += sum(v is not None for (c, _), v in out.items() if c == "tmp_tgl_2") * N_STATIONS
    return n, chunks


def zslab(kind, model, lo, hi, back_h, cols, station_idx=None):
    g = zopen(kind)[model]
    _run, a, b = zruns(g, lo - timedelta(hours=back_h), hi)
    n = 0
    for c in cols:
        slab = g[c][a:b] if station_idx is None else g[c][a:b][:, :, station_idx]
        n = int(np.count_nonzero(~np.isnan(slab)))
    return n, (b - a) * len(cols)


def zq2(kind):
    idx = [int(np.where(STATIONS == s)[0][0]) for s in Q2_STATIONS]
    return zslab(
        kind, "HRDPS", T0 - timedelta(days=5), T0 + timedelta(days=10), 48, FLOAT_COLS, idx
    )


def zq3(kind):
    return zslab(kind, "RDPS", T0 - timedelta(days=19), T0, 84, RAW_COLS)


def zq4(kind):
    run = (T0 - timedelta(days=1)).replace(hour=12)
    return zslab(kind, "RDPS", run, run, 0, FLOAT_COLS)


def timeit(fn, *a):
    fn(*a)
    ts = []
    for _ in range(5):
        t = time.perf_counter()
        res = fn(*a)
        ts.append(time.perf_counter() - t)
    return round(statistics.median(ts) * 1000, 1), res


def report():
    w = json.loads((ROOT / "write.json").read_text())
    if (w["days"], w["stations"]) != (N_DAYS, N_STATIONS):
        raise SystemExit(
            f"{ROOT} holds a {w['days']}-day, {w['stations']}-station run; pass --rewrite"
        )
    print(f"days={N_DAYS} stations={N_STATIONS} rows={w['rows']:,} runs={w['runs']}")
    print("\n== storage ==")
    for k in ["parquet", "geoparquet", "delta_runs", "delta_daily", "zarr", "icechunk"]:
        b, n = du(ROOT / k)
        print(
            f"{k:12s} {b / 1e6:9.1f} MB  {n:6d} objects  {b / w['rows']:6.1f} B/row  write {w['write_s'][k] / w['runs'] * 1000:7.1f} ms/run"
        )
    dt = DeltaTable(str(ROOT / "delta_daily"))
    live = sum(Path(u.replace("file://", "")).stat().st_size for u in dt.file_uris())
    print(
        f"delta_daily live data: {live / 1e6:.2f} MB in {len(dt.file_uris())} files, version {dt.version()}"
    )
    print("\n== queries: median ms, (rows, objects read) ==")
    qs = [
        ("Q1 morecast 20:00 latest, 5d, all stn, all models", q1, zq1),
        ("Q2 5 stations, HRDPS, 15d window, all runs", q2, zq2),
        ("Q3 training: RDPS 19d raw cols all stations", q3, zq3),
        ("Q4 one RDPS run", q4, zq4),
    ]
    for name, pf, zf in qs:
        print(name)
        for kind in ["parquet", "geoparquet", "delta"]:
            print(f"   {kind:12s}", *timeit(pf, kind))
        if pf is q1:
            print(f"   {'delta_daily':12s}", *timeit(q1_daily))
        for kind in ["zarr", "icechunk"]:
            print(f"   {kind:12s}", *timeit(zf, kind))

    # compaction: what does delta look like after optimize?
    t = time.perf_counter()
    d = DeltaTable(str(ROOT / "delta_runs"))
    d.optimize.compact()
    print(f"\n== delta_runs after optimize.compact ({time.perf_counter() - t:.1f}s) ==")
    live = sum(Path(u.replace("file://", "")).stat().st_size for u in d.file_uris())
    print(f"live {live / 1e6:.1f} MB in {len(d.file_uris())} files")
    for name, pf, _ in qs:
        print(f"   {name[:2]} delta(compacted)", *timeit(pf, "delta"))


if __name__ == "__main__":
    if not (ROOT / "write.json").exists() or ARGS.rewrite:
        write_all()
    report()
