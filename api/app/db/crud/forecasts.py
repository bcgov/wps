""" CRUD operations relating to forecasts made by forecasters.
"""
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.schemas.stations import StationCodeList
from app.db.models.forecasts import NoonForecast


def query_noon_forecast_records(session: Session,
                                station_codes: StationCodeList,
                                start_date: datetime,
                                end_date: datetime
                                ):
    """ Sends a query to get noon forecast records """
    return session.query(NoonForecast)\
        .filter(NoonForecast.station_code.in_(station_codes))\
        .filter(NoonForecast.weather_date >= start_date)\
        .filter(NoonForecast.weather_date <= end_date)\
        .order_by(NoonForecast.weather_date)\
        .order_by(desc(NoonForecast.created_at))


def save_noon_forecast(session: Session, noon_forecast: NoonForecast):
    """ Abstraction for writing NoonForecast to database. """
    session.add(noon_forecast)
    session.commit()
