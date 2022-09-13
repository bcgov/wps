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
    key: str  # S3 key
    run_type: SFMSRunType  # forecast or actual
    last_modified: datetime  # last modified date as provided by windows file system when uploaded
    create_time: datetime  # create time as provided by windows file system when uploaded
    run_date: date  # date of the run
    for_date: date  # date of interest
