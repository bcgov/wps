""" Class models that reflect resources and map to database tables for HFI Calculator.
"""
from geoalchemy2.types import Geometry
from sqlalchemy import (Column, Integer,
                        Sequence, Index)
from app.db.models.common import TZTimeStamp
import app.utils.time as time_utils
from app.db.database import Base


class ThessianPolygonArea(Base):
    """ Thessian polygon for a given area """
    __tablename__ = 'thessian_polygon_area'

    id = Column(Integer, Sequence('thessian_polygon_areaid_seq'),
                primary_key=True, nullable=False, index=True)
    geom = Column(Geometry(geometry_type='POLYGON', spatial_index=False))

    create_date = Column(TZTimeStamp, nullable=False,
                         default=time_utils.get_utc_now())
    update_date = Column(TZTimeStamp, nullable=False,
                         default=time_utils.get_utc_now())

    def __str__(self):
        return (f'id: {self.id}')


Index('idx_thessian_polygon_area_geom', ThessianPolygonArea.geom, postgresql_using='gist')
