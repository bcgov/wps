"""
Common functionality for ASA
"""

from datetime import date, datetime
from wps_shared import config
from wps_shared.run_type import RunType
from wps_shared.utils.time import convert_to_sfms_timezone


def get_hfi_s3_key(run_type: RunType, run_datetime: datetime, for_date: date):
    bucket = config.get("OBJECT_STORE_BUCKET")
    # TODO what really has to happen, is that we grab the most recent prediction for the given date,
    # but this method doesn't even belong here, it's just a shortcut for now!
    sfms_run_datetime = convert_to_sfms_timezone(run_datetime)
    for_date_string = f"{for_date.year}{for_date.month:02d}{for_date.day:02d}"

    # The filename in our object store, prepended with "vsis3" - which tells GDAL to use
    # it's S3 virtual file system driver to read the file.
    # https://gdal.org/user/virtual_file_systems.html
    key = f"/vsis3/{bucket}/sfms/uploads/{run_type.value}/{sfms_run_datetime.date().isoformat()}/hfi{for_date_string}.tif"
    return key
