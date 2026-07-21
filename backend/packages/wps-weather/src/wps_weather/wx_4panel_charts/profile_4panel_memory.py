"""
Standalone memory-profiling harness for the wx-4panel-charts-rdps cronjob.

Exercises the real production panel-generation path
(`FourPanelChartRunner._make_4panel_chart`, via `ConfigBuilder`/`PlotterFactory`,
same as production) against real RDPS GRIB2 files downloaded from ECCC's public
hpfx mirror, with S3 and Postgres access stubbed out so it runs with no cloud
credentials.

Usage:
    # 1) download real grib2 files for the forecast hours you want to profile
    uv run --package wps-weather python -m wps_weather.wx_4panel_charts.download_rdps \\
        --start 20260718 --days 1 --cycles 12 --step 3 --maxhr 12

    # 2) profile panel generation against those files
    uv run --package wps-weather python -m wps_weather.wx_4panel_charts.profile_4panel_memory \\
        --init_ymd 20260718 --init_hh 12 --end_hour 12 --step 3

Get a flamegraph attributing peak memory to call sites (e.g. confirming the
Delaunay triangulation / tricontour calls as the peak allocators):
    uv run --package wps-weather memray run -o 4panel.bin -m wps_weather.wx_4panel_charts.profile_4panel_memory ...
    memray flamegraph 4panel.bin

Reproduce the actual OOMKill locally (matches the prod 4Gi limit) via podman:
    podman run --rm --memory=4g -v "$(pwd)":/app -w /app <wps-weather-image> \\
        uv run --package wps-weather python -m wps_weather.wx_4panel_charts.profile_4panel_memory ...
"""

import argparse
import asyncio
import resource
import sys
from pathlib import Path

import cartopy

from wps_weather.wx_4panel_charts.config_builder import ConfigBuilder
from wps_weather.wx_4panel_charts.plot_4panel_gdps import gdps_fname
from wps_weather.wx_4panel_charts.plot_4panel_rdps import rdps_fname
from wps_weather.wx_4panel_charts.plot_500mb import CFG_500 as CFG_500_GDPS
from wps_weather.wx_4panel_charts.plot_500mb_rdps import CFG_500 as CFG_500_RDPS
from wps_weather.wx_4panel_charts.plot_700mb import CFG_700 as CFG_700_GDPS
from wps_weather.wx_4panel_charts.plot_700mb_rdps import CFG_700_RDPS
from wps_weather.wx_4panel_charts.plot_mslp import CFG_MSLP as CFG_MSLP_GDPS
from wps_weather.wx_4panel_charts.plot_mslp_rdps import CFG_MSLP_RDPS
from wps_weather.wx_4panel_charts.plot_precip import PLOT_CONFIG_PCPN12 as CFG_PCPN_GDPS
from wps_weather.wx_4panel_charts.plot_precip_rdps import PLOT_CONFIG_PCPN3_RDPS as CFG_PCPN_RDPS
from wps_weather.wx_4panel_charts.plotter_factory import PlotterFactory
from wps_weather.wx_4panel_charts.wx_4panel_chart_addresser import ECCCModel, WX4PanelChartAddresser
from wps_weather.wx_4panel_charts.wx_4panel_charts import DEFAULT_DPI, DEFAULT_FIG_SIZE, FourPanelChartRunner

_MODEL_CFGS = {
    ECCCModel.GDPS: (CFG_500_GDPS, CFG_MSLP_GDPS, CFG_700_GDPS, CFG_PCPN_GDPS, gdps_fname),
    ECCCModel.RDPS: (CFG_500_RDPS, CFG_MSLP_RDPS, CFG_700_RDPS, CFG_PCPN_RDPS, rdps_fname),
}


class _LocalBody:
    """Stands in for the boto3 StreamingBody so _open_dataset_s3 can `async with response["Body"]`."""

    def __init__(self, path: Path):
        self._path = path

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def read(self) -> bytes:
        return self._path.read_bytes()


class LocalGribS3Stub:
    """
    Drop-in replacement for S3Client that serves grib files downloaded locally
    (via download_rdps.py) instead of hitting real S3. The S3 "key" always ends
    in the same rdps_fname/gdps_fname filename that download_rdps.py writes to
    disk, so files are matched by basename.
    """

    def __init__(self, data_root: Path, output_dir: Path):
        self._output_dir = output_dir
        self._index: dict[str, Path] = {p.name: p for p in data_root.rglob("*.grib2")}

    def _resolve(self, key: str) -> Path | None:
        return self._index.get(Path(key).name)

    async def get_object(self, key: str):
        path = self._resolve(key)
        if path is None:
            raise FileNotFoundError(
                f"No downloaded grib2 matches key {key!r}. Run download_rdps.py for this init/fh first."
            )
        return {"ResponseMetadata": {"HTTPStatusCode": 200}, "Body": _LocalBody(path)}

    async def put_object(self, key: str, body: bytes):
        out = self._output_dir / Path(key).name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(body)

    async def object_exists(self, key: str) -> bool:
        return self._resolve(key) is not None

    async def all_objects_exist(self, *keys: str) -> bool:
        return all(self._resolve(k) is not None for k in keys)


def _rss_mb() -> float:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is bytes on macOS, KB on Linux.
    return peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024


async def run(args):
    if args.cartopy_data_dir:
        cartopy.config["data_dir"] = args.cartopy_data_dir

    model = ECCCModel(args.model)
    cfg500_base, cfgmslp_base, cfg700_base, cfgpcpn_base, fname_builder = _MODEL_CFGS[model]
    raster_addresser = WX4PanelChartAddresser(args.init_ymd, args.init_hh, model)
    config_builder = ConfigBuilder(
        init_ymd=args.init_ymd,
        init_hh=args.init_hh,
        raster_addresser=raster_addresser,
        cfg500=cfg500_base,
        cfgmslp=cfgmslp_base,
        cfg700=cfg700_base,
        cfgpcpn=cfgpcpn_base,
        file_name_builder=fname_builder,
        model=model,
    )
    plotter_factory = PlotterFactory(model=model)

    s3_stub = LocalGribS3Stub(Path(args.data_root), Path(args.output_dir))
    runner = FourPanelChartRunner(s3_stub)

    for fh in range(args.start_hour, args.end_hour + 1, args.step):
        cfg500, cfgmslp, cfg700, cfgpcpn = config_builder.build_config_for_hour(fh)
        output_name = f"{model.value}_{args.init_ymd}T{args.init_hh}Z_F{fh:03d}_4panel.png"
        output_key = raster_addresser.get_4panel_key(fh, output_name)

        await runner._make_4panel_chart(
            cfg500,
            cfgmslp,
            cfg700,
            cfgpcpn,
            DEFAULT_FIG_SIZE,
            DEFAULT_DPI,
            output_key,
            plotter_factory,
            args.step,
        )
        print(f"[fh={fh:03d}] peak RSS so far: {_rss_mb():.1f} MB -> {output_name}")


def parse_args():
    p = argparse.ArgumentParser(description="Profile FourPanelChartRunner memory use against local GRIB2 files.")
    p.add_argument("--init_ymd", required=True, help="Model run date YYYYMMDD, matching what you downloaded.")
    p.add_argument("--init_hh", required=True, help="Model run hour, e.g. 00 or 12.")
    p.add_argument("--model", choices=["GDPS", "RDPS"], default="RDPS")
    p.add_argument("--start_hour", type=int, default=0)
    p.add_argument("--end_hour", type=int, default=12)
    p.add_argument("--step", type=int, default=3)
    p.add_argument("--data_root", default="data_hpfx", help="Where download_rdps.py wrote the grib2 files.")
    p.add_argument("--output_dir", default="outputs", help="Where to write generated PNGs.")
    p.add_argument("--cartopy_data_dir", default=None)
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
