from sqlalchemy import CheckConstraint, Column, Integer, String
from wps_shared.db.models import Base
from wps_shared.db.models.common import TZTimeStamp

FUEL_RASTER_STATUS_INSTALLING = "installing"
FUEL_RASTER_STATUS_READY = "ready"
FUEL_RASTER_STATUS_FAILED = "failed"
FUEL_RASTER_INSTALL_STATUSES = (
    FUEL_RASTER_STATUS_INSTALLING,
    FUEL_RASTER_STATUS_READY,
    FUEL_RASTER_STATUS_FAILED,
)


class FuelTypeRaster(Base):
    """
    Records the historical and currently processed fuel type rasters.
    """

    __tablename__ = "fuel_type_raster"
    __table_args__ = (
        CheckConstraint(
            f"install_status IN {FUEL_RASTER_INSTALL_STATUSES}",
            name="ck_fuel_type_raster_install_status",
        ),
        {"comment": "Processed fuel type rasters."},
    )
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    version = Column(Integer, nullable=False)
    xsize = Column(Integer, nullable=False)
    ysize = Column(Integer, nullable=False)
    object_store_path = Column(String, nullable=False)
    content_hash = Column(String, nullable=False)
    create_timestamp = Column(TZTimeStamp, nullable=False)
    install_status = Column(String, default=FUEL_RASTER_STATUS_READY, nullable=False)
    ready_timestamp = Column(TZTimeStamp, nullable=True)
