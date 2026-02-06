"""Model for tracking SFMS job runs."""

import enum

from sqlalchemy import Column, Date, Integer, String

from wps_shared.db.models import Base
from wps_shared.db.models.common import TZTimeStamp


class SFMSRunLogJobName(str, enum.Enum):
    """Valid SFMS job names."""

    TEMPERATURE_INTERPOLATION = "temperature_interpolation"
    PRECIPITATION_INTERPOLATION = "precipitation_interpolation"
    FFMC_INTERPOLATION = "ffmc_interpolation"
    DMC_INTERPOLATION = "dmc_interpolation"
    DC_INTERPOLATION = "dc_interpolation"


class SFMSRunLogStatus(str, enum.Enum):
    """Valid SFMS run log statuses."""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class SFMSRunLog(Base):
    """Log of SFMS job executions with target date and run timing."""

    __tablename__ = "sfms_run_log"
    __table_args__ = {"comment": "Tracks SFMS job runs with execution timestamps and status."}

    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String, nullable=False, index=True)
    target_date = Column(Date, nullable=False, index=True)
    started_at = Column(TZTimeStamp, nullable=False)
    completed_at = Column(TZTimeStamp, nullable=True)
    status = Column(String, nullable=False)
