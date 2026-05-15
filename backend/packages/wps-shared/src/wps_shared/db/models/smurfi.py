import enum

from geoalchemy2 import Geometry
from sqlalchemy import ARRAY, Column, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

import wps_shared.utils.time as time_utils
from wps_shared.db.models import Base
from wps_shared.db.models.common import TZTimeStamp
from wps_shared.db.models.psu import FireCentre
from wps_shared.geospatial.geospatial import NAD83_BC_ALBERS


class FrequencyDayEnum(enum.Enum):
    Monday = "Monday"
    Tuesday = "Tuesday"
    Wednesday = "Wednesday"
    Thursday = "Thursday"
    Friday = "Friday"
    Saturday = "Saturday"
    Sunday = "Sunday"


class RequestTypeEnum(enum.Enum):
    Full = "Full"
    Mini = "Mini"
    Ventilation = "Ventilation"


class SpotRequestStatusEnum(enum.Enum):
    Requested = "Requested"
    Started = "Started"
    Suspended = "Suspended"
    Complete = "Complete"
    Archived = "Archived"


class SpotForecastPeriodEnum(enum.Enum):
    Today = "Today"
    Tonight = "Tonight"
    Tomorrow = "Tomorrow"


class CardinalDirectionEnum(enum.Enum):
    N = "North"
    NW = "Northwest"
    W = "West"
    SW = "Southwest"
    S = "South"
    SE = "Southeast"
    E = "East"
    NE = "Northeast"


class SpotSubscriberStatusEnum(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class SpotRequest(Base):
    """A class representing requests for spot forecasts."""

    __tablename__ = "spot_request"
    __table_args__ = {"comment": "Tracks requests for spot weather forecasts."}

    id = Column(Integer, primary_key=True)
    request_reference = Column(String, nullable=False)
    fire_number = Column(
        ARRAY(String), nullable=True
    )  # nullable to allow spot forecasts for prescribed burns
    fire_centre = Column(Integer, ForeignKey(FireCentre.id), nullable=False)
    status = Column(
        Enum(SpotRequestStatusEnum), nullable=False, default=SpotRequestStatusEnum.Requested
    )
    requestor_name = Column(String, nullable=False)
    requestor_idir = Column(String, nullable=False)
    requestor_email = Column(String, nullable=False)
    requested_frequency = Column(ARRAY(Enum(FrequencyDayEnum)), nullable=True)
    requested_type = Column(Enum(RequestTypeEnum), nullable=False, default=RequestTypeEnum.Full)
    aspect = Column(Enum(CardinalDirectionEnum), nullable=True)
    elevation = Column(Integer, nullable=True)
    geographic_description = Column(String, nullable=False)
    geom = Column(Geometry("POINT", spatial_index=False, srid=NAD83_BC_ALBERS), nullable=False)
    representative_station_codes = Column(ARRAY(Integer), nullable=True)
    requested_at = Column(TZTimeStamp, nullable=False)
    start_at = Column(TZTimeStamp, nullable=False)
    end_at = Column(TZTimeStamp, nullable=False)
    created_at = Column(TZTimeStamp, nullable=False, default=time_utils.get_utc_now)
    updated_at = Column(TZTimeStamp, nullable=False, onupdate=time_utils.get_utc_now)

    # Relationships
    spot_forecasts = relationship("SpotForecast", back_populates="spot_request")
    spot_subscribers = relationship("SpotSubscriber", back_populates="spot_request")


class SpotSubscriber(Base):
    """A class representing emails addresses that will receive spot forecasts for a spot request."""

    __tablename__ = "spot_subscriber"
    __table_args__ = {
        "comment": "Tracks email addresses subscribed to spot forecasts for a spot requests."
    }

    id = Column(Integer, primary_key=True)
    spot_request_id = Column(Integer, ForeignKey(SpotRequest.id), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    status = Column(
        Enum(SpotSubscriberStatusEnum), nullable=False, default=SpotSubscriberStatusEnum.ACTIVE
    )
    created_at = Column(TZTimeStamp, nullable=False, default=time_utils.get_utc_now)
    updated_at = Column(TZTimeStamp, nullable=False, onupdate=time_utils.get_utc_now)
    # Relationships
    spot_request = relationship("SpotRequest", back_populates="spot_subscribers")


class SpotForecast(Base):
    """Represents a spot forecast for a spot request."""

    __tablename__ = "spot_forecast"
    __table_args__ = {"comment": "Spot forecasts for spot requests."}

    id = Column(Integer, primary_key=True)
    spot_request_id = Column(Integer, ForeignKey("spot_request.id"), nullable=False, index=True)

    # forecaster info
    forecaster = Column(String, nullable=False)
    forecaster_email = Column(String, nullable=False)
    forecaster_phone = Column(String, nullable=True)

    # descriptive fields
    synopsis = Column(Text, nullable=True)
    inversion_and_venting = Column(Text, nullable=True)
    outlook = Column(Text, nullable=True)
    confidence = Column(Text, nullable=True)
    fire_size = Column(Float, nullable=True)
    created_at = Column(TZTimeStamp, nullable=False, default=time_utils.get_utc_now)
    updated_at = Column(TZTimeStamp, nullable=True, onupdate=time_utils.get_utc_now())

    # Relationships
    spot_request = relationship("SpotRequest", back_populates="spot_forecasts")
    tabular_weather = relationship("SpotTabularWeather", back_populates="spot_forecast")
    descriptive_weather = relationship("SpotDescriptiveWeather", back_populates="spot_forecast")


class SpotTabularWeather(Base):
    __tablename__ = "spot_tabular_weather"
    __table_args__ = {
        "comment": "Detailed numerical forecasts for weather variable in a spot forecast."
    }

    id = Column(Integer, primary_key=True)
    spot_forecast_id = Column(Integer, ForeignKey("spot_forecast.id"), nullable=False, index=True)
    forecast_time = Column(TZTimeStamp, nullable=False)
    temperature = Column(Float, nullable=True)
    relative_humidity = Column(Float, nullable=True)
    wind = Column(String, nullable=True)
    probability_of_precipitation = Column(Float, nullable=True)
    precipitation_amount = Column(Float, nullable=True)
    # Relationships
    spot_forecast = relationship("SpotForecast", back_populates="spot_tabular_weather")


class SpotDescriptiveWeather(Base):
    """A class representing the descriptive AFTERNOON/TONIGHT/TOMORROW forecasts in a full spot forecast.
    eg. AFTERNOON: Mainly sunny in the morning then increasing afternoon cloud. MAX TEMP 11C, MIN RH 40%
        TONIGHT: Mainly clear.  MIN TEMP -2C. MAX RH 90%.
        TOMORROW:  Cloudy.  TEMP 12C. MIN RH 40%.
    """

    __tablename__ = "spot_descriptive_weather"
    __table_args__ = {
        "comment": "Represents a general text based forecast which includes a description of conditions, temperature and humidity. "
    }

    id = Column(Integer, primary_key=True)
    spot_forecast_id = Column(Integer, ForeignKey("spot_forecast.id"), nullable=False, index=True)
    period = Column(Enum(SpotForecastPeriodEnum), nullable=False)
    temperature = Column(Float, nullable=True)
    relative_humidity = Column(Float, nullable=True)
    conditions = Column(String, nullable=True)
    # Relationships
    spot_forecast = relationship("SpotForecast", back_populates="descriptive_weather")
