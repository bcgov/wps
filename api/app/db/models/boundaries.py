
from sqlalchemy import (Column, String, Integer, Sequence)
from geoalchemy2 import Geometry
from app.db.database import Base


class FireCentres(Base):
    """ Records containing polygons that define fire centers """
    __tablename__ = 'fire_centers'
    __table_args__ = (
        {'comment': 'Bounds for fire centres'}
    )

    id = Column(Integer, Sequence('fire_centers_id_seq'),
                primary_key=True, nullable=False, index=True)
    geom = Column(Geometry('POLYGON'), nullable=False)
    name = Column(String, nullable=False, unique=True)
