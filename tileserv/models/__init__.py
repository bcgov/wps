""" Class model that reflect resources and map to database tables relating audits created
by authenticated user requests.
"""
import enum
import logging
from datetime import datetime
from sqlalchemy.types import TypeDecorator
from sqlalchemy import (Column, Enum, Index, Integer, String, TIMESTAMP)
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
        {'comment': 'The audit log of an authenticated request by a user.'}
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
