""" Code related to managing SFMS output files.
"""
import os
from datetime import date
from typing import Final
from app.schemas.auto_spatial_advisory import SFMSFile, SFMSRunType
from app.utils.time import get_hour_20, get_vancouver_now
from app.auto_spatial_advisory.common import get_prefix, get_date_part


def is_hfi_file(filename: str) -> bool:
    "Returns true if filename starts with 'hfi'"
    return filename.startswith("hfi")


def get_target_filename(filename: str) -> str:
    """ Get the target filename, something that looks like this:
    bucket/sfms/upload/forecast/[issue date NOT TIME]/hfi20220823.tif
    bucket/sfms/upload/actual/[issue date NOT TIME]/hfi20220823.tif
    """
    # We are assuming that the local server time, matches the issue date. We assume that
    # right after a file is generated, this API is called - and as such the current
    # time IS the issue date.
    issue_date = get_vancouver_now()
    # depending on the issue date, we decide if it's a forecast or actual.
    prefix = get_prefix(filename)
    # create the filename
    return os.path.join('sfms', 'uploads', prefix, issue_date.isoformat()[:10], filename)


def get_sfms_file_message(filename: str, meta_data: dict) -> SFMSFile:
    """ Given the SFMS filename, and the current date (which we take as the issue date) create
    a SFMS File object.
    """

    key = get_target_filename(filename)
    prefix = get_prefix(filename)
    run_type = SFMSRunType(prefix)
    issue_date = get_vancouver_now().date()
    for_date = get_date_part(filename)

    return SFMSFile(key=key,
                    run_type=run_type,
                    last_modified=meta_data.get('last_modified'),
                    create_time=meta_data.get('create_time'),
                    run_date=issue_date,
                    for_date=date(year=int(for_date[0:4]),
                                  month=int(for_date[4:6]),
                                  day=int(for_date[6:8])))
