import os
from app.auto_spatial_advisory.run_type import RunType
from datetime import date



def get_pmtiles_filepath(run_date: date, run_type: RunType, filename: str) -> str:
    """
    Get the file path for both reading and writing the pmtiles from/to the object store.
    Example: {bucket}/sfms/upload/actual/[issue/run_date]/hfi[for_date].pmtiles


    :param run_date: The date of the run to process. (when was the hfi file created?)
    :type run_date: date
    :param run_type: forecast or actual
    :type run_type: RunType
    :param filename: hfi[for_date].pmtiles -> hfi20230821.pmtiles
    :type filename: str
    :return: s3 bucket key for pmtiles file
    :rtype: str
    """
    pmtiles_filepath = os.path.join('psu', 'pmtiles', 'hfi', run_type.value, run_date.strftime('%Y-%m-%d'), filename)

    return pmtiles_filepath
