from datetime import datetime, timedelta, timezone
from sqlalchemy.sql.expression import literal
from sqlalchemy.orm import Session
from app.db.models.forecasts import NoonForecast
from app.db.models.observations import HourlyActual


def _get_noon_date(date_of_interest: datetime):
    """ 
    If before noon today, give noon from day before.
    If after noon today, give noon from date of interest.
    """
    noon_for_today = datetime(year=date_of_interest.year,
                              month=date_of_interest.month,
                              day=date_of_interest.day,
                              hour=20, tzinfo=timezone.utc)
    if date_of_interest < noon_for_today:
        # oh - you want noon for the prevous day
        yesterday = date_of_interest - timedelta(days=1)
        return datetime(
            year=yesterday.year, month=yesterday.month, day=yesterday.day, hour=20, tzinfo=timezone.utc)
    # you want noon for today
    return noon_for_today


def get_noon_forecast_observation_union(session: Session, date_of_interest: datetime):
    """ Return union of forecasts and observations.
    """
    noon_date = _get_noon_date(date_of_interest)
    forecast_query = session.query(
        literal('forecast').label('type'),
        NoonForecast.station_code, NoonForecast.temperature, NoonForecast.relative_humidity)\
        .filter(NoonForecast.rh_valid is True, NoonForecast.temp_valid is True)\
        .filter(NoonForecast.weather_date == noon_date)\
        .order_by(NoonForecast.station_code)
    observation_query = session.query(
        literal('observation').label('type'),
        HourlyActual.station_code, HourlyActual.temperature, HourlyActual.relative_humidity)\
        .filter(HourlyActual.rh_valid is True, HourlyActual.temp_valid is True)\
        .filter(HourlyActual.weather_date == noon_date)\
        .order_by(HourlyActual.station_code)

    return forecast_query.union(observation_query)
