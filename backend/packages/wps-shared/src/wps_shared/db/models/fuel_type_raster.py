import enum

from sqlalchemy import CheckConstraint, Column, Integer, String
from wps_shared.db.models import Base
from wps_shared.db.models.common import TZTimeStamp


class FuelRasterInstallStatus(str, enum.Enum):
    """Valid install statuses for FuelTypeRaster."""

    INSTALLING = "installing"
    READY = "ready"
    FAILED = "failed"


class FuelTypeRaster(Base):
    """
    Records the historical and currently processed fuel type rasters.
    """

    __tablename__ = "fuel_type_raster"
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    version = Column(Integer, nullable=False)
    xsize = Column(Integer, nullable=False)
    ysize = Column(Integer, nullable=False)
    object_store_path = Column(String, nullable=False)
    content_hash = Column(String, nullable=False)
    create_timestamp = Column(TZTimeStamp, nullable=False)
    install_status = Column(String, default=FuelRasterInstallStatus.READY, nullable=False)
    ready_timestamp = Column(TZTimeStamp, nullable=True)

    __table_args__ = (
        CheckConstraint(
            install_status.in_(tuple(status.value for status in FuelRasterInstallStatus)),
            name="ck_fuel_type_raster_install_status",
        ),
        {"comment": "Processed fuel type rasters."},
    )
