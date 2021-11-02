
import logging
import asyncio
import os
from app.weather_models.env_canada import get_model_run_hours, download
from app.c_haines.severity_index import model_prediction_hour_iterator, make_model_run_download_urls
from app.weather_models import ModelEnum, ProjectionEnum
from app import configure_logging
import app.utils.time as time_utils

logger = logging.getLogger(__name__)


def make_model_levels(model, prediction_hour):
    # https://weather.gc.ca/grib/GLB_HR/GLB_latlonp24xp24_P000_deterministic_e.html
    # showalter, uses temperature 500mb - 850mb
    if prediction_hour == 0:
        return ['TMP_ISBL_500', 'DEPR_ISBL_500', 'TMP_ISBL_700', 'TMP_ISBL_850', 'DEPR_ISBL_850', 'APCP_SFC_0', 'ACPCP_SFC_0', 'TMP_TGL_2', 'CAPE_SFC_0', 'SHOWA_SFC_0']
    else:
        return ['TMP_ISBL_500', 'DEPR_ISBL_500', 'TMP_ISBL_700', 'TMP_ISBL_850', 'DEPR_ISBL_850', 'APCP_SFC_0', 'ACPCP_SFC_0', 'TMP_TGL_2', 'CAPE_SFC_0', 'SHOWA_SFC_0']


def get_target(url):
    full = url[25:]
    folder = full[:full.rfind('/')]
    filename = full[full.rfind('/')+1:]
    return folder, filename


async def main():
    models = ((ModelEnum.GDPS, ProjectionEnum.LATLON_15X_15),)
    for model, projection in models:
        logger.info('Downloading %s', model)
        utc_now = time_utils.get_utc_now()
        for model_hour in get_model_run_hours(model):
            for prediction_hour in model_prediction_hour_iterator(model):
                levels = make_model_levels(model, prediction_hour)
                urls, model_run_timestamp, prediction_timestamp = make_model_run_download_urls(
                    model, utc_now, model_hour, prediction_hour, levels)
                for level in levels:
                    # https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/00/000/CMC_glb_TMP_ISBL_700_latlon.15x.15_2021110200_P000.grib2
                    folder, filename = get_target(urls[level])
                    if not os.path.exists(folder):
                        os.makedirs(f'{folder}')
                    if not os.path.exists(f'{folder}/{filename}'):
                        print(
                            f'downloading {urls[level]} to {folder}/{filename}')
                        filename = download(urls[level], folder)
                    else:
                        print(f'{urls[level]} already downloaded')
    print('hello')

if __name__ == "__main__":
    configure_logging()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
