""" Class model that reflect resources and map to database tables relating audits created
by authenticated user requests.
"""
import enum
import logging
from datetime import datetime
from sqlalchemy.types import TypeDecorator
from sqlalchemy import (Column, Enum, Index, Integer, String, TIMESTAMP)
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from sqlalchemy.ext.declarative import declarative_base
import geoalchemy2

# constructing a base class for declarative class definitions
Base = declarative_base()

""" Types etc. common to models
"""

logger = logging.getLogger(__name__)


class TZTimeStamp(TypeDecorator):  # pylint: disable=abstract-method
    """ TimeStamp type that ensures that timezones are always specified.
    If the timezone isn't specified, you aren't guaranteed that you're going to get consistent times. """
    impl = TIMESTAMP(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if isinstance(value, datetime) and value.tzinfo is None:
            logger.warning('type:%s tzinfo:%s', type(value), value.tzinfo)
            raise ValueError('{!r} must be TZ-aware'.format(value))
        return value

    def __repr__(self):
        return 'TZTimeStamp()'


class RunType(enum.Enum):
    FORECAST = 'forecast'
    ACTUAL = 'actual'


class HFI(Base):
    """ Class representing table structure of processed HFI by
    run date and time
    """
    __tablename__ = 'hfi'
    __table_args__ = (
        {'comment': 'Processed HFI by run date and time'}
    )
    id = Column(Integer, primary_key=True)
    hfi = Column(String, nullable=True, index=True)
    geom = Column(geoalchemy2.types.Geometry(geometry_type='MULTIPOLYGON',
                                             srid=3005,
                                             spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False)
    run_date = Column(TZTimeStamp, nullable=False)
    for_date = Column(TZTimeStamp, nullable=False)
    run_type = Column(Enum(RunType), nullable=False)


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_hfi_geom',
      HFI.geom, postgresql_using='gist')
# Explict creation of index for multi index
Index('sfms_run_multiindex', HFI.run_date, HFI.for_date, HFI.run_type)


class FireCentre(Base):
    """ Class representing table structure of a fire centre
    """
    __tablename__ = 'fire_centre'
    __table_args__ = (
        {'comment': 'BC fire centre boundaries'}
    )
    id = Column(Integer, primary_key=True)
    feature_id = Column(Integer, nullable=False)
    geom = Column(geoalchemy2.types.Geometry(geometry_type='Polygon',
                                             srid=4326,
                                             spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False)
    create_date = Column(TZTimeStamp, nullable=False)
    update_date = Column(TZTimeStamp, nullable=False)
    mof_fire_centre_id = Column(Integer)
    mof_fire_centre_name = Column(String)
    objectid = Column(Integer)
    feature_area_sqm = Column(DOUBLE_PRECISION)
    feature_length_m = Column(DOUBLE_PRECISION)
    geometry_area = Column(Integer, name="geometry.area")
    geometry_len = Column(Integer, name="geometry.len")


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_fire_centre_geom',
      FireCentre.geom, postgresql_using='gist')


# CREATE TABLE fire_centres (
#     id SERIAL PRIMARY KEY,
#     feature_id integer NOT NULL,
#     geom geometry(Polygon,4326) NOT NULL,
#     create_date timestamp with time zone NOT NULL,
#     update_date timestamp with time zone NOT NULL,
#     mof_fire_centre_id integer,
#     mof_fire_centre_name text,
#     objectid integer,
#     feature_area_sqm double precision,
#     feature_length_m double precision,
#     "geometry.area" integer,
#     "geometry.len" integer
# );

# -- Indices -------------------------------------------------------

# CREATE UNIQUE INDEX fire_centres_pkey ON fire_centres(id int4_ops);
# CREATE INDEX idx_fire_centres_geom ON fire_centres USING GIST (geom gist_geometry_ops_2d);
