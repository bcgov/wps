"""Model for tracking SFMS job runs."""

import enum

from sqlalchemy import ARRAY, Column, Date, Enum, ForeignKey, Integer, String

from wps_shared.db.models import Base
from wps_shared.db.models.auto_spatial_advisory import RunTypeEnum
from wps_shared.db.models.common import TZTimeStamp


class SFMSRunLogJobName(str, enum.Enum):
    """Valid SFMS job names."""

    TEMPERATURE_INTERPOLATION = "temperature_interpolation"
    PRECIPITATION_INTERPOLATION = "precipitation_interpolation"


class SFMSRunLogStatus(str, enum.Enum):
    """Valid SFMS run log statuses."""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

class SFMSRunLog(Base):
    """Log of SFMS job interpolations with run status and timing."""

    __tablename__ = "sfms_run_log"
    __table_args__ = {
        "comment": "Tracks SFMS interpolation runs with execution timestamps and status."
    }

    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String, nullable=False, index=True)
    started_at = Column(TZTimeStamp, nullable=False)
    completed_at = Column(TZTimeStamp, nullable=True)
    status = Column(String, nullable=False)
    sfms_run_id = Column(Integer, ForeignKey("sfms_run.id"), nullable=True)


class SFMSRun(Base):
    """A class representing actual and forecast runs of SFMS and the stations used."""

    __tablename__ = "sfms_run"
    __table_args__ = {"comment": "Tracks SFMS job runs and the stations used."}

    id = Column(Integer, primary_key=True, index=True)
    run_type = Column(Enum(RunTypeEnum), nullable=False, index=True)
    target_date = Column(Date, nullable=False, index=True)
    run_datetime = Column(TZTimeStamp, nullable=False, index=True)
    stations = Column(ARRAY(Integer), nullable=False)
