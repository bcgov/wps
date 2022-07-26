""" We don't want alembic to manage the models in here!
"""

from sqlalchemy import (Column, Integer, Float, String, ForeignKey)
from geoalchemy2 import Geometry
from app.db.database import Base


class Hfi(Base):
    """ This table manually created - by running ogr2ogr on the classified geojson - see polygonize_hfi.py
    """
    __tablename__ = 'hfi'
    ogc_fid = Column(Integer, primary_key=True, index=True)
    wkb_geometry = Column(Geometry('POLYGON'))


class FireZone(Base):
    """ This table manually created - see wps-tileserver project for details!
    """
    __tablename__ = 'fire_zones'
    id = Column(Integer, primary_key=True, index=True)
    geom = Column(Geometry('MULTIPOLYGON'))
    mof_fire_zone_name = Column(String)


class FireZoneAdvisory(Base):
    """ This file manually created!!! What would it take to make alembic understand
    there are two different databases in this project? Messy?

    from app.db.database import get_hfi_read_session_scope
    from app.db.external_models.fba_advisory import FireZoneAdvisory
    from app.db.database import _hfi_read_engine

    FireZoneAdvisory.__table__.create(_hfi_read_engine)

    TODO: this needs unique constrainsts, dates etc. etc.
    """
    __tablename__ = 'fire_zone_advisory'
    id = Column(Integer, primary_key=True, index=True)
    fire_zone_id = Column(Integer, ForeignKey('fire_zones.id'), nullable=False, index=True)
    elevated_hfi_area = Column(Float, nullable=False)
