import enum
from sqlalchemy import (Integer, String, Column, Index, ForeignKey, Enum, UniqueConstraint)
from geoalchemy2 import Geometry

from app.db.database import Base


class AreaTypeEnum(enum.Enum):
    fire_centre = 1
    fire_zone = 2


class AreaType(Base):
    """ Identify some kind of area type, e.g. "Zone", or "Fire" """
    __tablename__ = 'advisory_area_types'
    __table_args__ = (
        {'comment': 'Identify kind of advisory area (e.g. Zone, Fire etc.)'}
    )

    id = Column(Integer, primary_key=True)
    name = Column(Enum(AreaTypeEnum), nullable=False, unique=True, index=True)


class Area(Base):
    """ Identify some area of interest with respect to advisories. """
    __tablename__ = 'advisory_areas'
    __table_args__ = (
        # we may have to re-visit this constraint - but for the time being, the idea is
        # that for any given type of area, it has to be unique for the kind of thing that
        # it is. e.g. a zone has some id.
        UniqueConstraint('external_identifier', 'area_type'),
        {'comment': 'Record identifying some area of interest with respect to advisories'}
    )

    id = Column(Integer, primary_key=True)
    # An area is uniquely identified, e.g. a zone has a number, so does a fire.
    external_identifier = Column(String, nullable=False, index=True)
    area_type = Column(Integer, ForeignKey('advisory_area_types.id'), nullable=False, index=True)
    geom = Column(Geometry('MULTIPOLYGON', spatial_index=False), nullable=False)


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_advisory_areas_geom', Area.geom, postgresql_using='gist')
