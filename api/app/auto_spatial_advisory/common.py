""" Shared common constants and functions for ASA.
"""
from enum import Enum
from datetime import date
from app.utils.time import get_hour_20, get_vancouver_now
from app import config
from typing import Final


class RunType(Enum):
    FORECAST = 'forecast'
    ACTUAL = 'actual'

    @staticmethod
    def from_str(label):
        if label in ('forecast', 'Forecast', 'FORECAST'):
            return RunType.FORECAST
        elif label in ('actual', 'Actual', 'ACTUAL'):
            return RunType.ACTUAL
        else:
            raise NotImplementedError


actual: Final = 'actual'
forecast: Final = 'forecast'


def get_tiff_key(run_type: RunType, run_date: date, for_date: date):
    bucket = config.get('OBJECT_STORE_BUCKET')
    # TODO what really has to happen, is that we grab the most recent prediction for the given date,
    # but this method doesn't even belong here, it's just a shortcut for now!
    for_date_string = f'{for_date.year}{for_date.month:02d}{for_date.day:02d}'

    # The filename in our object store, prepended with "vsis3" - which tells GDAL to use
    # it's S3 virtual file system driver to read the file.
    # https://gdal.org/user/virtual_file_systems.html
    key = f'/vsis3/{bucket}/sfms/uploads/{run_type.value}/{run_date.isoformat()}/hfi{for_date_string}.tif'
    return key


def get_date_part(filename: str) -> str:
    """ Get the date part of the filename.
    Filename example: hfi20220823.tif
    """
    return filename[filename.rfind('.') - 8:filename.rfind('.')]


def get_prefix(filename: str) -> str:
    """ 
    Get date from filename and delegate to determine
    whether it's and actual or forecast
    """
    file_date_string = get_date_part(filename)
    return get_prefix_from_file_date(file_date_string)


def get_prefix_from_file_date(file_date_string: str) -> str:
    """ Decide whether the file is an actual or forecast file.
    08h00 PST on the 22nd hfi20220823.tif -> forecast
    13h00 PST on the 22nd hfi20220823.tif -> forecast
    08h00 PST on the 23rd hfi20220823.tif -> forecast
    13h00 PST on the 23rd hfi20220823.tif -> actual
    """
    file_date = date(
        year=int(file_date_string[:4]),
        month=int(file_date_string[4:6]),
        day=int(file_date_string[6:8]))
    now = get_vancouver_now()
    now_date = now.date()

    if file_date < now_date:
        # It's from the past - it's an actual.
        return actual
    if file_date > now_date:
        # It's from the future - it's a forecast.
        return forecast
    # It's from today - now it gets weird.
    # If the current time is after solar noon, it's an actual.
    # If the current time is before solar noon, it's a forecast.
    solar_noon_today = get_hour_20(now)
    if now > solar_noon_today:
        return actual
    return forecast
