
""" Class models that reflect resources and map to database tables relating to observed values
(a.k.a. hourlies)
"""
import math
from sqlalchemy import (Column, Integer, Float, Boolean, UniqueConstraint)
from app.db.database import Base
from app.db.models.common import TZTimeStamp
import app.time_utils as time_utils


class HourlyActual(Base):
    """ Class representing table structure of 'hourly_actuals' table in DB.
    Default float values of math.nan are used for the weather variables that are
    sometimes null (None), because Postgres evaluates None != None, so the unique
    constraint doesn't work on records with >=1 None values. But math.nan == math.nan
    """
    __tablename__ = 'hourly_actuals'
    __table_args__ = (
        UniqueConstraint('weather_date',
                         'station_code'),
        {'comment': 'The hourly_actuals for a weather station and weather date.'}
    )
    id = Column(Integer, primary_key=True)
    weather_date = Column(TZTimeStamp, nullable=False, index=True)
    station_code = Column(Integer, nullable=False, index=True)
    temp_valid = Column(Boolean, default=False, nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    dewpoint = Column(Float, nullable=False)
    rh_valid = Column(Boolean, default=False, nullable=False, index=True)
    relative_humidity = Column(Float, nullable=False)
    wdir_valid = Column(Boolean, default=False, nullable=False)
    # Set default wind_direction to NaN because some stations don't report it
    wind_direction = Column(Float, nullable=False, default=math.nan)
    wspeed_valid = Column(Boolean, default=False, nullable=False)
    wind_speed = Column(Float, nullable=False)
    precip_valid = Column(Boolean, default=False, nullable=False)
    precipitation = Column(Float, nullable=False)
    ffmc = Column(Float, nullable=False, default=math.nan)
    isi = Column(Float, nullable=False, default=math.nan)
    fwi = Column(Float, nullable=False, default=math.nan)
    created_at = Column(TZTimeStamp, nullable=False,
                        default=time_utils.get_utc_now())

    def __str__(self):
        return (
            'station_code:{self.station_code}, '
            'weather_date:{self.weather_date}, '
            'temperature :{self.temperature}, '
            'relative_humidity:{self.relative_humidity}'
        ).format(self=self)
