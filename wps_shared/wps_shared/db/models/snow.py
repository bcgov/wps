import enum
from wps_shared.db.models import Base
from sqlalchemy import Column, Enum, Integer, Sequence
from wps_shared.db.models.common import TZTimeStamp


class SnowSourceEnum(enum.Enum):
    """ Define different sensors from which snow data is processed. eg. VIIRS """
    viirs = "viirs"


class ProcessedSnow(Base):
    """ Keeps track of snow coverage data that has been processed. """
    __tablename__ = 'processed_snow'
    __table_args__ = (
        {'comment': 'Record containing information about processed snow coverage data.'}
    )

    id = Column(Integer, Sequence('processed_snow_id_seq'),
                primary_key=True, nullable=False, index=True)
    for_date = Column(TZTimeStamp, nullable=False, index=True)
    processed_date = Column(TZTimeStamp, nullable=False, index=True)
    snow_source = Column(Enum(SnowSourceEnum), nullable=False, index=True)
   