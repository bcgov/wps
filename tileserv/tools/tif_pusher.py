import sys
import asyncio
import logging
from datetime import date
import requests
import pandas as pd
from decouple import config

from s3 import get_tifs_for_date

import pdb

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def build_post_body_for_tiff(tif_object, run_date: date):
    key: str = tif_object["Key"]
    for_date_str: str = tif_object["Key"].split("hfi")[1].split(".")[0]
    for_date: str = date(year=int(for_date_str[0:4]), month=int(
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
        tif_objects = await get_tifs_for_date(current_date)
        for tif_object in tif_objects:
            post_body = build_post_body_for_tiff(tif_object, current_date)
            logger.info(post_body)
            response = requests.post(url=config("URL"), json=post_body, headers={
                "Secret": config("SECRET"), "Content-Type": "application/json"})
            pdb.set_trace()
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
