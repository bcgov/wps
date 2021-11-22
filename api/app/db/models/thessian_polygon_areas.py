""" Class models that reflect resources and map to database tables for HFI Calculator.
"""
from geoalchemy2.types import Geometry
from sqlalchemy import (Column, Integer,
                        Sequence)
from app.db.database import Base


class ThessianPolygonArea(Base):
    """ Thessian polygon for a given area """
    __tablename__ = 'fire_area_thessian_polygons'

    id = Column(Integer, Sequence('thessian_area_id_seq'),
                primary_key=True, nullable=False, index=True)
    polygon = Column(Geometry(geometry_type='POLYGON', from_text='ST_GeomFromGeoJSON'))

    def __str__(self):
        return (f'id:{self.id}, '
                f'fire_center:{self.polygon}')
