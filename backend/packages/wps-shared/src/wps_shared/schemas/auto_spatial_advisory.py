""" Schemas used for serializing and deserializing data that is published on the message queue.
"""
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel


class SFMSRunType(Enum):
    FORECAST = 'forecast'
    ACTUAL = 'actual'


class SFMSFile(BaseModel):
    """ SFMS File - this schema used to store messages on the queue """
    version: str = '0.0.1'
    key: str  # S3 key
    run_type: SFMSRunType  # forecast or actual
    last_modified: datetime  # last modified date as provided by windows file system when uploaded
    create_time: datetime  # create time as provided by windows file system when uploaded
    run_date: date  # date of the run
    for_date: date  # date of interest


class ManualSFMS(BaseModel):
    key: str  # S3 key
    for_date: date
    runtype: SFMSRunType
    run_date: date  # The date that this run is on, the date folder path in s3
