from datetime import datetime

from pydantic import BaseModel


class PullFromChefsResponse(BaseModel):
    success: bool


class SpotSubscriberData(BaseModel):
    id: int | None = None
    email: str
    subscriber_status: str = "active"


class UpdateSubscriberStatusData(BaseModel):
    subscriber_id: int
    status: str


class SpotLatestForecastData(BaseModel):
    id: int
    created_at: datetime
    issued_at: datetime
    expires_at: datetime | None = None
    forecast_end_at: datetime | None = None
    forecaster_name: str | None = None


class SpotRequestInput(BaseModel):
    id: int | None = None
    request_reference: str
    fire_number: list[str] | None = None
    fire_centre: int
    status: str = "Requested"
    request_frequency: list[str] | None = None
    request_type: str = "Full"
    aspect: str | None = None
    elevation: int | None = None
    geographic_description: str
    additional_information: str | None = None
    latitude: float
    longitude: float
    requested_at: datetime
    start_at: datetime
    end_at: datetime
    subscribers: list[SpotSubscriberData] = []


class SpotRequestData(SpotRequestInput):
    requestor_name: str
    requestor_idir: str
    requestor_email: str
    latest_forecast: SpotLatestForecastData | None = None


class SpotRequestResponse(BaseModel):
    spot_request: SpotRequestData


class SpotRequestListResponse(BaseModel):
    spot_requests: list[SpotRequestData]


class SpotDescriptiveWeatherInput(BaseModel):
    period: str
    temperature: float | None = None
    relative_humidity: float | None = None
    conditions: str | None = None


class SpotDescriptiveWeatherData(SpotDescriptiveWeatherInput):
    id: int | None = None


class SpotTabularWeatherInput(BaseModel):
    forecast_time: datetime
    temperature: float | None = None
    relative_humidity: float | None = None
    wind: str | None = None
    probability_of_precipitation: float | None = None
    precipitation_amount: float | None = None


class SpotTabularWeatherData(SpotTabularWeatherInput):
    id: int | None = None


class SpotForecastInput(BaseModel):
    spot_request_id: int
    issued_at: datetime
    expires_at: datetime | None = None
    synopsis: str | None = None
    inversion_and_venting: str | None = None
    outlook: str | None = None
    confidence: str | None = None
    fire_size: float | None = None
    representative_station_codes: list[int] | None = None
    descriptive_weather: list[SpotDescriptiveWeatherInput] = []
    tabular_weather: list[SpotTabularWeatherInput] = []


class SpotForecastData(SpotForecastInput):
    id: int | None = None
    created_at: datetime | None = None
    forecaster_name: str | None = None
    forecaster_email: str | None = None
    forecaster_phone: str | None = None
    descriptive_weather: list[SpotDescriptiveWeatherData] = []
    tabular_weather: list[SpotTabularWeatherData] = []


class SpotForecastResponse(BaseModel):
    spot_forecast: SpotForecastData


class SpotForecastListResponse(BaseModel):
    spot_forecasts: list[SpotForecastData]


class SmurfiGeneralForecastData(BaseModel):
    period: str
    temperature: float | None = None
    relative_humidity: float | None = None
    conditions: str | None = None


class SmurfiForecastData(BaseModel):
    forecast_time: str
    temperature: float | None = None
    relative_humidity: float | None = None
    wind: str | None = None
    probability_of_precipitation: float | None = None
    precipitation_amount: float | None = None


class SpotUpdatePayload(BaseModel):
    spot_request_id: int
    spot_forecast_id: int


class SubscribeResponse(BaseModel):
    subscriber_status: str


class SubscriptionsResponse(BaseModel):
    spot_request_ids: list[int]


class SmurfiSpotVersionData(BaseModel):
    spot_id: int
    fire_number: str
    requested_by: str
    forecaster: str
    latitude: float
    longitude: float
    elevation: float | None = None
    representative_weather_stations: list[str] | None = None
    forecaster_email: str | None = None
    forecaster_phone: str | None = None
    additional_fire_numbers: list[str] | None = None
    geographic_area_name: str | None = None
    fire_centre: str | None = None
    elevation: float | None = None
    fire_size: float | None = None
    slope: float | None = None
    aspect: str | None = None
    valley: str | None = None
    synopsis: str | None = None
    inversion_and_venting: str | None = None
    outlook: str | None = None
    confidence: str | None = None
    general_forecasts: list[SmurfiGeneralForecastData] | None = None
    forecasts: list[SmurfiForecastData] | None = None
