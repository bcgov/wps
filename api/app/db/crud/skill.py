"""CRUD operations relating to skill scoring"""

from typing import List
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session
from datetime import date, datetime, time, timedelta
from app.db.models.observations import HourlyActual
from app.db.models.weather_models import PredictionModel, PredictionModelRunTimestamp, WeatherStationModelPrediction
from app.utils.time import get_hour_20_from_date
from app.weather_models import ModelEnum

# The 12Z model run hour
MODEL_RUN_HOUR = 12


def get_skill_score_data(session: Session, start_date: date, days: int, stations: List[int]):
    result = get_skill_score_data_for_model(session, start_date, days, stations, ModelEnum.RDPS)
    return result


def get_skill_score_data_for_model(session: Session, start_date: date, days: int, stations: List[int], model: ModelEnum):
    # Hourly observation times
    hourly_start = get_hour_20_from_date(start_date)
    hourly_actual_times = []
    for day in range(1, days + 1):
        hourly_actual_times.append(hourly_start - timedelta(days=day))
    # Subquery to filter for correct numerical weather model (eg. HRDPS, RDPS, etc.)
    # prediction_model = select(PredictionModel).where(PredictionModel.abbreviation == model.value).subquery()

    # Subquery to filter for weather station model predictions by stations and prediction times
    predictions = (
        select(WeatherStationModelPrediction)
        .where(WeatherStationModelPrediction.station_code.in_(stations))
        .where(WeatherStationModelPrediction.prediction_timestamp.in_(hourly_actual_times))
        .subquery()
    )

    # Subquery to join predictions to actuals
    predictions_and_actuals = (
        select(HourlyActual, predictions)
        .join(predictions, and_(HourlyActual.station_code == predictions.c.station_code, HourlyActual.weather_date == predictions.c.prediction_timestamp))
        .subquery()
    )

    # Subquery to filter numerical weather model runs by prediction model and model run hour (12Z)
    model_runs = (
        select(PredictionModelRunTimestamp, PredictionModel.abbreviation)
        .join(PredictionModel, PredictionModel.id == PredictionModelRunTimestamp.prediction_model_id)
        .where(func.date_part("hour", PredictionModelRunTimestamp.prediction_run_timestamp) == MODEL_RUN_HOUR)
        .subquery()
    )

    # Final query to filter the predictions and actuals to the matching model runs
    stmt = (
        select(
            model_runs.c.abbreviation,
            predictions_and_actuals.c.prediction_timestamp,
            model_runs.c.prediction_run_timestamp,
            predictions_and_actuals.c.tmp_tgl_2,
            predictions_and_actuals.c.temperature,
            predictions_and_actuals.c.bias_adjusted_temperature,
            predictions_and_actuals.c.station_code,
        )
        .join(model_runs, predictions_and_actuals.c.prediction_model_run_timestamp_id == model_runs.c.id)
        .order_by(model_runs.c.prediction_run_timestamp, predictions_and_actuals.c.prediction_timestamp)
    )

    result = session.execute(stmt)
    return result
    # prediction_model_query = select(PredictionModel.abbreviation).where(PredictionModel.c.abbreviation == str(model.value))
    # prediction_model_query = select(PredictionModel)
    # q1 = (
    #     select(WeatherStationModelPrediction)
    #     .join(PredictionModelRunTimestamp, WeatherStationModelPrediction.prediction_model_run_timestamp_id == PredictionModelRunTimestamp.id)
    #     .where(WeatherStationModelPrediction.prediction_timestamp.in_(hourly_actual_times))
    #     .where()
    # )

    # result = session.execute(prediction_model_query)

    # prediction_times
    # query =
    # subquery = (
    #     session.query(MorecastForecastRecord.station_code, func.max(MorecastForecastRecord.create_timestamp).label("most_recent"), MorecastForecastRecord.for_date)
    #     .filter(MorecastForecastRecord.for_date.between(start_date, end_date))
    #     .filter(MorecastForecastRecord.station_code.in_(stations))
    #     .group_by(MorecastForecastRecord.station_code, MorecastForecastRecord.for_date)
    #     .subquery()
    # )

    # query = session.query(MorecastForecastRecord).join(
    #     subquery,
    #     and_(
    #         MorecastForecastRecord.station_code == subquery.c.station_code,
    #         MorecastForecastRecord.create_timestamp == subquery.c.most_recent,
    #         MorecastForecastRecord.for_date == subquery.c.for_date,
    #     ),
    # )
    # return query.all()