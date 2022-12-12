import sys
import asyncio
import os
import pytz
import logging
from datetime import date, datetime
import requests

import os
import logging
from datetime import date
import pandas as pd
from decouple import config

from s3 import get_ordered_tifs_for_date

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_hfi_objects(objects):
    tif_objects = list(filter(lambda obj: obj["Key"].endswith('tif')
                              or obj["Key"].endswith('tiff'), objects))
    hfi_tif_objects = list(filter(lambda obj: os.path.basename(obj["Key"]).startswith('hfi'), tif_objects))
    return hfi_tif_objects


def normalize_datetime(last_modified: datetime):
    """
        SFMS generates data in the Vancouver timezone, but S3 returns UTC
    """
    vancouver_tz = pytz.timezone('America/Vancouver')
    return vancouver_tz.localize(datetime(year=last_modified.year,
                                          month=last_modified.month,
                                          day=last_modified.day,
                                          hour=last_modified.hour,
                                          minute=last_modified.minute,
                                          second=last_modified.second,
                                          microsecond=last_modified.microsecond))


def buildpost_body_for_tiff(tif_object, run_date: date):
    key: str = tif_object["Key"]
    for_date_str: str = tif_object["Key"].split("hfi")[1].split(".")[0]
    for_date: date = date(year=int(for_date_str[0:4]), month=int(
        for_date_str[4:6]), day=int(for_date_str[6:8])).isoformat()
    runtype = "forecast" if "forecast" in key else "actual"

    return {"key": key, "for_date": for_date, "runtype": runtype, "run_date": run_date.isoformat()}


async def push_tifs_to_api(start_date: date, end_date: date):
    """
        Given a start date and end date, look up forecasts and actuals for each date in order,
        processing each tif ordered by their last modified timestamp
    """
    daterange = pd.date_range(start_date, end_date, freq='D').date

    for current_date in daterange:
        ordered_tif_objects = await get_ordered_tifs_for_date(current_date)
        for tif_object in ordered_tif_objects:
            post_body = buildpost_body_for_tiff(tif_object, current_date)
            logger.info(post_body)
            response = requests.post(url=config("URL"), json=post_body, headers={
                "Secret": config("SECRET"), "Content-Type": "application/json"})
            logger.info(response)


async def main(start_date: date, end_date: date):
    logger.info('Generating SFMS uploads for start date: "%s" end date: "%s"',
                start_date.isoformat(), end_date.isoformat())
    await push_tifs_to_api(start_date, end_date)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python3 tif_pusher.py start_date end_date')
        sys.exit(1)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2])))
