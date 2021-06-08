
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
                         'station_code',
                         'temp_valid',
                         'temperature',
                         'rh_valid',
                         'relative_humidity',
                         'wdir_valid',
                         'wind_direction',
                         'wspeed_valid',
                         'wind_speed',
                         'precip_valid',
                         'precipitation',
                         'gc',
                         'ffmc',
                         'dmc',
                         'dc',
                         'isi',
                         'bui',
                         'fwi',
                         'danger_rating'),
        {'comment': 'The noon_forecast for a weather station and weather date.'}
    )
    id = Column(Integer, primary_key=True)
    weather_date = Column(TZTimeStamp, nullable=False, index=True)
    station_code = Column(Integer, nullable=False, index=True)
    temp_valid = Column(Boolean, default=False, nullable=False)
    temperature = Column(Float, nullable=False)
    rh_valid = Column(Boolean, default=False, nullable=False)
    relative_humidity = Column(Float, nullable=False)
    wdir_valid = Column(Boolean, default=False, nullable=False)
    # Set default wind_direction to NaN because some stations don't report it
    wind_direction = Column(Float, nullable=False, default=math.nan)
    wspeed_valid = Column(Boolean, default=False, nullable=False)
    wind_speed = Column(Float, nullable=False)
    precip_valid = Column(Boolean, default=False, nullable=False)
    precipitation = Column(Float, nullable=False)
    gc = Column(Float, nullable=False, default=math.nan)
    ffmc = Column(Float, nullable=False, default=math.nan)
    dmc = Column(Float, nullable=False, default=math.nan)
    dc = Column(Float, nullable=False, default=math.nan)
    isi = Column(Float, nullable=False, default=math.nan)
    bui = Column(Float, nullable=False, default=math.nan)
    fwi = Column(Float, nullable=False, default=math.nan)
    danger_rating = Column(Integer, nullable=False)
    created_at = Column(TZTimeStamp, nullable=False,
                        default=time_utils.get_utc_now(), index=True)

    def __str__(self):
        return (
            'station_code:{self.station_code}, '
            'weather_date:{self.weather_date}, '
            'created_at:{self.created_at}, '
            'temp={self.temperature}, '
            'ffmc={self.ffmc}'
        ).format(self=self)
