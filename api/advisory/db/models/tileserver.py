""" We don't want alembic to manage the models in here!
"""

from sqlalchemy import (Column, Integer, Date, String)
from geoalchemy2 import Geometry
from app.db.database import Base


class Hfi(Base):
    """ This table manually created - by running ogr2ogr on the classified geojson - see polygonize_hfi.py
    """
    __tablename__ = 'hfi'
    ogc_fid = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    wkb_geometry = Column(Geometry('POLYGON'))


class FireZone(Base):
    """ This table manually created - see wps-tileserver project for details!
    """
    __tablename__ = 'fire_zones'
    id = Column(Integer, primary_key=True, index=True)
    mof_fire_zone_id = Column(Integer)
    geom = Column(Geometry('MULTIPOLYGON'))
    mof_fire_zone_name = Column(String)
