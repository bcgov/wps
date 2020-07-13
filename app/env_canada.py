""" A script that downloads weather models from Environment Canada HTTP data server
"""

import os
from pathlib import Path
from datetime import datetime
import logging
import time
import pytz
import wget

# pylint: disable=invalid-name, broad-except


# Cron job schedule times are based on the timezone of the master where the job is initiated.
tz = pytz.timezone('America/Vancouver')
logger = logging.getLogger()
logging.Formatter.converter = lambda *args: datetime.now(tz=tz).timetuple()
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)


def get_download_urls():
    """ Create a list of urls to download and return it """
    urls = []
    date = tz.localize(datetime.now()).strftime('%Y%m%d')  # YYYYMMDD

    # hh: model run start, in UTC [00, 12]
    # hhh: forecast hour [000, 003, 006, ..., 240]
    for hh in ['00', '12']:
        for h in range(81):
            hhh = format(h * 3, '03d')
            for level in ['TMP_TGL_2', 'RH_TGL_2']:
                base_url = 'https://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/{}/{}/'.format(
                    hh, hhh)
                filename = 'CMC_glb_{}_latlon.24x.24_{}{}_P{}.grib2'.format(
                    level, date, hh, hhh)
                url = base_url + filename
                urls.append(url)

    return urls


def download(url: str, path: str):
    """ Downloads file with given url and returns the full path of the downloaded file """
    try:
        return wget.download(url, path)
    except Exception as exception:
        logger.error('Download Failed, %s, url: %s', exception, url)


def main():
    """ main script """
    start_time = time.time()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    gdps_path = dir_path + '/downloads/gdps'

    Path(gdps_path).mkdir(parents=True, exist_ok=True)

    files = []
    urls = get_download_urls()
    for url in urls:
        downloaded = download(url, gdps_path)
        if downloaded:
            files.append(downloaded)

    for idx, file in enumerate(files, start=1):
        if idx == 1:
            print('\n')
        logger.info('%s', file)

    execution_time = round(time.time() - start_time, 1)
    logger.info('%d downloaded in total, took %s seconds',
                len(files), execution_time)


if __name__ == "__main__":
    main()
