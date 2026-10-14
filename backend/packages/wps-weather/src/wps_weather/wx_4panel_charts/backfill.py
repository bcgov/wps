"""Download public ECCC inputs and generate real charts in a local object store."""

import argparse
import asyncio
import logging
from datetime import datetime

import cartopy
from wps_shared import config
from wps_shared.utils.object_store import get_endpoint_url, is_loopback_endpoint
from wps_shared.utils.s3_client import S3Client

from wps_weather.db.models.wx_4panel_charts import ECCCModel
from wps_weather.eccc_grib_consumer import FileToDownload, GribDownloader
from wps_weather.wx_4panel_charts.wx_4panel_charts import (
    FourPanelChartRunner,
    create_config_builder,
    get_required_grib_keys,
)

logger = logging.getLogger(__name__)

ECCC_BASE_URL = "https://dd.weather.gc.ca"
MODEL_LIMITS = {
    ECCCModel.GDPS: (6, 240),
    ECCCModel.RDPS: (3, 84),
}


def parse_date(value: str) -> str:
    """Require an explicit model-run date in the format used by ECCC paths."""
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError as error:
        raise argparse.ArgumentTypeError("date must use YYYYMMDD format") from error
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill public ECCC data and generate charts in the local object store."
    )
    parser.add_argument("--model", required=True, choices=[model.value for model in ECCCModel])
    parser.add_argument("--init-ymd", required=True, type=parse_date)
    parser.add_argument("--model-run", required=True, choices=["00", "12"])
    parser.add_argument("--start-hour", type=int, default=0)
    parser.add_argument("--end-hour", type=int, required=True)
    parser.add_argument("--max-concurrent-downloads", type=int, default=4)
    return parser.parse_args()


def validate_range(model: ECCCModel, start_hour: int, end_hour: int) -> int:
    """Validate a bounded model range and return its model-specific step."""
    step, max_hour = MODEL_LIMITS[model]
    if start_hour < 0 or end_hour < start_hour or end_hour > max_hour:
        raise ValueError(f"hours must satisfy 0 <= start <= end <= {max_hour} for {model.value}")
    if start_hour % step or end_hour % step:
        raise ValueError(f"hours must align to the {step}-hour {model.value} interval")
    return step


def source_url_for_key(key: str, init_ymd: str) -> str:
    """Translate a production-compatible GRIB key to its public ECCC source URL."""
    prefix = f"weather_models/{init_ymd}/"
    if not key.startswith(prefix):
        raise ValueError(f"Unexpected weather-model key: {key}")
    return f"{ECCC_BASE_URL}/{init_ymd}/WXO-DD/{key.removeprefix(prefix)}"


def build_downloads(
    model: ECCCModel,
    init_ymd: str,
    model_run: str,
    start_hour: int,
    end_hour: int,
    step: int,
) -> list[FileToDownload]:
    """Build the de-duplicated set of public inputs required by a chart range."""
    config_builder = create_config_builder(model, init_ymd, model_run)
    keys = {
        key
        for forecast_hour in range(start_hour, end_hour + 1, step)
        for key in get_required_grib_keys(config_builder, forecast_hour)
    }
    return [
        FileToDownload(url=source_url_for_key(key, init_ymd), s3_key=key) for key in sorted(keys)
    ]


async def download_inputs(
    s3_client: S3Client,
    downloads: list[FileToDownload],
    max_concurrent_downloads: int,
) -> None:
    """Download inputs concurrently and fail before chart generation if any are unavailable."""
    if max_concurrent_downloads < 1:
        raise ValueError("max-concurrent-downloads must be at least 1")

    semaphore = asyncio.Semaphore(max_concurrent_downloads)
    async with GribDownloader(s3_client) as downloader:

        async def download(file: FileToDownload) -> bool:
            async with semaphore:
                return await downloader.download_and_upload(file)

        results = await asyncio.gather(*(download(file) for file in downloads))

    failed_count = results.count(False)
    if failed_count:
        raise RuntimeError(f"Unable to download {failed_count} required ECCC input files")


async def run_backfill(args: argparse.Namespace) -> None:
    endpoint_url = get_endpoint_url()
    if not is_loopback_endpoint(endpoint_url):
        raise RuntimeError("Weather chart backfill requires a loopback object-store endpoint")

    model = ECCCModel(args.model)
    step = validate_range(model, args.start_hour, args.end_hour)
    downloads = build_downloads(
        model,
        args.init_ymd,
        args.model_run,
        args.start_hour,
        args.end_hour,
        step,
    )

    cartopy_data_dir = config.get("WX_CARTOPY_DATA_DIR")
    if cartopy_data_dir:
        cartopy.config["data_dir"] = cartopy_data_dir

    async with S3Client(
        user_id=config.get("WX_OBJECT_STORE_USER_ID"),
        secret_key=config.get("WX_OBJECT_STORE_SECRET"),
        bucket=config.get("WX_OBJECT_STORE_BUCKET"),
    ) as s3_client:
        await download_inputs(s3_client, downloads, args.max_concurrent_downloads)
        complete = await FourPanelChartRunner(s3_client).generate_range(
            model,
            args.init_ymd,
            args.model_run,
            args.start_hour,
            args.end_hour,
            step,
        )
        if not complete:
            raise RuntimeError("Chart generation stopped because required inputs were missing")

    logger.info(
        "Generated local %s charts for %sT%sZ from F%03d through F%03d",
        model.value,
        args.init_ymd,
        args.model_run,
        args.start_hour,
        args.end_hour,
    )


async def main() -> None:
    await run_backfill(parse_args())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
