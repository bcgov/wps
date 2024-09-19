import logging
import asyncio
import os
import sys
import tempfile
from app.jobs.common_model_fetchers import download

from app import configure_logging
import app.utils.time as time_utils
from app.utils.s3 import get_client


MODIS_URL = "https://firms.modaps.eosdis.nasa.gov/api/kml_fire_footprints/canada/7/c6.1/FirespotArea_canada_c6.1_48.kmz"

logger = logging.getLogger(__name__)

class FIRMSkmz:
    def __init__(self):
        self.files_downloaded = 0
        self.exception_count = 0
        self.now = time_utils.get_utc_now()
        self.date_key = self.now.date().isoformat()

    def _get_filename_from_url(self, url: str) -> str:
        """Parses the grib file name from the URL. URLs have the form:
        https://firms.modaps.eosdis.nasa.gov/api/kml_fire_footprints/canada/48h/c6.1/FirespotArea_canada_c6.1_48.kmz
        """
        parts = url.split("/")
        name = parts[-1]
        return name

    def _generate_s3_key(self, file_name: str) -> str:
        return f"fire_perimeter/firms/modis1km/{self.date_key}/{file_name}"

    async def process(self):
        try:
            with tempfile.TemporaryDirectory() as tempdir:
                downloaded = download(MODIS_URL, tempdir, "REDIS_CACHE_FIRMS", config_cache_expiry_var=10)
                if downloaded:
                    self.files_downloaded += 1
                    filename = self._get_filename_from_url(MODIS_URL)
                    file_path = os.path.join(tempdir, filename)
                    key = self._generate_s3_key(filename)

                    try:
                        async with get_client() as (client, bucket):
                            await client.put_object(Bucket=bucket, Key=key, Body=open(file_path, "rb"))
                    finally:
                        os.remove(downloaded)
        except Exception as e:
            self.exception_count += 1
            logger.error("unexpected exception processing %s", MODIS_URL, exc_info=e)


class FIRMSJob:
    async def run(self):
        logger.info("Begin downloading of FIRMS kmz data")

        start_time = time_utils.get_utc_now()

        firms_kmz = FIRMSkmz()
        await firms_kmz.process()

        execution_time = time_utils.get_utc_now() - start_time
        hours, remainder = divmod(execution_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        logger.info(
            "%d downloaded, time taken %d hours, %d minutes, %d seconds (%s)",
            firms_kmz.files_downloaded,
            hours,
            minutes,
            seconds,
            execution_time,
        )


def main():
    try:
        logger.debug("Begin download and storage of FIRMS MODIS data.")

        job = FIRMSJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(job.run())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error("An error occurred while downloading and storing RDPS data.", exc_info=exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()
