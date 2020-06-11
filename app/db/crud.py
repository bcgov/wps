""" CRUD operations for management of resources
"""
from sqlalchemy.orm import Session
from db.models import ForecastModel, SingleForecast
import schemas


def get_forecast_models(db_session: Session):
    """ Get all available info about all supported weather forecast models """
    return db_session.query(ForecastModel).all()


def create_single_forecast(db_session: Session,
                           forecast: schemas.WeatherForecastValues,
                           issue_date: str,
                           weather_station: int):
    """ Create a new single forecast
        `weather_station` corresponds to schemas.WeatherStation.code
    """
    new_single_forecast = SingleForecast(
        forecast_datetime=forecast.datetime,
        forecast_model=forecast.forecast_model,
        weather_station=weather_station,
        issue_date=issue_date,
        temperature=forecast.temperature,
        dew_point=forecast.dew_point,
        relative_humidity=forecast.relative_humidity,
        wind_speed=forecast.wind_speed,
        wind_direction=forecast.wind_direction,
        total_precipitation=forecast.total_precipitation,
        accumulated_rain=forecast.accumulated_rain,
        accumulated_snow=forecast.accumulated_snow,
        accumulated_freezing_rain=forecast.accumulated_freezing_rain,
        accumulated_ice_pellets=forecast.accumulated_ice_pellets,
        cloud_cover=forecast.cloud_cover,
        sea_level_pressure=forecast.sea_level_pressure,
        wind_speed_40m=forecast.wind_speed_40m,
        wind_direction_40m=forecast.wind_direction_40m,
        wind_direction_80m=forecast.wind_direction_80m,
        wind_speed_120m=forecast.wind_speed_120m,
        wind_direction_120m=forecast.wind_direction_120m,
        wind_speed_925mb=forecast.wind_speed_925mb,
        wind_direction_925mb=forecast.wind_direction_925mb,
        wind_speed_850mb=forecast.wind_speed_850mb,
        wind_direction_850mb=forecast.wind_direction_850mb
    )
    db_session.add(new_single_forecast)
    db_session.commit()
    db_session.refresh(new_single_forecast)
    return (
        db_session.query(SingleForecast)
        .filter(SingleForecast.forecast_datetime == forecast.datetime)
        .filter(SingleForecast.issue_date == issue_date)
        .filter(SingleForecast.weather_station == weather_station).first()
    )
