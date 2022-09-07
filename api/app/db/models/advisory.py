import enum
from sqlalchemy import (Integer, Date, String, Column, Index, ForeignKey, Enum, UniqueConstraint)
from geoalchemy2 import Geometry
from app.db.database import Base
from app.geospatial import NAD83_BC_ALBERS


class ShapeTypeEnum(enum.Enum):
    """ Define different shape types. e.g. "Zone", "Fire Centre" - later we may add
    "Incident"/"Fire", "Custom" etc. etc. """
    fire_centre = 1
    fire_zone = 2


class RunTypeEnum(enum.Enum):
    """ Define different run types. e.g. "Forecast", "Actual" """
    forecast = 1
    actual = 2


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
    geom = Column(Geometry('MULTIPOLYGON', spatial_index=False, srid=NAD83_BC_ALBERS), nullable=False)


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_advisory_areas_geom', Shape.geom, postgresql_using='gist')


class ClassifiedHfi(Base):
    """ TODO: Do!
    NOTE: In actual fact, forecasts and actuals can be run multiple times per day,
    but we only care about the most recent one, so we only store the date, not the timesamp.
    """
    __tablename__ = 'advisory_classified_hfi'
    __table_args__ = (
        UniqueConstraint('run_type', 'run_date', 'for_date'),
        {'comment': 'HFI classification for some forecast/advisory run on some day, for some date'}
    )
    id = Column(Integer, primary_key=True, index=True)
    # TODO: we could do this better!
    hfi = Column(String, nullable=False)
    run_type = Column(Enum(RunTypeEnum), nullable=False, index=True)
    run_date = Column(Date, nullable=False)
    for_date = Column(Date, nullable=False)
    geom = Column(Geometry('POLYGON', spatial_index=False, srid=NAD83_BC_ALBERS))


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_advisory_classified_hfi_geom', ClassifiedHfi.geom, postgresql_using='gist')
