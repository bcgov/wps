import enum

from geoalchemy2 import Geometry
from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
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
    FULL = "Full"
    MINI = "Mini"


request_type_values = (RequestTypeEnum.FULL.value, RequestTypeEnum.MINI.value)


class SpotRequestStatusEnum(enum.Enum):
    REQUESTED = "Requested"
    STARTED = "Started"
    SUSPENDED = "Suspended"
    COMPLETE = "Complete"
    ARCHIVED = "Archived"


request_status_values = (
    SpotRequestStatusEnum.REQUESTED.value,
    SpotRequestStatusEnum.STARTED.value,
    SpotRequestStatusEnum.SUSPENDED.value,
    SpotRequestStatusEnum.COMPLETE.value,
    SpotRequestStatusEnum.ARCHIVED.value,
)


class SpotForecastPeriodEnum(enum.Enum):
    TODAY = "Today"
    TONIGHT = "Tonight"
    TOMORROW = "Tomorrow"


forecast_period_values = (
    SpotForecastPeriodEnum.TODAY.value,
    SpotForecastPeriodEnum.TONIGHT.value,
    SpotForecastPeriodEnum.TOMORROW.value,
)


class CardinalDirectionEnum(enum.Enum):
    N = "North"
    NW = "Northwest"
    W = "West"
    SW = "Southwest"
    S = "South"
    SE = "Southeast"
    E = "East"
    NE = "Northeast"


cardinal_direction_values = (
    CardinalDirectionEnum.N.value,
    CardinalDirectionEnum.NW.value,
    CardinalDirectionEnum.W.value,
    CardinalDirectionEnum.SW.value,
    CardinalDirectionEnum.S.value,
    CardinalDirectionEnum.SE.value,
    CardinalDirectionEnum.E.value,
    CardinalDirectionEnum.NE.value,
)


spot_request_distribution_groups = Table(
    "spot_request_distribution_group",
    Base.metadata,
    Column(
        "spot_request_id",
        Integer,
        ForeignKey("spot_request_base.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "distribution_group_id",
        Integer,
        ForeignKey("smurfi_distribution_group.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class SmurfiDistributionGroup(Base):
    """Named email distribution groups that can be attached to spot requests."""

    __tablename__ = "smurfi_distribution_group"
    __table_args__ = {"comment": "Named distribution groups for spot forecast email notifications."}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    emails = Column(ARRAY(String), nullable=False, default=list)
    owner_idir = Column(String, nullable=False)
    created_at = Column(TZTimeStamp, nullable=False, default=time_utils.get_utc_now)
    updated_at = Column(
        TZTimeStamp, nullable=False, onupdate=time_utils.get_utc_now, default=time_utils.get_utc_now
    )

    spot_requests = relationship(
        "SpotRequestBase",
        secondary=spot_request_distribution_groups,
        back_populates="distribution_groups",
    )


class SpotSubscriberStatusEnum(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


subscriber_status_values = (
    SpotSubscriberStatusEnum.ACTIVE.value,
    SpotSubscriberStatusEnum.INACTIVE.value,
)


class SpotRequestBase(Base):
    """A durable administrative request for spot forecasts."""

    __tablename__ = "spot_request_base"

    id = Column(Integer, primary_key=True)
    request_reference = Column(String, nullable=False)
    fire_number = Column(
        ARRAY(String), nullable=True
    )  # nullable to allow spot forecasts for prescribed burns
    fire_centre = Column(Integer, ForeignKey(FireCentre.id), nullable=False)
    status = Column(
        String,
        nullable=False,
        default=SpotRequestStatusEnum.REQUESTED.value,
        index=True,
    )
    requestor_name = Column(String, nullable=False)
    requestor_idir = Column(String, nullable=False)
    requestor_email = Column(String, nullable=False)
    request_frequency = Column(ARRAY(Enum(FrequencyDayEnum)), nullable=True)
    request_type = Column(String, nullable=False, default=RequestTypeEnum.FULL.value)
    additional_information = Column(Text, nullable=True)
    requested_at = Column(TZTimeStamp, nullable=False)
    start_at = Column(TZTimeStamp, nullable=False, index=True)
    end_at = Column(TZTimeStamp, nullable=False, index=True)
    created_at = Column(TZTimeStamp, nullable=False, default=time_utils.get_utc_now)
    updated_at = Column(
        TZTimeStamp, nullable=False, onupdate=time_utils.get_utc_now, default=time_utils.get_utc_now
    )

    # Relationships
    spot_forecasts = relationship("SpotForecast", back_populates="spot_request_base")
    spot_request_instances = relationship(
        "SpotRequestInstance",
        back_populates="spot_request_base",
        foreign_keys="SpotRequestInstance.spot_request_base_id",
    )
    spot_subscribers = relationship("SpotSubscriber", back_populates="spot_request_base")
    distribution_groups = relationship(
        "SmurfiDistributionGroup",
        secondary=spot_request_distribution_groups,
        back_populates="spot_requests",
    )

    __table_args__ = (
        CheckConstraint(status.in_(request_status_values), name="chk_status_spot_request_base"),
        CheckConstraint(
            request_type.in_(request_type_values), name="chk_request_type_spot_request_base"
        ),
        {"comment": "Tracks administrative requests for spot weather forecasts."},
    )


class SpotRequestInstance(Base):
    """An instance of a spot_request containing geographic and terrain context for a spot request or forecast."""

    __tablename__ = "spot_request_instance"

    id = Column(Integer, primary_key=True)
    spot_request_base_id = Column(
        Integer, ForeignKey("spot_request_base.id"), nullable=False, index=True
    )
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(Geometry("POINT", spatial_index=False, srid=NAD83_BC_ALBERS), nullable=False)
    geographic_description = Column(String, nullable=False)
    aspect = Column(String, nullable=True)
    elevation = Column(Integer, nullable=True)
    valley = Column(String, nullable=True)
    created_at = Column(TZTimeStamp, nullable=False, default=time_utils.get_utc_now)
    updated_at = Column(
        TZTimeStamp, nullable=False, onupdate=time_utils.get_utc_now, default=time_utils.get_utc_now
    )

    # Relationships
    spot_request_base = relationship(
        "SpotRequestBase",
        back_populates="spot_request_instances",
        foreign_keys=[spot_request_base_id],
    )
    spot_forecasts = relationship("SpotForecast", back_populates="spot_request_instance")

    __table_args__ = (
        {"comment": "Tracks geographic instances used by spot requests and forecasts."},
    )


class SpotSubscriber(Base):
    """A class representing emails addresses that will receive spot forecasts for a spot request."""

    __tablename__ = "spot_subscriber"

    id = Column(Integer, primary_key=True)
    spot_request_base_id = Column(
        Integer, ForeignKey("spot_request_base.id"), nullable=False, index=True
    )
    email = Column(String, nullable=False, index=True)
    subscriber_status = Column(
        String, nullable=False, default=SpotSubscriberStatusEnum.ACTIVE.value
    )
    created_at = Column(TZTimeStamp, nullable=False, default=time_utils.get_utc_now)
    updated_at = Column(
        TZTimeStamp, nullable=False, onupdate=time_utils.get_utc_now, default=time_utils.get_utc_now
    )

    # Relationships
    spot_request_base = relationship("SpotRequestBase", back_populates="spot_subscribers")

    __table_args__ = (
        CheckConstraint(
            subscriber_status.in_(subscriber_status_values),
            name="chk_subscriber_status_spot_subscriber",
        ),
        {"comment": "Tracks email addresses subscribed to spot forecasts for a spot requests."},
    )


class SpotForecast(Base):
    """Represents a spot forecast for a spot request."""

    __tablename__ = "spot_forecast"

    id = Column(Integer, primary_key=True)
    spot_request_base_id = Column(
        Integer, ForeignKey("spot_request_base.id"), nullable=False, index=True
    )
    spot_request_instance_id = Column(
        Integer, ForeignKey("spot_request_instance.id"), nullable=False, index=True
    )

    # forecaster info
    forecaster_name = Column(String, nullable=False, index=True)
    forecaster_email = Column(String, nullable=False)
    forecaster_phone = Column(String, nullable=True)

    synopsis = Column(Text, nullable=True)
    inversion_and_venting = Column(Text, nullable=True)
    outlook = Column(Text, nullable=True)
    confidence = Column(Text, nullable=True)
    forecast_type = Column(String, nullable=False, default=RequestTypeEnum.FULL.value)
    fire_size = Column(ARRAY(Float), nullable=True)
    representative_station_codes = Column(ARRAY(Integer), nullable=True)
    created_at = Column(TZTimeStamp, nullable=False, default=time_utils.get_utc_now)
    issued_at = Column(TZTimeStamp, nullable=False)
    expires_at = Column(TZTimeStamp, nullable=True)

    # Relationships
    spot_request_base = relationship("SpotRequestBase", back_populates="spot_forecasts")
    spot_request_instance = relationship("SpotRequestInstance", back_populates="spot_forecasts")
    tabular_weather = relationship("SpotTabularWeather", back_populates="spot_forecast")
    descriptive_weather = relationship("SpotDescriptiveWeather", back_populates="spot_forecast")

    __table_args__ = (
        CheckConstraint(
            forecast_type.in_(request_type_values), name="chk_forecast_type_spot_forecast"
        ),
        {"comment": "Spot forecasts for spot requests."},
    )


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
    spot_forecast = relationship("SpotForecast", back_populates="tabular_weather")


class SpotDescriptiveWeather(Base):
    """A class representing the descriptive AFTERNOON/TONIGHT/TOMORROW forecasts in a full spot forecast.
    eg. AFTERNOON: Mainly sunny in the morning then increasing afternoon cloud. MAX TEMP 11C, MIN RH 40%
        TONIGHT: Mainly clear.  MIN TEMP -2C. MAX RH 90%.
        TOMORROW:  Cloudy.  TEMP 12C. MIN RH 40%.
    """

    __tablename__ = "spot_descriptive_weather"

    id = Column(Integer, primary_key=True)
    spot_forecast_id = Column(Integer, ForeignKey("spot_forecast.id"), nullable=False, index=True)
    period = Column(String, nullable=False)
    temperature = Column(Float, nullable=True)
    relative_humidity = Column(Float, nullable=True)
    conditions = Column(String, nullable=True)

    # Relationships
    spot_forecast = relationship("SpotForecast", back_populates="descriptive_weather")

    __table_args__ = (
        CheckConstraint(
            period.in_(forecast_period_values), name="chk_period_spot_descriptive_weather"
        ),
        {
            "comment": "Represents a general text based forecast which includes a description of conditions, temperature and humidity. "
        },
    )
