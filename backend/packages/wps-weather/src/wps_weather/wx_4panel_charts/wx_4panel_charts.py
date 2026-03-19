import argparse
import asyncio
import logging
import os
import tempfile
from datetime import date
from typing import List, Tuple

import aiofiles
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import xarray as xr
from wps_shared import config
from wps_shared.utils.s3_client import S3Client
from wps_shared.wps_logging import configure_logging
from wps_weather.wx_4panel_charts.panel_layout import (
    add_panel_title,
    add_valid_time_stamp,
    apply_4panel_frames,
)
from wps_weather.wx_4panel_charts.plot_4panel_rdps import (
    _valid_time_str,
    rdps_fname,
)
from wps_weather.wx_4panel_charts.plot_500mb_rdps import CFG_500 as CFG_500_RDPS
from wps_weather.wx_4panel_charts.plot_500mb_rdps import plot_500hpa
from wps_weather.wx_4panel_charts.plot_700mb_rdps import CFG_700_RDPS, plot_700hpa_rdps
from wps_weather.wx_4panel_charts.plot_mslp_rdps import CFG_MSLP_RDPS, plot_mslp_thickness_rdps
from wps_weather.wx_4panel_charts.plot_precip_rdps import PLOT_CONFIG_PCPN3_RDPS as CFG_PCPN_RDPS
from wps_weather.wx_4panel_charts.plot_precip_rdps import plot_pcpn3_rdps
from wps_weather.wx_4panel_charts.raster_addresser import (
    ECCCModel,
    RasterAddresser,
)
from wps_weather.wx_4panel_charts.wx_4panel_chart_config_builder import ConfigBuilder

DEFAULT_FIG_SIZE = (11.8, 10)
DEFAULT_DPI = 300

configure_logging()
logger = logging.getLogger(__name__)


def build_cfgs_for_fh_rdps(init_ymd: str, init_hh: str, fh: int, ra: RasterAddresser):
    """
    Build cfg dicts using weather model grib2 S3 storage structure:
    eg: {bucket}/weather_models/20260217/model_rdps}/10km/{HH}/{FFF}/*.grib2
    """
    # ---- 500 hPa ----
    cfg500 = CFG_500_RDPS.copy()
    cfg500["z500_grib"] = ra.get_grib_key(
        fh,
        rdps_fname(init_ymd, init_hh, "GeopotentialHeight", "IsbL-0500", fh),
    )
    cfg500["vort_grib"] = ra.get_grib_key(
        fh,
        rdps_fname(init_ymd, init_hh, "AbsoluteVorticity", "IsbL-0500", fh),
    )
    cfg500["valid_time_str"] = _valid_time_str(init_ymd, init_hh, fh)

    # ---- MSLP + thickness ----
    cfgmslp = CFG_MSLP_RDPS.copy()
    cfgmslp["mslp_grib"] = ra.get_grib_key(
        fh,
        rdps_fname(init_ymd, init_hh, "Pressure_MSL", None, fh),
    )
    cfgmslp["thk_grib"] = ra.get_grib_key(
        fh,
        rdps_fname(init_ymd, init_hh, "Thickness", "IsbL-1000to0500", fh),
    )

    # ---- 700 hPa + RH layer mean ----
    cfg700 = CFG_700_RDPS.copy()
    cfg700["z700_grib"] = ra.get_grib_key(
        fh,
        rdps_fname(init_ymd, init_hh, "GeopotentialHeight", "IsbL-0700", fh),
    )
    cfg700["rh500_grib"] = ra.get_grib_key(
        fh,
        rdps_fname(init_ymd, init_hh, "RelativeHumidity", "IsbL-0500", fh),
    )
    cfg700["rh700_grib"] = ra.get_grib_key(
        fh,
        rdps_fname(init_ymd, init_hh, "RelativeHumidity", "IsbL-0700", fh),
    )
    cfg700["rh850_grib"] = ra.get_grib_key(
        fh,
        rdps_fname(init_ymd, init_hh, "RelativeHumidity", "IsbL-0850", fh),
    )

    # ---- 3h precip + jet ----
    cfgpcpn = CFG_PCPN_RDPS.copy()
    cfgpcpn["jet_spd_grib"] = ra.get_grib_key(
        fh,
        rdps_fname(init_ymd, init_hh, "WindSpeed", "IsbL-0250", fh),
    )

    if fh == 0:
        cfgpcpn["show_precip"] = False  # jet-only at analysis time
    else:
        cfgpcpn["show_precip"] = True
        # RDPS 3-hourly accumulation (adjust field token if your files differ)
        cfgpcpn["pcpn_grib"] = ra.get_grib_key(
            fh,
            rdps_fname(init_ymd, init_hh, "Precip-Accum3h", "Sfc", fh),
        )

    return cfg500, cfgmslp, cfg700, cfgpcpn


class FourPanelChartRunner:
    def __init__(self, s3_client: S3Client):
        self._s3_client = s3_client

    async def _open_dataset_s3(self, key):
        """
        Creates a xarray.Dataset from the grib file located at the provided S3 key.

        :param key: The key to the grib file in object storage.
        :return: An xarray.Dataset object.
        """
        # Get the grib file and read the bytes.
        response = await self._s3_client.get_object(key)

        status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status != 200:
            raise RuntimeError(
                f"Error when fetching key {key} from S3. HTTP status code was: {status}"
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            fd, temp_path = tempfile.mkstemp(suffix=".grib2", dir=temp_dir)
            os.close(fd)
            async with response["Body"] as stream, aiofiles.open(temp_path, "wb") as f:
                content = await stream.read()
                await f.write(content)

            # Create the xarray.Dataset and load it. load() must be called before unlinking the tmp file.
            ds = xr.open_dataset(
                temp_path,
                engine="cfgrib",
                backend_kwargs={"indexpath": ""},
            )
            ds = ds.load()

            return ds

    async def _make_4panel_chart_rdps(
        self,
        cfg500,
        cfgmslp,
        cfg700,
        cfgpcpn,
        figsize: Tuple[float, float],
        dpi: int,
        output_key: str,
    ):
        proj = ccrs.LambertConformal(
            central_longitude=cfg500.get("central_longitude", -130.0),
            central_latitude=cfg500.get("central_latitude", 50.0),
        )

        fig, axes = plt.subplots(
            2,
            2,
            figsize=figsize,
            dpi=dpi,
            subplot_kw={"projection": proj},
        )

        ax500, axmslp = axes[0, 0], axes[0, 1]
        ax700, axpcpn = axes[1, 0], axes[1, 1]

        ds_z500 = await self._open_dataset_s3(cfg500["z500_grib"])
        ds_vort = await self._open_dataset_s3(cfg500["vort_grib"])

        plot_500hpa(cfg500, ax=ax500, ds_z500=ds_z500, ds_vort=ds_vort)
        add_panel_title(ax500, "500 hPa Height + Abs Vorticity", loc="bl")

        ds_z500.close()
        ds_vort.close()

        ds_msl = await self._open_dataset_s3(cfgmslp["mslp_grib"])
        ds_thk = await self._open_dataset_s3(cfgmslp["thk_grib"])

        plot_mslp_thickness_rdps(cfgmslp, ax=axmslp, ds_msl=ds_msl, ds_thk=ds_thk)
        add_panel_title(axmslp, "MSLP + 1000–500 Thickness", loc="bl")

        ds_msl.close()
        ds_thk.close()

        ds_z700 = await self._open_dataset_s3(cfg700["z700_grib"])
        ds_rh850 = await self._open_dataset_s3(cfg700["rh850_grib"])
        ds_rh700 = await self._open_dataset_s3(cfg700["rh700_grib"])
        ds_rh500 = await self._open_dataset_s3(cfg700["rh500_grib"])

        plot_700hpa_rdps(
            cfg700,
            ax=ax700,
            ds_z700=ds_z700,
            ds_rh850=ds_rh850,
            ds_rh700=ds_rh700,
            ds_rh500=ds_rh500,
        )
        add_panel_title(ax700, "700 hPa Height + 850-500 Relative Humidity", loc="bl")

        ds_z700.close()
        ds_rh850.close()
        ds_rh700.close()
        ds_rh500.close()

        ds_p: xr.Dataset = None

        if cfgpcpn["show_precip"]:
            ds_p = await self._open_dataset_s3(cfgpcpn["pcpn_grib"])

        ds_js = await self._open_dataset_s3(cfgpcpn["jet_spd_grib"])

        plot_pcpn3_rdps(cfgpcpn, ax=axpcpn, ds_p=ds_p, ds_js=ds_js)
        add_panel_title(
            axpcpn, "3H PCPN" if cfgpcpn.get("show_precip", True) else "No PCPN at 00H", loc="bl"
        )

        if ds_p is not None:
            ds_p.close()
        ds_js.close()

        apply_4panel_frames(fig, axes, add_outer_border=True)

        valid_text = cfg500.get("valid_time_str", "")
        if valid_text:
            add_valid_time_stamp(fig, valid_text, height=0.04, fontsize=14)

        # Save the 4panel chart to S3. First save to a local temp file then write to S3.
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            fig.savefig(tmp, dpi=dpi, bbox_inches=None, pad_inches=0.0, facecolor="white")
            plt.close(fig)
            async with aiofiles.open(tmp.name, "rb") as f:
                body = await f.read()
                await self._s3_client.put_object(output_key, body)
                print("Saved:", output_key)

    async def _make_4panel_charts_rdps(
        self, init_ymd: date, init_hh: str, fstart: int, fend: int, step: int
    ):
        raster_addresser = RasterAddresser(init_ymd, init_hh, ECCCModel.RDPS)
        config_builder = ConfigBuilder(
            init_ymd=init_ymd,
            init_hh=init_hh,
            raster_addresser=raster_addresser,
            cfg500=CFG_500_RDPS,
            cfgmslp=CFG_MSLP_RDPS,
            cfg700=CFG_700_RDPS,
            cfgpcpn=CFG_PCPN_RDPS,
            file_name_builder=rdps_fname,
        )
        for fh in range(int(fstart), int(fend) + 1, int(step)):
            output_name = f"RDPS_{init_ymd}T{init_hh}Z_F{fh:03d}_4panel.png"
            output_key = raster_addresser.get_4panel_key(fh, output_name)

            # If a 4panel chart already exists don't re-create it.
            if await self._s3_client.object_exists(output_key):
                logger.info(f"Skipping: 4 panel chart already exists: {output_name}")
                continue

            cfg500, cfgmslp, cfg700, cfgpcpn = config_builder.build_config_for_hour(fh)
            # cfg500, cfgmslp, cfg700, cfgpcpn = build_cfgs_for_fh_rdps(
            #     init_ymd, init_hh, fh, raster_addresser
            # )
            required_keys = [
                cfg500["z500_grib"],
                cfg500["vort_grib"],
                cfgmslp["mslp_grib"],
                cfgmslp["thk_grib"],
                cfg700["z700_grib"],
                cfg700["rh500_grib"],
                cfg700["rh700_grib"],
                cfg700["rh850_grib"],
            ]
            if cfgpcpn.get("show_precip", True):
                required_keys.append(cfgpcpn["pcpn_grib"])
            if cfgpcpn.get("show_jet_core", True):
                required_keys.append(cfgpcpn["jet_spd_grib"])

            all_keys_exist = await self._s3_client.all_objects_exist(*required_keys)
            if not all_keys_exist:
                logger.info(
                    f"Unable to create 4 panel chart {output_name} due to missing input files."
                )
                return False

            await self._make_4panel_chart_rdps(
                cfg500, cfgmslp, cfg700, cfgpcpn, DEFAULT_FIG_SIZE, DEFAULT_DPI, output_key
            )
        return True

    async def _make_4panel_charts_gdps(
        self, init_ymd: date, init_hh: str, fstart: int, fend: int, step: int
    ):
        raise NotImplementedError()

    async def run(
        self, init_ymd: date, model_runs: List[str], fstart: int, fend: int, step: int, model: str
    ):
        assert model == ECCCModel.GDPS or model == ECCCModel.RDPS
        for init_hh in model_runs:
            # TODO - Get or create database record. If charts complete, continue
            if model == ECCCModel.RDPS:
                complete = await self._make_4panel_charts_rdps(
                    init_ymd, init_hh, fstart, fend, step
                )
                # TODO - If charts complete update database
            elif model == ECCCModel.GDPS:
                complete = await self._make_4panel_charts_gdps(
                    init_ymd, model_runs, fstart, fend, step
                )
            else:
                raise RuntimeError("Unrecognized ECCC weather model.")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Create 4Panel Charts from ECCC NWM data.")

    parser.add_argument(
        "--init_ymd",
        help="Model run date formatted as YYYYMMDD",
    )
    parser.add_argument(
        "--model_runs",
        nargs="+",
        choices=["00", "12"],
        default=["12"],
        help="Model run hour(s).",
    )
    parser.add_argument(
        "--fstart", type=int, default=0, help="The first prediction hour to generate a chart for."
    )
    parser.add_argument(
        "--fend", type=int, default=84, help="The last prediction hour to generate a chart for."
    )
    parser.add_argument(
        "--step", type=int, default=3, help="The hourly step increment between charts."
    )
    parser.add_argument(
        "--model", choices=["GDPS", "RDPS"], default="RDPS", help="The ECCC NWM (GDPS or RDPS)"
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()

    user_id = config.get("WX_OBJECT_STORE_USER_ID")
    secret_key = config.get("WX_OBJECT_STORE_SECRET")
    bucket = config.get("WX_OBJECT_STORE_BUCKET")

    async with S3Client(user_id=user_id, secret_key=secret_key, bucket=bucket) as s3_client:
        runner = FourPanelChartRunner(s3_client)
        await runner.run(
            args.init_ymd, args.model_runs, args.fstart, args.fend, args.step, args.model
        )


if __name__ == "__main__":
    asyncio.run(main())
