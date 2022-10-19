
""" Class models that reflect resources and map to database tables relating to forecasts made by weather
forecasters.
"""
import math
from sqlalchemy import (Column, Integer, Float, Boolean, UniqueConstraint)
from app.db.database import Base
from app.db.models.common import TZTimeStamp
import app.utils.time as time_utils


class NoonForecast(Base):
    """ Class representing table structure of 'noon_forecasts' table in DB.
    Default float values of math.nan are used for the weather variables that are
    sometimes null (None), because Postgres evaluates None != None, so the unique
    constraint doesn't work on records with >=1 None values. But math.nan == math.nan
    """
    __tablename__ = 'noon_forecasts'
    __table_args__ = (
        UniqueConstraint('weather_date',
                         'wfwx_update_date',
                         'station_code'),
        {'comment': 'The noon_forecast for a weather station and weather date.'}
    )
    id = Column(Integer, primary_key=True)
    weather_date = Column(TZTimeStamp, nullable=False, index=True)
    station_code = Column(Integer, nullable=False, index=True)
    temp_valid = Column(Boolean, nullable=False, default=False)
    temperature = Column(Float, nullable=False, default=math.nan)
    rh_valid = Column(Boolean, nullable=False, default=False)
    relative_humidity = Column(Float, nullable=False, default=math.nan)
    wdir_valid = Column(Boolean, nullable=False, default=False)
    # Set default wind_direction to NaN because some stations don't report it
    wind_direction = Column(Float, nullable=False, default=math.nan)
    wspeed_valid = Column(Boolean, nullable=False, default=False)
    wind_speed = Column(Float, nullable=False, default=math.nan)
    precip_valid = Column(Boolean, nullable=False, default=False)
    precipitation = Column(Float, nullable=False, default=math.nan)
    gc = Column(Float, nullable=False, default=math.nan)
    ffmc = Column(Float, nullable=False, default=math.nan)
    dmc = Column(Float, nullable=False, default=math.nan)
    dc = Column(Float, nullable=False, default=math.nan)
    isi = Column(Float, nullable=False, default=math.nan)
    bui = Column(Float, nullable=False, default=math.nan)
    fwi = Column(Float, nullable=False, default=math.nan)
    created_at = Column(TZTimeStamp, nullable=False,
                        default=time_utils.get_utc_now(), index=True)
    wfwx_update_date = Column(TZTimeStamp, nullable=False, index=True)

    def __str__(self):
        return (
            'station_code:{self.station_code}, '
            'weather_date:{self.weather_date}, '
            'created_at:{self.created_at}, '
            'wfwx_update_date:{self.wfwx_update_date}, '
            'temp={self.temperature}, '
            'ffmc={self.ffmc}'
        ).format(self=self)
