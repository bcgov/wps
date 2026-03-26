import enum

from sqlalchemy import CheckConstraint, Column, Enum, Integer, String

from wps_shared.db.models import Base
from wps_shared.db.models.common import TZTimeStamp
from wps_shared.utils.time import get_utc_now


class ECCCModel(str, enum.Enum):
    """Enumerator for different kinds of supported ECCC weather models"""

    GDPS = "GDPS"
    RDPS = "RDPS"


class ChartStatusEnum(str, enum.Enum):
    """Valid statuses for ProcessedFourPanelCharts."""

    COMPLETE = "complete"
    INPROGRESS = "in_progress"
    FAILED = "failed"


# Used for limiting the model field in the ProcessedFourPanelChart table instead of an enum as the valid models will be updated over time.
ModelNames = (ECCCModel.GDPS.value, ECCCModel.RDPS.value)


class ProcessedFourPanelChart(Base):
    """Keeps track of the generation of four panel charts by mode, day and model run hour."""

    __tablename__ = "processed_four_panel_chart"

    id = Column(
        Integer, primary_key=True, nullable=False, index=True, autoincrement=True
    )
    model = Column(String, nullable=False, index=True)
    model_run_timestamp = Column(TZTimeStamp, nullable=False, index=True)
    status = Column(Enum(ChartStatusEnum), nullable=False, index=True)
    create_date = Column(TZTimeStamp, default=get_utc_now, nullable=False, index=False)
    update_date = Column(TZTimeStamp, default=get_utc_now, nullable=False, index=False)

    __table_args__ = (
        CheckConstraint(model.in_(ModelNames), name="chk_model_name_four_panel_charts"),
        {"comment": "Record containing information about processed four panel charts."},
    )
