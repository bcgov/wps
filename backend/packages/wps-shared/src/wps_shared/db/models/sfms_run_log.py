"""Model for tracking SFMS job runs."""

from sqlalchemy import Column, Date, Integer, String

from wps_shared.db.models import Base
from wps_shared.db.models.common import TZTimeStamp


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
