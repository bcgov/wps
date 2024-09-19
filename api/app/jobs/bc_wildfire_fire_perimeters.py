import logging
import asyncio
import os
import sys
import tempfile
import bcdata
import json
from app.jobs.common_model_fetchers import download
from app import configure_logging
import app.utils.time as time_utils
from app.utils.s3 import get_client

logger = logging.getLogger(__name__)

DATASET = 'bc-wildfire-fire-perimeters-current'

class BCDATAgeojson:
    def __init__(self):
        self.now = time_utils.get_utc_now()
        self.date_key = self.now.date().isoformat()

    async def process(self):
        try:
            with tempfile.TemporaryDirectory() as tempdir:
                os.environ['BCDATA_CACHE'] = os.path.join(tempdir, "bcdata")
                geojson = bcdata.get_data(DATASET)
                if geojson:
                    filename = f"{DATASET}.json"
                    file_path = os.path.join(tempdir, filename)
                    with open(file_path, 'w') as f:
                        json.dump(geojson, f)  
                    today = time_utils.get_utc_now()
                    key = f"fire_perimeter/bcdata/{today}/{filename}"
                    try:
                        async with get_client() as (client, bucket):
                            await client.put_object(Bucket=bucket, Key=key, Body=open(file_path, "rb"))
                    finally:
                        os.remove(file_path)
        except Exception as e:
            logger.error("unexpected exception processing %s", exc_info=e)

class BCDATAJob:
    async def run(self):
        logger.info("Begin downloading of Current Fire Perimeter data")

        start_time = time_utils.get_utc_now()

        await BCDATAgeojson().process()

        execution_time = time_utils.get_utc_now() - start_time
        hours, remainder = divmod(execution_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        logger.info(
            "%d geojson, time taken %d hours, %d minutes, %d seconds (%s)",
            hours,
            minutes,
            seconds,
            execution_time,
        )

def main():
    try:
        logger.debug("Begin download and storage of BCData Current Fire Perimeter data.")

        job = BCDATAJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(job.run())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error("An error occurred while downloading and storing data.", exc_info=exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    # configure_logging()
    main()