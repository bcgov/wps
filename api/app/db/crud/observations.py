""" CRUD operations relating to observed readings (a.k.a "hourlies")
"""
import datetime
from typing import List
from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.db.models import ModelRunGridSubsetPrediction, PredictionModelRunTimestamp
from app.db.models.observations import HourlyActual


def get_hourly_actuals(
        session: Session,
        station_codes: List[int],
        start_date: datetime,
        end_date: datetime = None):
    """ Query for hourly actuals for given stations, from stated start_date to end_date.

    :param end_date: If specified, return up to and including the end_date
    """
    # pylint: disable=singleton-comparison
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


def get_actuals_left_outer_join_with_predictions(  # pylint: disable=too-many-arguments
        session: Session, model_id: int, grid_id: int, station_code: int,
        start_date: datetime, end_date: datetime):
    """
    NOTE: Can improve this query by only returning the most recent prediction, maybe using nested
    queries. It works for now - but things could be faster.
    """
    # pylint: disable=singleton-comparison
    return session.query(HourlyActual, ModelRunGridSubsetPrediction)\
        .outerjoin(ModelRunGridSubsetPrediction,
                   and_(ModelRunGridSubsetPrediction.prediction_timestamp == HourlyActual.weather_date,
                        ModelRunGridSubsetPrediction.prediction_model_grid_subset_id == grid_id))\
        .outerjoin(PredictionModelRunTimestamp,
                   and_(PredictionModelRunTimestamp.id ==
                        ModelRunGridSubsetPrediction.prediction_model_run_timestamp_id,
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
