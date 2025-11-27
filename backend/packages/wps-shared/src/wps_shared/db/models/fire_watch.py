import enum
from wps_shared.db.models import Base
from geoalchemy2 import Geometry
from sqlalchemy import ARRAY, Boolean, Column, Date, Enum, Float, ForeignKey, Integer, String
from wps_shared.db.models.common import TZTimeStamp
from wps_shared.db.models.hfi_calc import FireCentre
from wps_shared.db.models.weather_models import PredictionModelRunTimestamp
from wps_shared.fuel_types import FuelTypeEnum
from wps_shared.geospatial.geospatial import NAD83_BC_ALBERS


class BurnStatusEnum(enum.Enum):
    """Enum for the status of a prescribed burn."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETE = "complete"
    HOLD = "hold"


class FireWatch(Base):
    """Daily percent grass curing per weather station."""

    __tablename__ = "fire_watch"
    __table_args__ = {"comment": "Contains parameters related to a prescribed burn."}

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    burn_location = Column(
        Geometry("Point", spatial_index=True, srid=NAD83_BC_ALBERS), nullable=False
    )
    burn_window_end = Column(TZTimeStamp, nullable=True, index=False)
    burn_window_start = Column(TZTimeStamp, nullable=True, index=False)
    contact_email = Column(ARRAY(String), nullable=False, index=False)
    create_timestamp = Column(TZTimeStamp, nullable=False, index=False)
    create_user = Column(String, nullable=False)
    fire_centre = Column(Integer, ForeignKey(FireCentre.id), nullable=True, index=False)
    station_code = Column(Integer, nullable=False, index=False)
    status = Column(Enum(BurnStatusEnum), nullable=False, index=True)
    title = Column(String, nullable=False, index=False)
    update_timestamp = Column(TZTimeStamp, nullable=False, index=False)
    update_user = Column(String, nullable=False)
    # Fuel parameters
    fuel_type = Column(Enum(FuelTypeEnum), nullable=False, index=False)
    percent_conifer = Column(Float, nullable=True, index=False)
    percent_dead_fir = Column(Float, nullable=True, index=False)
    percent_grass_curing = Column(Float, nullable=True, index=False)
    # Weather parameters
    temp_min = Column(Float, nullable=False, index=False)
    temp_preferred = Column(Float, nullable=True, index=False)
    temp_max = Column(Float, nullable=False, index=False)
    rh_min = Column(Float, nullable=False, index=False)
    rh_preferred = Column(Float, nullable=True, index=False)
    rh_max = Column(Float, nullable=False, index=False)
    wind_speed_min = Column(Float, nullable=False, index=False)
    wind_speed_preferred = Column(Float, nullable=True, index=False)
    wind_speed_max = Column(Float, nullable=False, index=False)
    # FWI and FBP parameters
    ffmc_min = Column(Float, nullable=True, index=False)
    ffmc_preferred = Column(Float, nullable=True, index=False)
    ffmc_max = Column(Float, nullable=True, index=False)
    dmc_min = Column(Float, nullable=True, index=False)
    dmc_preferred = Column(Float, nullable=True, index=False)
    dmc_max = Column(Float, nullable=True, index=False)
    dc_min = Column(Float, nullable=True, index=False)
    dc_preferred = Column(Float, nullable=True, index=False)
    dc_max = Column(Float, nullable=True, index=False)
    isi_min = Column(Float, nullable=True, index=False)
    isi_preferred = Column(Float, nullable=True, index=False)
    isi_max = Column(Float, nullable=True, index=False)
    bui_min = Column(Float, nullable=True, index=False)
    bui_preferred = Column(Float, nullable=True, index=False)
    bui_max = Column(Float, nullable=True, index=False)
    hfi_min = Column(Float, nullable=False, index=False)
    hfi_preferred = Column(Float, nullable=True, index=False)
    hfi_max = Column(Float, nullable=False, index=False)

    OPTIONAL_FWI_FIELDS = [
        "ffmc",
        "dmc",
        "dc",
        "isi",
        "bui",
    ]


class PrescriptionStatus(Base):
    """Table to store fire watch prescription statuses."""

    __tablename__ = "prescription_status"
    __table_args__ = {"comment": "Contains the status of a fire watch prescription."}

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False)


class FireWatchWeather(Base):
    """Weather and FWI/FBP indices for a fire watch."""

    __tablename__ = "fire_watch_weather"
    __table_args__ = {
        "comment": "Contains weather forecasts and FWI/FBP indices related to a fire watch prescribed burn."
    }

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    fire_watch_id = Column(Integer, ForeignKey(FireWatch.id), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    # Weather parameters
    prediction_model_run_timestamp_id = Column(
        Integer, ForeignKey(PredictionModelRunTimestamp.id), nullable=False, index=True
    )
    temperature = Column(Float, nullable=False, index=False)
    relative_humidity = Column(Float, nullable=False, index=False)
    wind_speed = Column(Float, nullable=False, index=False)
    precip_24hr = Column(Float, nullable=False, index=False)
    # FWI indices
    ffmc = Column(Float, nullable=False, index=False)
    dmc = Column(Float, nullable=False, index=False)
    dc = Column(Float, nullable=False, index=False)
    isi = Column(Float, nullable=False, index=False)
    bui = Column(Float, nullable=False, index=False)
    # FBP indices
    hfi = Column(Float, nullable=False, index=False)
    # prescription flag
    in_prescription = Column(Integer, ForeignKey(PrescriptionStatus.id), nullable=False, index=True)
    # metadata
    created_at = Column(TZTimeStamp, nullable=False, index=False)

    UPDATABLE_FIELDS = [
        "temperature",
        "relative_humidity",
        "wind_speed",
        "precip_24hr",
        "ffmc",
        "isi",
        "bui",
        "dc",
        "dmc",
        "hfi",
        "in_prescription",
        "created_at",
    ]
