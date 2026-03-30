import argparse
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, time, timedelta, timezone
from typing import List, Optional, Tuple

import aiofiles
import cartopy
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import xarray as xr
from wps_shared import config
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now
from wps_shared.wps_logging import configure_logging

from wps_weather.db.crud.wx_4panel_charts import (
    get_earliest_in_progress_date_limited,
    get_last_complete,
    get_or_create_processed_four_panel_chart,
    save_four_panel_chart,
)
from wps_weather.db.models.wx_4panel_charts import ChartStatusEnum, ECCCModel, ModelNames
from wps_weather.wx_4panel_charts.config_builder import ConfigBuilder
from wps_weather.wx_4panel_charts.panel_layout import (
    add_panel_title,
    add_valid_time_stamp,
    apply_4panel_frames,
)
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
from wps_weather.wx_4panel_charts.wx_4panel_chart_addresser import WX4PanelChartAddresser

DEFAULT_FIG_SIZE = (11.8, 10)
DEFAULT_DPI = 300

configure_logging()
logger = logging.getLogger(__name__)


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

        async with (
            aiofiles.tempfile.NamedTemporaryFile(suffix=".grib2", mode="w+b") as f,
            response["Body"] as stream,
        ):
            content = await stream.read()
            await f.write(content)
            await f.seek(0)

            # Create the xarray.Dataset and load it. load() must be called before unlinking the tmp file.
            ds = xr.open_dataset(
                f.name,
                engine="cfgrib",
                backend_kwargs={"indexpath": ""},
            )
            ds = ds.load()

            return ds

    @asynccontextmanager
    async def _dataset(self, key):
        # Small helper to ensure datasets get closed in the event of an error.
        ds = await self._open_dataset_s3(key)
        if not isinstance(ds, xr.Dataset):
            logger.error(
                f"Expected xr.Dataset for key '{key}', got {type(ds).__name__}. Skipping chart."
            )
            raise TypeError(f"Expected xr.Dataset for key '{key}', got {type(ds).__name__}.")
        try:
            yield ds
        finally:
            ds.close()

    async def _make_4panel_chart(
        self,
        cfg500,
        cfgmslp,
        cfg700,
        cfgpcpn,
        figsize: Tuple[float, float],
        dpi: int,
        output_key: str,
        plotter_factory: PlotterFactory,
        step: int,
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

        async with (
            self._dataset(cfg500["z500_grib"]) as ds_z500,
            self._dataset(cfg500["vort_grib"]) as ds_vort,
        ):
            logger.info(f"Creating 500hpa panel for {output_key}")
            plotter_500hpa = plotter_factory.get_500hpa_plotter()
            plotter_500hpa(cfg500, ax=ax500, ds_z500=ds_z500, ds_vort=ds_vort)
            add_panel_title(ax500, "500 hPa Height + Abs Vorticity", loc="bl")

        async with (
            self._dataset(cfgmslp["mslp_grib"]) as ds_msl,
            self._dataset(cfgmslp["thk_grib"]) as ds_thk,
        ):
            logger.info(f"Creating mslp panel for {output_key}")
            plotter_mslp_thickness = plotter_factory.get_mslp_thickness_plotter()
            plotter_mslp_thickness(cfgmslp, ax=axmslp, ds_msl=ds_msl, ds_thk=ds_thk)
            add_panel_title(axmslp, "MSLP + 1000–500 Thickness", loc="bl")

        async with (
            self._dataset(cfg700["z700_grib"]) as ds_z700,
            self._dataset(cfg700["rh850_grib"]) as ds_rh850,
            self._dataset(cfg700["rh700_grib"]) as ds_rh700,
            self._dataset(cfg700["rh500_grib"]) as ds_rh500,
        ):
            logger.info(f"Creating 700hpa panel for {output_key}")
            plotter_700hpa = plotter_factory.get_700hpa_plotter()
            plotter_700hpa(
                cfg700,
                ax=ax700,
                ds_z700=ds_z700,
                ds_rh850=ds_rh850,
                ds_rh700=ds_rh700,
                ds_rh500=ds_rh500,
            )
            add_panel_title(ax700, "700 hPa Height + 850-500 Relative Humidity", loc="bl")

        ds_p: Optional[xr.Dataset] = None
        ds_js: Optional[xr.Dataset] = None

        try:
            logger.info(f"Creating precip panel for {output_key}")
            if cfgpcpn["show_precip"]:
                ds_p = await self._open_dataset_s3(cfgpcpn["pcpn_grib"])

            if cfgpcpn.get("show_jet_core", True):
                ds_js = await self._open_dataset_s3(cfgpcpn["jet_spd_grib"])

            plotter_pcpn = plotter_factory.get_pcpn_plotter()
            plotter_pcpn(cfgpcpn, ax=axpcpn, ds_p=ds_p, ds_js=ds_js)

            add_panel_title(
                axpcpn,
                f"{step}H PCPN" if cfgpcpn.get("show_precip", True) else "No PCPN at 00H",
                loc="bl",
            )
        finally:
            if ds_p is not None:
                ds_p.close()
            if ds_js is not None:
                ds_js.close()

        apply_4panel_frames(fig, axes, add_outer_border=True)

        valid_text = cfg500.get("valid_time_str", "")
        if valid_text:
            add_valid_time_stamp(fig, valid_text, height=0.04, fontsize=14)

        # Save the 4panel chart to S3. First save to a local temp file then write to S3.
        async with aiofiles.tempfile.NamedTemporaryFile(suffix=".png", mode="w+b") as f:
            fig.savefig(f.name, dpi=dpi, bbox_inches=None, pad_inches=0.0, facecolor="white")
            plt.close(fig)
            await f.seek(0)
            body = await f.read()
            await self._s3_client.put_object(output_key, body)
            logger.info(f"Saved: {output_key}")

    async def _make_4panel_charts(
        self, model: ECCCModel, init_ymd: str, init_hh: str, start_hour: int, end_hour: int, step: int
    ):
        _model_cfgs = {
            ECCCModel.GDPS: (CFG_500_GDPS, CFG_MSLP_GDPS, CFG_700_GDPS, CFG_PCPN_GDPS, gdps_fname),
            ECCCModel.RDPS: (CFG_500_RDPS, CFG_MSLP_RDPS, CFG_700_RDPS, CFG_PCPN_RDPS, rdps_fname),
        }
        cfg500_base, cfgmslp_base, cfg700_base, cfgpcpn_base, fname_builder = _model_cfgs[model]
        raster_addresser = WX4PanelChartAddresser(init_ymd, init_hh, model)
        config_builder = ConfigBuilder(
            init_ymd=init_ymd,
            init_hh=init_hh,
            raster_addresser=raster_addresser,
            cfg500=cfg500_base,
            cfgmslp=cfgmslp_base,
            cfg700=cfg700_base,
            cfgpcpn=cfgpcpn_base,
            file_name_builder=fname_builder,
            model=model,
        )
        plotter_factory = PlotterFactory(model=model)
        for fh in range(start_hour, end_hour + 1, step):
            logger.info(
                f"Start {model} 4 panel chart generation for hour {fh} of model run {init_ymd}T{init_hh}Z."
            )
            output_name = f"{model}_{init_ymd}T{init_hh}Z_F{fh:03d}_4panel.png"
            output_key = raster_addresser.get_4panel_key(fh, output_name)

            # If a 4panel chart already exists don't re-create it.
            if await self._s3_client.object_exists(output_key):
                logger.info(f"Skipping: 4 panel chart already exists: {output_name}")
                continue

            cfg500, cfgmslp, cfg700, cfgpcpn = config_builder.build_config_for_hour(fh)

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

            try:
                await self._make_4panel_chart(
                    cfg500,
                    cfgmslp,
                    cfg700,
                    cfgpcpn,
                    DEFAULT_FIG_SIZE,
                    DEFAULT_DPI,
                    output_key,
                    plotter_factory,
                    step,
                )
            except TypeError:
                # Error was logged when thrown. Continue processing of remaining 4panel charts.
                continue
            logger.info(
                f"End {model} 4 panel chart generation for hour {fh} of model run {init_ymd}T{init_hh}Z."
            )
        # The specified end hour has been reached and the processing is complete.
        return True

    async def run(
        self,
        init_ymd: str,
        model_runs: List[str],
        start_hour: int,
        end_hour: int,
        step: int,
        model: ECCCModel,
    ):
        if model not in ModelNames:
            raise ValueError(f"Model must be one of {list(ModelNames)}, received {model}")
        for init_hh in model_runs:
            model_run_time = time(int(init_hh))
            init_datetime = datetime.strptime(init_ymd, "%Y%m%d")
            model_run_timestamp = datetime.combine(init_datetime.date(), model_run_time).replace(
                tzinfo=timezone.utc
            )
            async with get_async_write_session_scope() as session:
                chart = await get_or_create_processed_four_panel_chart(
                    session, model, model_run_timestamp
                )

                if chart is not None and chart.status == ChartStatusEnum.INPROGRESS:
                    complete = await self._make_4panel_charts(
                        model, init_ymd, init_hh, start_hour, end_hour, step
                    )
                    if complete:
                        chart.status = ChartStatusEnum.COMPLETE
                        chart.update_date = get_utc_now()
                        save_four_panel_chart(session, chart)
                        logger.info(
                            f"Successfully generated {model} 4 panel charts for {init_ymd}."
                        )
                    else:
                        logger.info(
                            f"Could not generate all {model} 4 panel charts for {init_ymd}."
                        )


async def get_init_datetime():
    """
    Determine the UTC datetime at which to start processing

    :return: A UTC datetime object.
    """
    #
    async with get_async_read_session_scope() as session:
        now = get_utc_now()
        now = now.replace(hour=0, minute=0, second=0, microsecond=0)
        min_date = now - timedelta(days=7)
        # Limit lookup to 7 days in the past as we prune grib files older than 7 days
        init_datetime: Optional[datetime] = None
        incomplete_result = await get_earliest_in_progress_date_limited(session, min_date)
        if incomplete_result is not None:
            # Try generating charts from a previous day that were incomplete
            init_datetime: datetime = incomplete_result.model_run_timestamp
        else:
            # Lookup the last complete run in the past 7 days
            last_complete_result = await get_last_complete(session, min_date)
            if last_complete_result is not None:
                init_datetime: datetime = last_complete_result.model_run_timestamp + timedelta(
                    days=1
                )
        if init_datetime is None:
            # Begin processing from today at 0:00 UTC if no useful result returned from db
            init_datetime = now

        return init_datetime.replace(hour=0, minute=0, second=0, microsecond=0)


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
        default=["00", "12"],
        help="Model run hour(s).",
    )
    parser.add_argument(
        "--start_hour",
        type=int,
        default=0,
        help="The first prediction hour to generate a chart for.",
    )
    parser.add_argument(
        "--end_hour", type=int, default=84, help="The last prediction hour to generate a chart for."
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

    if args.init_ymd is None:
        now = get_utc_now()
        start_datetime = await get_init_datetime()
        end_datetime = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # If an init_ymd was provided as an argument, only process that one day
        start_datetime = datetime.strptime(args.init_ymd, "%Y%m%d").replace(tzinfo=timezone.utc)
        end_datetime = start_datetime

    user_id = config.get("WX_OBJECT_STORE_USER_ID")
    secret_key = config.get("WX_OBJECT_STORE_SECRET")
    bucket = config.get("WX_OBJECT_STORE_BUCKET")
    cartopy_data_dir = "/app/.local/share/cartopy"
    cartopy.config["data_dir"] = cartopy_data_dir

    async with S3Client(user_id=user_id, secret_key=secret_key, bucket=bucket) as s3_client:
        try:
            current_datetime = start_datetime
            while current_datetime <= end_datetime:
                init_ymd = current_datetime.strftime("%Y%m%d")
                logger.info(f"Creating {args.model} 4 panel chart for model run {init_ymd}.")
                logger.info(f"Model run hour(s) {args.model_runs}")
                logger.info(
                    f"From hour {args.start_hour} to {args.end_hour} in {args.step} hour increments."
                )

                runner = FourPanelChartRunner(s3_client)
                await runner.run(
                    init_ymd, args.model_runs, args.start_hour, args.end_hour, args.step, args.model
                )
                current_datetime = current_datetime + timedelta(days=1)

            # Exit with 0 - success.
            sys.exit(os.EX_OK)
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
