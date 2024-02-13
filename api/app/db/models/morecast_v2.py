from app.db.models import Base
from sqlalchemy import (Column, Float, Integer, String, Sequence)
from app.db.models.common import TZTimeStamp


class MorecastForecastRecord(Base):
    """ A forecast created within Morecast v2 """
    __tablename__ = 'morecast_forecast'

    id = Column(Integer, Sequence('morecast_forecast_id_seq'),
                primary_key=True, nullable=False, index=True)
    station_code = Column(Integer, nullable=False, index=True)
    for_date = Column(TZTimeStamp, nullable=False, index=True)
    temp = Column(Float, nullable=False, index=True)
    rh = Column(Integer, nullable=False, index=True)
    precip = Column(Float, nullable=False, index=True)
    wind_speed = Column(Float, nullable=False, index=True)
    wind_direction = Column(Integer, nullable=True, index=True)
    grass_curing = Column(Float, nullable=True, index=True)
    create_timestamp = Column(TZTimeStamp, nullable=False, index=True)
    create_user = Column(String, nullable=False)
    update_timestamp = Column(TZTimeStamp, nullable=False, index=True)
    update_user = Column(String, nullable=False)
