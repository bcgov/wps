from sqlalchemy import Column, Integer, String
from wps_shared.db.models import Base
from wps_shared.db.models.common import TZTimeStamp


class FuelTypeRaster(Base):
    """
    Records the historical and currently processed fuel type rasters.
    """

    __tablename__ = "fuel_type_raster"
    __table_args__ = {"comment": "Processed fuel type rasters."}
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    version = Column(Integer, nullable=False)
    xsize = Column(Integer, nullable=False)
    ysize = Column(Integer, nullable=False)
    object_store_path = Column(String, nullable=False)
    content_hash = Column(String, nullable=False)
    create_timestamp = Column(TZTimeStamp, nullable=False)
