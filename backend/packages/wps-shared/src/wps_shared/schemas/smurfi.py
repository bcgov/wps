from pydantic import BaseModel


class PullFromChefsResponse(BaseModel):
    success: bool


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
