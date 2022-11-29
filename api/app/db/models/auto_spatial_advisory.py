import enum
from sqlalchemy import (Integer, Date, String, Float, Column, Index, ForeignKey, Enum, UniqueConstraint)
from app.db.models.common import TZTimeStamp
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
    forecast = "forecast"
    actual = "actual"


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
    # The area in square meters of the shape's geom that has combustible fuels in it,
    # according to the fuel type layer
    # Have to make this column nullable to start because the table already exists. Will be
    # modified in subsequent migration to nullable=False
    combustible_area = Column(Float, nullable=True)
    geom = Column(Geometry('MULTIPOLYGON', spatial_index=False, srid=NAD83_BC_ALBERS), nullable=False)


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_advisory_shapes_geom', Shape.geom, postgresql_using='gist')


class HfiClassificationThreshold(Base):
    __tablename__ = 'advisory_hfi_classification_threshold'
    __table_args__ = (
        {'comment': 'The Operational Safe Works Standards specifies that an hfi of greater than '
                    '4000 should result in an advisory. However in order for an FBAN to create '
                    'useful information, there are other thresholds of concern. E.g. > 10000'
         }
    )
    id = Column(Integer, primary_key=True, index=True)
    # e.g. '4000 < hfi < 10000' or 'hfi >= 10000'
    description = Column(String, nullable=False)
    # e.g. 'advisory' 'warning'
    name = Column(String, nullable=False)


class ClassifiedHfi(Base):
    """ HFI classified into different groups.
    NOTE: In actual fact, forecasts and actuals can be run multiple times per day,
    but we only care about the most recent one, so we only store the date, not the timesamp.
    """
    __tablename__ = 'advisory_classified_hfi'
    __table_args__ = (
        {'comment': 'HFI classification for some forecast/advisory run on some day, for some date'}
    )
    id = Column(Integer, primary_key=True, index=True)
    threshold = Column(Integer, ForeignKey('advisory_hfi_classification_threshold.id'), nullable=False, index=True)
    run_type = Column(Enum(RunTypeEnum), nullable=False, index=True)
    run_datetime = Column(TZTimeStamp, nullable=False)
    for_date = Column(Date, nullable=False)
    geom = Column(Geometry('POLYGON', spatial_index=False, srid=NAD83_BC_ALBERS))


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_advisory_classified_hfi_geom', ClassifiedHfi.geom, postgresql_using='gist')


class FuelType(Base):
    """ Identify some kind of fuel type. """
    __tablename__ = 'advisory_fuel_types'
    __table_args__ = (
        {'comment': 'Identify some kind of fuel type'}
    )
    id = Column(Integer, primary_key=True, index=True)
    fuel_type_id = Column(Integer, nullable=False, index=True)
    geom = Column(Geometry('POLYGON', spatial_index=False, srid=NAD83_BC_ALBERS))


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_advisory_fuel_types_geom', FuelType.geom, postgresql_using='gist')


class HighHfiArea(Base):
    """ Area exceeding HFI thresholds per fire zone. """
    __tablename__ = 'hfi_advisory_area'
    __table_args__ = (
        {'comment': 'Area under advisory/warning per fire zone.'}
    )
    id = Column(Integer, primary_key=True, index=True)
    source_identifier = Column(String, ForeignKey('advisory_shapes.source_identifier'), nullable=False, index=True)
    run_type = Column(Enum(RunTypeEnum), nullable=False)
    run_datetime = Column(TZTimeStamp, nullable=False)
    for_date = Column(Date, nullable=False)
    advisory_area = Column(Float, nullable=False)
    warn_area = Column(Float, nullable=False)
