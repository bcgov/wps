"""This module contains pydandict schemas relating to weather stations for the API."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FireZone(BaseModel):
    id: int
    display_label: str
    fire_centre: str


class StationFireCentre(BaseModel):
    """The fire centre associated with a station"""

    id: int
    display_label: str


class Season(BaseModel):
    """A fire season consists of a start date (month and day) and an end date (month and day)."""

    start_month: int
    start_day: int
    end_month: int
    end_day: int


class WeatherStationProperties(BaseModel):
    """Non-geometrical weather station properties"""

    code: int
    name: str
    ecodivision_name: Optional[str] = None
    core_season: Optional[Season] = None


class WeatherVariables(BaseModel):
    """Weather variables"""

    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None


class DetailedWeatherStationProperties(WeatherStationProperties):
    """Detailed, non-geometrical weather station properties"""

    observations: Optional[WeatherVariables] = None
    forecasts: Optional[WeatherVariables] = None


class WeatherStationGeometry(BaseModel):
    """Geometrical coordinates of a weather station"""

    type: str = "Point"
    coordinates: List[float]


class GeoJsonDetailedWeatherStation(BaseModel):
    """GeoJson formatted weather station with details"""

    type: str = "Feature"
    properties: DetailedWeatherStationProperties
    geometry: WeatherStationGeometry


class NoonForecast(BaseModel):
    """Class representing noon forecasts."""

    weather_date: datetime
    station_code: int
    temp_valid: bool
    temperature: float
    rh_valid: bool
    relative_humidity: float
    wdir_valid: bool
    wind_direction: float
    wspeed_valid: bool
    wind_speed: float
    precip_valid: bool
    precipitation: float
    gc: float
    ffmc: float
    dmc: float
    dc: float
    isi: float
    bui: float
    fwi: float
    created_at: datetime
    wfwx_update_date: datetime


class WeatherStation(BaseModel):
    """A fire weather station has a code, name and geographical coordinate."""

    zone_code: Optional[str] = None
    code: int
    name: str
    lat: float
    long: float
    ecodivision_name: Optional[str] = None
    core_season: Optional[Season] = None
    elevation: Optional[int] = None
    wfwx_station_uuid: Optional[str] = None


class StationCodeList(BaseModel):
    """List of station codes."""

    stations: List[int]


class WeatherStationGroupMember(BaseModel):
    """Description of a station in a group"""

    id: str
    display_label: str
    fire_centre: StationFireCentre
    fire_zone: Optional[FireZone] = None
    station_code: int
    station_status: str


class WeatherStationGroup(BaseModel):
    """A weather station group from WF1"""

    display_label: str
    group_description: Optional[str] = None
    group_owner_user_guid: str
    group_owner_user_id: str
    id: str


class WeatherReading(BaseModel):
    """Weather reading for a particular point in time"""

    datetime: Optional[datetime]
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    barometric_pressure: Optional[float] = None
    precipitation: Optional[float] = None
    dewpoint: Optional[float] = None
    ffmc: Optional[float] = None
    isi: Optional[float] = None
    fwi: Optional[float] = None
    observation_valid: Optional[bool] = None
    observation_valid_comment: Optional[str] = None


class WeatherStationHourlyReadings(BaseModel):
    """The weather readings for a particular station"""

    values: List[WeatherReading]
    station: WeatherStation


class WFWXWeatherStation(BaseModel):
    """A WFWX station includes a code and WFWX API-specific ID"""

    model_config = ConfigDict(
        populate_by_name=True, frozen=True
    )  # allows populating by alias name, and frozen makes it hashable for collections

    wfwx_id: str
    code: int
    name: str
    lat: float = Field(alias="latitude")
    long: float = Field(alias="longitude")
    elevation: int
    zone_code: Optional[str]


class HourlyActual(BaseModel):
    """Class representing table structure of 'hourly_actuals.'"""

    weather_date: datetime
    station_code: int
    temp_valid: Optional[bool] = False
    temperature: Optional[float] = None
    dewpoint: Optional[float] = None
    rh_valid: Optional[bool] = False
    relative_humidity: Optional[float]
    wdir_valid: Optional[bool] = False
    wind_direction: Optional[float]
    wspeed_valid: Optional[bool] = False
    wind_speed: Optional[float]
    precip_valid: Optional[bool] = False
    precipitation: Optional[float]
    ffmc: Optional[float]
    isi: Optional[float]
    fwi: Optional[float]
    created_at: Optional[datetime] = datetime.now(tz=timezone.utc)


class FireCenterStation(BaseModel):
    """A fire weather station has a code, name and geographical coordinate."""

    code: int
    name: str
    zone: Optional[str] = None


class FireCentre(BaseModel):
    """The highest-level organizational unit for wildfire planning. Each fire centre
    has 1 or more planning areas within it."""

    id: str
    name: str
    stations: List[FireCenterStation]


class StationDailyFromWF1(BaseModel):
    """Daily weather data (forecast or observed) for a specific station and date retrieved from WF1 API"""

    created_by: str
    forecast_id: str
    station_code: int
    station_name: str
    utcTimestamp: datetime
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    precipitation: Optional[float] = None
    wind_direction: Optional[float] = None
    wind_speed: Optional[float] = None


class WeatherDeterminate(str, Enum):
    """Enumerator for all valid determinate weather sources"""

    GDPS = "GDPS"
    GDPS_BIAS = "GDPS_BIAS"
    GFS = "GFS"
    GFS_BIAS = "GFS_BIAS"
    HRDPS = "HRDPS"
    HRDPS_BIAS = "HRDPS_BIAS"
    NAM = "NAM"
    NAM_BIAS = "NAM_BIAS"
    RDPS = "RDPS"
    RDPS_BIAS = "RDPS_BIAS"
    GRASS_CURING_CWFIS = "Grass_Curing_CWFIS"
    ECMWF = "ECMWF"

    # non prediction models
    FORECAST = "Forecast"
    ACTUAL = "Actual"

    @classmethod
    def from_string(cls, value: str) -> "WeatherDeterminate":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"{value!r} is not a valid WeatherDeterminate")


class WeatherIndeterminate(BaseModel):
    """Used to represent a predicted or actual value"""

    station_code: int
    station_name: str
    determinate: WeatherDeterminate
    utc_timestamp: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    precipitation: Optional[float] = None
    wind_direction: Optional[float] = None
    wind_speed: Optional[float] = None
    fine_fuel_moisture_code: Optional[float] = None
    duff_moisture_code: Optional[float] = None
    drought_code: Optional[float] = None
    initial_spread_index: Optional[float] = None
    build_up_index: Optional[float] = None
    fire_weather_index: Optional[float] = None
    danger_rating: Optional[int] = None
    grass_curing: Optional[float] = None
    update_date: Optional[datetime] = None
    prediction_run_timestamp: Optional[datetime] = None


class WF1ForecastRecordType(BaseModel):
    id: str = "FORECAST"
    displayLabel: str = "Forecast"


class WF1PostForecast(BaseModel):
    """Used to represent a forecast to be POSTed to WF1"""

    archive: str = "false"
    createdBy: Optional[str] = None
    id: Optional[str] = None
    station: str  # station URL
    stationId: str  # station UUID
    weatherTimestamp: int  # UTC timestamp in millis
    temperature: float
    relativeHumidity: float
    precipitation: float
    windSpeed: float
    windDirection: Optional[float] = None
    grasslandCuring: Optional[float] = None
    recordType: WF1ForecastRecordType
