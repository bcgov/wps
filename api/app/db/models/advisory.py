import enum
from sqlalchemy import (Integer, Float, Date, String, Column, Index, ForeignKey, Enum, UniqueConstraint)
from geoalchemy2 import Geometry
from app.db.database import Base


class FireZoneAdvisory(Base):
    """ 
    TODO: this needs unique constrainsts etc. etc.
    TODO: i think we're getting rid of this soon?
    """
    __tablename__ = 'advisory_fire_zones'
    __table_args__ = (
        {'comment': 'Information about advisories.'}
    )
    id = Column(Integer, primary_key=True, index=True)
    for_date = Column(Date, nullable=False, index=True)
    # TODO: the official spec has two different numbers!
    mof_fire_zone_id = Column(Integer, nullable=False, index=True)
    elevated_hfi_area = Column(Float, nullable=False)
    elevated_hfi_percentage = Column(Float, nullable=False)


class ShapeTypeEnum(enum.Enum):
    """ Define different shape types. e.g. "Zone", "Fire Centre" - later we may add
    "Incident"/"Fire", "Custom" etc. etc. """
    fire_centre = 1
    fire_zone = 2


class ShapeType(Base):
    """ Identify some kind of area type, e.g. "Zone", or "Fire" """
    __tablename__ = 'advisory_shape_types'
    __table_args__ = (
        {'comment': 'Identify kind of advisory area (e.g. Zone, Fire etc.)'}
    )

    id = Column(Integer, primary_key=True)
    name = Column(Enum(ShapeTypeEnum), nullable=False, unique=True, index=True)


class Shape(Base):
    """ Identify some area of interest with respect to advisories. """
    __tablename__ = 'advisory_shapes'
    __table_args__ = (
        # we may have to re-visit this constraint - but for the time being, the idea is
        # that for any given type of area, it has to be unique for the kind of thing that
        # it is. e.g. a zone has some id.
        UniqueConstraint('source_identifier', 'shape_type'),
        {'comment': 'Record identifying some area of interest with respect to advisories'}
    )

    id = Column(Integer, primary_key=True)
    # An area is uniquely identified, e.g. a zone has a number, so does a fire.
    source_identifier = Column(String, nullable=False, index=True)
    shape_type = Column(Integer, ForeignKey('advisory_shape_types.id'), nullable=False, index=True)
    geom = Column(Geometry('MULTIPOLYGON', spatial_index=False, srid=3005), nullable=False)
    # The area in square meters of the shape's geom that has combustible fuels in it,
    # according to the fuel type layer
    combustible_area = Column(Float, nullable=True)
    # Optional name that can be used to help identify the shape
    name = Column(String, nullable=True)


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_advisory_areas_geom', Shape.geom, postgresql_using='gist')


class ClassifiedHfi(Base):
    """ TODO: Do!
    """
    __tablename__ = 'advisory_classified_hfi'
    id = Column(Integer, primary_key=True, index=True)
    # TODO: we could do this better!
    hfi = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    geom = Column(Geometry('POLYGON', spatial_index=False, srid=3005))


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_advisory_classified_hfi_geom', ClassifiedHfi.geom, postgresql_using='gist')
