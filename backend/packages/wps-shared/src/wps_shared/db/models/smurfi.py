
from sqlalchemy import (
	Column, Integer, String, Float, Boolean, ForeignKey, Text, Enum, ARRAY
)
from sqlalchemy.orm import relationship
import enum
from wps_shared.db.models import Base
from wps_shared.db.models.common import TZTimeStamp
import wps_shared.utils.time as time_utils




# Enum definitions (should match your migration)
class FrequencyDayEnum(enum.Enum):
	Monday = 'Monday'
	Tuesday = 'Tuesday'
	Wednesday = 'Wednesday'
	Thursday = 'Thursday'
	Friday = 'Friday'
	Saturday = 'Saturday'
	Sunday = 'Sunday'

class RequestTypeEnum(enum.Enum):
	Full = 'Full'
	Mini = 'Mini'
	Ventilation = 'Ventilation'

class SpotRequestStatusEnum(enum.Enum):
	Requested = 'Requested'
	Started = 'Started'
	Suspended = 'Suspended'
	Complete = 'Complete'
	Archived = 'Archived'

class SpotForecastPeriodEnum(enum.Enum):
	Today = 'Today'
	Tonight = 'Tonight'
	Tomorrow = 'Tomorrow'

class Spot(Base):
	__tablename__ = 'spot'
	__table_args__ = {'comment': 'Requests for SMURFI spot forecasts'}
	id = Column(Integer, primary_key=True)
	request_id = Column(String, unique=True, nullable=False)
	fire_number = Column(String, nullable=False)
	request_time = Column(TZTimeStamp, nullable=False)
	end_time = Column(TZTimeStamp, nullable=False)
	status = Column(Enum(SpotRequestStatusEnum), nullable=False)
	requested_frequency = Column(ARRAY(Enum(FrequencyDayEnum)), nullable=True)
	requested_type = Column(Enum(RequestTypeEnum), nullable=False, default=RequestTypeEnum.Full)
	additional_info = Column(Text, nullable=True)
	requested_by = Column(String, nullable=False)
	geographic_area_name = Column(String, nullable=True)
	email_distribution_list = Column(ARRAY(String), nullable=True)
	fire_centre = Column(String, nullable=True)
	created_at = Column(TZTimeStamp, nullable=False, default=time_utils.get_utc_now())
	updated_at = Column(TZTimeStamp, nullable=True, onupdate=time_utils.get_utc_now())
	# Relationships
	versions = relationship('SpotVersion', back_populates='spot')

class SpotVersion(Base):
	__tablename__ = 'spot_version'
	__table_args__ = {'comment': 'Versions of SMURFI spot forecasts'}
	id = Column(Integer, primary_key=True)
	spot_id = Column(Integer, ForeignKey('spot.id'), nullable=False)
	additional_fire_numbers = Column(ARRAY(String), nullable=True)
	forecaster = Column(String, nullable=False)
	forecaster_email = Column(String, nullable=True)
	forecaster_phone = Column(String, nullable=True)
	representative_weather_stations = Column(ARRAY(String), nullable=True)
	latitude = Column(Float, nullable=False)
	longitude = Column(Float, nullable=False)
	elevation = Column(Float, nullable=True)
	slope = Column(Float, nullable=True)
	aspect = Column(String, nullable=True)
	valley = Column(String, nullable=True)
	synopsis = Column(Text, nullable=True)
	inversion_and_venting = Column(Text, nullable=True)
	outlook = Column(Text, nullable=True)
	confidence = Column(Text, nullable=True)
	is_latest = Column(Boolean, nullable=False, default=True)
	created_at = Column(TZTimeStamp, nullable=False, default=time_utils.get_utc_now())
	updated_at = Column(TZTimeStamp, nullable=True, onupdate=time_utils.get_utc_now())
	# Relationships
	spot = relationship('Spot', back_populates='versions')
	forecasts = relationship('SpotForecast', back_populates='spot_version')
	general_forecasts = relationship('SpotGeneralForecast', back_populates='spot_version')
	
class SpotForecast(Base):
	__tablename__ = 'spot_forecast'
	__table_args__ = {'comment': 'Detailed forecasts for SMURFI spot versions'}
	id = Column(Integer, primary_key=True)
	spot_version_id = Column(Integer, ForeignKey('spot_version.id'), nullable=False)
	forecast_time = Column(TZTimeStamp, nullable=False)
	temperature = Column(Float, nullable=True)
	relative_humidity = Column(Float, nullable=True)
	wind = Column(String, nullable=True)
	probability_of_precipitation = Column(Float, nullable=True)
	precipitation_amount = Column(Float, nullable=True)
	# Relationships
	spot_version = relationship('SpotVersion', back_populates='forecasts')

class SpotGeneralForecast(Base):
	__tablename__ = 'spot_general_forecast'
	__table_args__ = {'comment': 'General (less specific) forecasts for SMURFI spot versions'}
	id = Column(Integer, primary_key=True)
	spot_version_id = Column(Integer, ForeignKey('spot_version.id'), nullable=False)
	period = Column(Enum(SpotForecastPeriodEnum), nullable=False)
	temperature = Column(Float, nullable=True)
	relative_humidity = Column(Float, nullable=True)
	conditions = Column(String, nullable=True)
	# Relationships
	spot_version = relationship('SpotVersion', back_populates='general_forecasts')
