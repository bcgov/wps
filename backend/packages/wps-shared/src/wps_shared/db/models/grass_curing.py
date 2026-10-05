from wps_shared.db.models import Base
from sqlalchemy import (Column, Float, Integer, Sequence)
from wps_shared.db.models.common import TZTimeStamp


class PercentGrassCuring(Base):
    """ Daily percent grass curing per weather station. """
    __tablename__ = 'percent_grass_curing'
    __table_args__ = (
        {'comment': 'Record containing information about percent grass curing from the CWFIS.'}
    )

    id = Column(Integer, Sequence('percent_grass_curing_id_seq'),
                primary_key=True, nullable=False, index=True)
    station_code = Column(Integer, nullable=False, index=True)
    percent_grass_curing = Column(Float, nullable=False, index=False)
    for_date = Column(TZTimeStamp, nullable=False, index=True)
   