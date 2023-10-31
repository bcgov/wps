""" CRUD operations relating to observed readings (a.k.a "hourlies")
"""
import datetime
from typing import List
from sqlalchemy import and_, select, text
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from app.db.models.weather_models import (ModelRunPrediction, PredictionModel, PredictionModelRunTimestamp,
                                          WeatherStationModelPrediction)
from app.db.models.observations import HourlyActual


def get_hourly_actuals(
        session: Session,
        station_codes: List[int],
        start_date: datetime,
        end_date: datetime = None):
    """ Query for hourly actuals for given stations, from stated start_date to end_date.

    :param end_date: If specified, return up to and including the end_date
    """
    query = session.query(HourlyActual)\
        .filter(HourlyActual.station_code.in_(station_codes))\
        .filter(HourlyActual.weather_date >= start_date)\
        .filter(HourlyActual.temp_valid == True)\
        .filter(HourlyActual.rh_valid == True)
    if end_date is not None:
        query = query.filter(HourlyActual.weather_date <= end_date)
    query = query.order_by(HourlyActual.station_code)\
        .order_by(HourlyActual.weather_date)
    return query


def get_actuals_left_outer_join_with_predictions(
        session: Session, model_id: int, station_code: int,
        start_date: datetime, end_date: datetime):
    """
    NOTE: Can improve this query by only returning the most recent prediction, maybe using nested
    queries. It works for now - but things could be faster.
    """
    return session.query(HourlyActual, ModelRunPrediction)\
        .outerjoin(ModelRunPrediction,
                   and_(ModelRunPrediction.prediction_timestamp == HourlyActual.weather_date,
                        ModelRunPrediction.station_code == station_code))\
        .outerjoin(PredictionModelRunTimestamp,
                   and_(PredictionModelRunTimestamp.id ==
                        ModelRunPrediction.prediction_model_run_timestamp_id,
                        PredictionModelRunTimestamp.prediction_model_id == model_id))\
        .filter(HourlyActual.station_code == station_code)\
        .filter(HourlyActual.weather_date >= start_date)\
        .filter(HourlyActual.temp_valid == True)\
        .filter(HourlyActual.rh_valid == True)\
        .filter(HourlyActual.weather_date <= end_date)\
        .order_by(HourlyActual.station_code)\
        .order_by(HourlyActual.weather_date)\
        .order_by(PredictionModelRunTimestamp.prediction_run_timestamp.desc())


def save_hourly_actual(session: Session, hourly_actual: HourlyActual):
    """ Abstraction for writing HourlyActual to database. """
    session.add(hourly_actual)
    session.commit()


def get_accumulated_precipitation(session: Session, station_code: int, start_datetime: datetime, end_datetime: datetime):
    """ Get the accumulated precipitation for a station by datetime range. """
    stmt = select(func.sum(HourlyActual.precipitation))\
        .where(HourlyActual.station_code == station_code, HourlyActual.weather_date > start_datetime, HourlyActual.weather_date <= end_datetime)
    result = session.scalars(stmt).first()
    if result is None:
        return 0
    return result


def get_accumulated_precip_by_24h_interval(session: Session, station_code: int, start_datetime: datetime, end_datetime: datetime):
    """ Get the accumulated precip for 24 hour intervals for a given station code within the specified time interval.
    :param session: The ORM/database session.
    :param station_code: The numeric code identifying the weather station of interest.
    :param start_datetime: The earliest date and time of interest.
    :param end_datetime: The latest date and time of interest.
    
    Note: I couldn't construct this query in SQLAlchemy, hence the need for the 'text' based query.

    generate_series(\'{}\', \'{}\', '24 hours'::interval)

    This gives us a one column table of dates separated by 24 hours between the start and end dates. For example, if start and end dates are 2023-10-31 20:00:00 to 2023-11-03 20:00:00 we would have a table like:

    day
    2023-10-31 20:00:00
    2023-11-01 20:00:00
    2023-11-02 20:00:00
    2023-11-03 20:00:00

    We then join the HourlyActuals table so that we can sum hourly precip in a 24 hour period. The join is based on the weather_date field in the HourlyActuals table being in a 24 hour range using this odd looking syntax:

    weather_date <@ tstzrange(day, day + '24 hours', '(]')

    Using 2023-10-31 20:00:00 as an example, rows with the following dates would match. The (] syntax means the lower bound is excluded but the upper bound is included.

    2023-10-31 21:00:00
    2023-10-31 22:00:00
    2023-10-31 23:00:00
    2023-11-01 00:00:00
    2023-11-01 01:00:00
    ....
    2023-11-01 19:00:00
    2023-11-01 20:00:00    
    """
    stmt = """
        SELECT day, station_code, sum(precipitation) actual_precip_24h
        FROM
            generate_series(\'{}\', \'{}\', '24 hours'::interval) day
        LEFT JOIN
            hourly_actuals
        ON 
            weather_date <@ tstzrange(day, day - '24 hours', '(]')
        WHERE
            station_code = {}
        GROUP BY
            day, station_code;
    """.format(start_datetime, end_datetime, station_code)
    result = session.execute(text(stmt))
    return result.all()


def get_predicted_daily_precip(session: Session, model: PredictionModel, station_code: int, start_datetime: datetime, end_datetime: datetime):
    """ Gets rows from WeatherStationModelPrediction for the given model and station within the
    specified time interval at 20:00:00 UTC each day.
    :param session: The ORM/database session
    :param model: The numeric weather prediction model
    :param station_code: The code identifying the weather station.
    :param start_datetime: The earliest date and time of interest.
    :param end_datetime: The latest date and time of interest. 
    """
    result = session.query(WeatherStationModelPrediction)\
        .join(PredictionModelRunTimestamp, PredictionModelRunTimestamp.id == WeatherStationModelPrediction.prediction_model_run_timestamp_id)\
        .filter(PredictionModelRunTimestamp.prediction_model_id == model.id)\
        .filter(WeatherStationModelPrediction.station_code == station_code)\
        .filter(WeatherStationModelPrediction.prediction_timestamp >= start_datetime)\
        .filter(WeatherStationModelPrediction.prediction_timestamp < end_datetime)\
        .filter(func.date_part('hour', WeatherStationModelPrediction.prediction_timestamp) == 20)\
        .order_by(WeatherStationModelPrediction.prediction_timestamp)
    return result.all()
