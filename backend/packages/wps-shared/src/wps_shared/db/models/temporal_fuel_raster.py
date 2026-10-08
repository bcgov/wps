from sqlalchemy import Column, Date, ForeignKey, Integer, String, UniqueConstraint
from wps_shared.db.models import Base
from wps_shared.db.models.common import TZTimeStamp


class TemporalFuelRaster(Base):
    """
    Records the daily fuel type rasters derived from a base fuel type raster and the Julian
    date season rasters (green-up and grass curing) that were applied to it.
    """

    __tablename__ = "temporal_fuel_raster"
    id = Column(Integer, primary_key=True)
    fuel_type_raster_id = Column(
        Integer, ForeignKey("fuel_type_raster.id"), nullable=False, index=True
    )
    for_date = Column(Date, nullable=False, index=True)
    version = Column(Integer, nullable=False)
    object_store_path = Column(String, nullable=False)
    fuel_codes_lookup_path = Column(String, nullable=False)
    content_hash = Column(String, nullable=False)
    green_up_on_hash = Column(String, nullable=False)
    green_up_off_hash = Column(String, nullable=False)
    grass_standing_hash = Column(String, nullable=False)
    grass_matted_hash = Column(String, nullable=False)
    green_up_on_archive_path = Column(String, nullable=False)
    green_up_off_archive_path = Column(String, nullable=False)
    grass_standing_archive_path = Column(String, nullable=False)
    grass_matted_archive_path = Column(String, nullable=False)
    create_timestamp = Column(TZTimeStamp, nullable=False)

    __table_args__ = (
        UniqueConstraint("for_date", "version"),
        {"comment": "Daily temporal fuel type rasters."},
    )
