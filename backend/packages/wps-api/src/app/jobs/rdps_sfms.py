"""
A script that downloads RDPS temp, rh, precip and wind speed weather model data from the Environment Canada HTTP data server.
Data is stored in S3 storage for a maximum of 7 days
"""

import asyncio
import os
import sys
from datetime import timedelta, datetime, timezone
from collections.abc import Generator
import logging
import tempfile
import aiofiles
from sqlalchemy.orm import Session
from wps_shared.db.database import get_write_session_scope
from wps_shared.db.crud.weather_models import (
    create_model_run_for_sfms,
    create_saved_model_run_for_sfms_url,
    get_saved_model_run_for_sfms,
    get_rdps_sfms_urls_for_deletion,
    delete_rdps_sfms_urls,
)
from wps_shared.utils.s3_client import S3Client
from wps_shared.weather_models import CompletedWithSomeExceptions, download
from wps_shared.weather_models import ModelEnum
from wps_shared.wps_logging import configure_logging
import wps_shared.utils.time as time_utils
from wps_shared.utils.s3 import apply_retention_policy_on_date_folders, get_client
from wps_shared.rocketchat_notifications import send_rocketchat_notification
from wps_shared.weather_models.job_utils import get_regional_model_run_download_urls
from app.weather_models.precip_rdps_model import compute_and_store_precip_rasters
from wps_shared.sfms.rdps_filename_marshaller import model_run_for_hour

# If running as its own process, configure logging appropriately.
if __name__ == "__main__":
    configure_logging()

logger = logging.getLogger(__name__)


DAYS_TO_RETAIN = 7
MAX_MODEL_RUN_HOUR = 45
GRIB_LAYERS = {
    "temp": "TMP_TGL_2",
    "rh": "RH_TGL_2",
    "precip": "APCP_SFC_0",
    "wind_speed": "WIND_TGL_10",
}


def get_model_run_hours_to_process() -> Generator[int, None, None]:
    """Yield the 00 and 12 model run hours for RDPS (skip 06 and 18 for now)"""
    for hour in [0, 12]:
        yield hour


class RDPSGrib:
    """Class that orchestrates downloading, storage and retention policy of RDPS grib files."""

    def __init__(self, session: Session):
        """Prep variables"""
        self.files_downloaded = 0
        self.exception_count = 0
        # We always work in UTC:
        self.now = time_utils.get_utc_now()
        self.date_key = self.now.date().isoformat()
        self.session = session

    def _get_file_name_from_url(self, url: str) -> str:
        """Parses the grib file name from the URL. URLs have the form:
        https://dd.weather.gc.ca/model_gem_regional/10km/grib2/00/000/CMC_reg_TMP_TGL_2_ps10km_2024061700_P000.grib2
        """
        parts = url.split("/")
        name = parts[-1]
        return name

    def _generate_s3_key(self, model_run_hour: int, weather_param: str, file_name) -> str:
        """Creates a key for storing an object in S3 storage."""
        return f"weather_models/{(ModelEnum.RDPS).lower()}/{self.date_key}/{model_run_hour:02d}/{weather_param}/{file_name}"

    async def _process_model_run_urls(
        self, model_run_hour: int, weather_param: str, urls: list[str]
    ):
        """Process the urls for a model run."""
        for url in urls:
            try:
                # check the database for a record of this file:
                processed_url = get_saved_model_run_for_sfms(self.session, url)
                if processed_url:
                    # This url has already been processed - so we skip it.
                    logger.debug("file already processed %s", url)
                    continue
                else:
                    # download the file:
                    with tempfile.TemporaryDirectory() as temporary_path:
                        downloaded = download(
                            url,
                            temporary_path,
                            "REDIS_CACHE_ENV_CANADA",
                            ModelEnum.RDPS,
                            "REDIS_ENV_CANADA_CACHE_EXPIRY",
                        )
                        if downloaded:
                            self.files_downloaded += 1
                            file_name = self._get_file_name_from_url(url)
                            key = self._generate_s3_key(model_run_hour, weather_param, file_name)
                            # If we've downloaded the file ok, we can now save it to S3 storage.
                            try:
                                async with get_client() as (client, bucket):
                                    async with aiofiles.open(downloaded, "rb") as f:
                                        file_content = await f.read()
                                    await client.put_object(
                                        Bucket=bucket, Key=key, Body=file_content
                                    )
                                    create_saved_model_run_for_sfms_url(self.session, url, key)
                            finally:
                                # delete the file when done.
                                os.remove(downloaded)
            except Exception as exception:
                self.exception_count += 1
                # We catch and log exceptions, but keep trying to download.
                # We intentionally catch a broad exception, as we want to try and download as much
                # as we can.
                logger.error("unexpected exception processing %s", url, exc_info=exception)

    async def _process_model_run(self, model_run_hour: int):
        """Process a particular RDPS model run"""
        logger.info(f"Processing RDPS model run {model_run_hour}Z")
        for key, value in GRIB_LAYERS.items():
            urls = list(
                get_regional_model_run_download_urls(
                    self.now, model_run_hour, [value], MAX_MODEL_RUN_HOUR
                )
            )
            await self._process_model_run_urls(model_run_hour, key, urls)

    async def process(self):
        """Entry point for downloading and processing RDPS weather model grib files"""
        for hour in get_model_run_hours_to_process():
            try:
                await self._process_model_run(hour)
                if self.files_downloaded > 0:
                    create_model_run_for_sfms(self.session, ModelEnum.RDPS, self.now, hour)
            except Exception as exception:
                # We catch and log exceptions, but keep trying to process.
                # We intentionally catch a broad exception, as we want to try to process as much as we can.
                self.exception_count += 1
                logger.error(
                    "unexpected exception processing %s model run %d",
                    self.model_type,
                    hour,
                    exc_info=exception,
                )

    async def apply_retention_policy(self, days_to_retain: int):
        """Delete objects from S3 storage and remove records from database that are older than DAYS_TO_RETAIN"""
        logger.info(
            f"Applying retention policy to RDPS data downloaded for SFMS. Data in S3 and corresponding database records older than {days_to_retain} days are being deleted."
        )
        prefix = "weather_models/rdps/"
        async with S3Client() as client:
            await apply_retention_policy_on_date_folders(client, prefix, days_to_retain)

        deletion_threshold = self.now - timedelta(days=days_to_retain)
        records_for_deletion = get_rdps_sfms_urls_for_deletion(self.session, deletion_threshold)
        ids_for_deletion = list(record.id for record in records_for_deletion)
        delete_rdps_sfms_urls(self.session, ids_for_deletion)
        logger.info(f"Completed deleting {len(records_for_deletion)} objects and records.")


class RDPSJob:
    async def run(self):
        # Add some check based on current time and previous runs to determine if we need to proceed
        logger.info("Begin download and storage of RDPS gribs.")

        # grab the start time.
        start_time = time_utils.get_utc_now()

        # start our computing at the utc datetime of the most recent model run
        model_run_hour = model_run_for_hour(start_time.hour)
        model_start_time = datetime(
            start_time.year, start_time.month, start_time.day, model_run_hour, tzinfo=timezone.utc
        )
        with get_write_session_scope() as session:
            rdps_grib = RDPSGrib(session)
            await rdps_grib.process()
            await rdps_grib.apply_retention_policy(DAYS_TO_RETAIN)
            await compute_and_store_precip_rasters(model_start_time)
        # calculate the execution time.
        execution_time = time_utils.get_utc_now() - start_time
        hours, remainder = divmod(execution_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # log some info.
        logger.info(
            "%d downloaded, time taken %d hours, %d minutes, %d seconds (%s)",
            rdps_grib.files_downloaded,
            hours,
            minutes,
            seconds,
            execution_time,
        )
        # check if we encountered any exceptions.
        if rdps_grib.exception_count > 0:
            # if there were any exceptions, return a non-zero status.
            raise CompletedWithSomeExceptions()


def main():
    """Kicks off asynchronous downloading and storage of RDPS weather model data."""
    try:
        logger.debug("Begin download and storage of RDPS NWM data.")

        job = RDPSJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(job.run())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error(
            "An error occurred while downloading and storing RDPS data.", exc_info=exception
        )
        rc_message = ":scream: Encountered an error while processing RDPS data."
        send_rocketchat_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
