""" Class model that reflect resources and map to database tables relating audits created
by authenticated user requests.
"""
import enum
import logging
from datetime import datetime
from sqlalchemy.types import TypeDecorator
from sqlalchemy import (Boolean, Column, Enum, Index, Integer, String, TIMESTAMP)
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
    snow_masked = Column(Boolean, nullable=False)


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_hfi_geom',
      HFI.geom, postgresql_using='gist')
# Explict creation of index for multi index
Index('sfms_run_multiindex', HFI.run_date, HFI.for_date, HFI.run_type)


class FireCentre(Base):
    """ Class representing table structure of a fire centre
    """
    __tablename__ = 'fire_centres'
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
Index('idx_fire_centres_geom',
      FireCentre.geom, postgresql_using='gist')


class FireCentreLabel(Base):
    """ Class representing table structure of a fire centre label
    """
    __tablename__ = 'fire_centres_labels'
    __table_args__ = (
        {'comment': 'BC fire centre labels'}
    )
    id = Column(Integer, primary_key=True)
    feature_id = Column(Integer, nullable=False)
    geom = Column(geoalchemy2.types.Geometry(geometry_type='Point',
                                             srid=4326,
                                             spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False)
    create_date = Column(TZTimeStamp, nullable=False)
    update_date = Column(TZTimeStamp, nullable=False)
    mof_fire_centre_id = Column(Integer)
    mof_fire_zone_name = Column(String)
    mof_fire_centre_name = Column(String)
    objectid = Column(Integer)
    feature_area_sqm = Column(DOUBLE_PRECISION)
    feature_length_m = Column(DOUBLE_PRECISION)
    geometry_area = Column(Integer, name="geometry.area")
    geometry_len = Column(Integer, name="geometry.len")


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_fire_centres_labels_geom',
      FireCentreLabel.geom, postgresql_using='gist')


class FireZone(Base):
    """ Class representing table structure of a fire zone
    """
    __tablename__ = 'fire_zones'
    __table_args__ = (
        {'comment': 'BC fire zone boundaries'}
    )
    id = Column(Integer, primary_key=True)
    feature_id = Column(Integer, nullable=False)
    geom = Column(geoalchemy2.types.Geometry(geometry_type='MultiPolygon',
                                             srid=4326,
                                             spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False)
    create_date = Column(TZTimeStamp, nullable=False)
    update_date = Column(TZTimeStamp, nullable=False)
    mof_fire_zone_id = Column(Integer)
    mof_fire_zone_name = Column(String)
    mof_fire_centre_name = Column(String)
    headquarters_city_name = Column(String)
    objectid = Column(Integer)
    feature_area_sqm = Column(DOUBLE_PRECISION)
    feature_length_m = Column(DOUBLE_PRECISION)
    geometry_area = Column(Integer, name="geometry.area")
    geometry_len = Column(Integer, name="geometry.len")


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_fire_zones_geom',
      FireZone.geom, postgresql_using='gist')


class FireZoneLabel(Base):
    """ Class representing table structure of a fire zone label
    """
    __tablename__ = 'fire_zones_labels'
    __table_args__ = (
        {'comment': 'BC fire zone labels'}
    )
    id = Column(Integer, primary_key=True)
    feature_id = Column(Integer, nullable=False)
    geom = Column(geoalchemy2.types.Geometry(geometry_type='Point',
                                             srid=4326,
                                             spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False)
    create_date = Column(TZTimeStamp, nullable=False)
    update_date = Column(TZTimeStamp, nullable=False)
    mof_fire_zone_id = Column(Integer)
    mof_fire_zone_name = Column(String)
    mof_fire_centre_name = Column(String)
    headquarters_city_name = Column(String)
    objectid = Column(Integer)
    feature_area_sqm = Column(DOUBLE_PRECISION)
    feature_length_m = Column(DOUBLE_PRECISION)
    geometry_area = Column(Integer, name="geometry.area")
    geometry_len = Column(Integer, name="geometry.len")


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_fire_zones_labels_geom',
      FireZoneLabel.geom, postgresql_using='gist')


class FireZoneLabelExt(Base):
    """ Class representing table structure of a fire zone extended label
    """
    __tablename__ = 'fire_zones_labels_ext'
    __table_args__ = (
        {'comment': 'BC fire zone extended labels'}
    )
    id = Column(Integer, primary_key=True)
    geom = Column(geoalchemy2.types.Geometry(geometry_type='Point',
                                             srid=4326,
                                             spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False)
    create_date = Column(TZTimeStamp, nullable=False)
    update_date = Column(TZTimeStamp, nullable=False)
    fire_zone_feature_id = Column(Integer, nullable=False)
    fire_zone_mof_fire_zone_id = Column(Integer)
    fire_zone_mof_fire_zone_name = Column(String)
    fire_zone_headquarters_city_name = Column(String)
    fire_zone_mof_fire_centre_name = Column(String)
    fire_zone_objectid = Column(Integer)
    fire_zone_feature_area_sqm = Column(DOUBLE_PRECISION)
    fire_zone_feature_length_m = Column(DOUBLE_PRECISION)
    fire_zone_geometry_area = Column(Integer, name="fire_zone_geometry.area")
    fire_zone_geometry_len = Column(Integer, name="fire_zone_geometry.len")
    fire_centre_feature_id = Column(Integer, nullable=False)
    fire_centre_mof_fire_centre_id = Column(Integer)
    fire_centre_mof_fire_centre_name = Column(String)
    fire_centre_objectid = Column(Integer)
    fire_centre_feature_area_sqm = Column(DOUBLE_PRECISION)
    fire_centre_feature_length_m = Column(DOUBLE_PRECISION)
    fire_centre_geometry_area = Column(Integer, name="fire_centre_geometry.area")
    fire_centre_geometry_len = Column(Integer, name="fire_centre_geometry.len")


# Explict creation of index due to issue with alembic + geoalchemy.
Index('idx_fire_zones_labels_ext_geom',
      FireZoneLabelExt.geom, postgresql_using='gist')
