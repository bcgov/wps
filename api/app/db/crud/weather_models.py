""" CRUD operations for management of weather model data.
"""
import logging
import datetime
from typing import List, Union
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.weather_models import ModelEnum, ProjectionEnum
from app.db.models.weather_models import (
    ProcessedModelRunUrl, PredictionModel, PredictionModelRunTimestamp,
    ModelRunPrediction, WeatherStationModelPrediction, MoreCast2MaterializedView)

logger = logging.getLogger(__name__)


def get_prediction_run(session: Session, prediction_model_id: int,
                       prediction_run_timestamp: datetime.datetime) -> PredictionModelRunTimestamp:
    """ load the model run from the database (.e.g. for 2020 07 07 12h00). """
    logger.info('get prediction run for %s', prediction_run_timestamp)
    return session.query(PredictionModelRunTimestamp).\
        filter(PredictionModelRunTimestamp.prediction_model_id == prediction_model_id).\
        filter(PredictionModelRunTimestamp.prediction_run_timestamp ==
               prediction_run_timestamp).first()


def create_prediction_run(
        session: Session,
        prediction_model_id: int,
        prediction_run_timestamp: datetime.datetime,
        complete: bool,
        interpolated: bool) -> PredictionModelRunTimestamp:
    """ Create a model prediction run for a particular model.
    """
    prediction_run = PredictionModelRunTimestamp(
        prediction_model_id=prediction_model_id,
        prediction_run_timestamp=prediction_run_timestamp,
        complete=complete,
        interpolated=interpolated)
    session.add(prediction_run)
    session.commit()
    return prediction_run


def update_prediction_run(session: Session, prediction_run: PredictionModelRunTimestamp):
    """ Update a PredictionModelRunTimestamp record """
    session.add(prediction_run)
    session.commit()


def get_or_create_prediction_run(session, prediction_model: PredictionModel,
                                 prediction_run_timestamp: datetime.datetime) -> PredictionModelRunTimestamp:
    """ Get a model prediction run for a particular model, creating one if it doesn't already exist.
    """
    prediction_run = get_prediction_run(
        session, prediction_model.id, prediction_run_timestamp)
    if not prediction_run:
        logger.info('Creating prediction run %s for %s',
                    prediction_model.abbreviation, prediction_run_timestamp)
        prediction_run = create_prediction_run(
            session, prediction_model.id, prediction_run_timestamp, False, False)
    return prediction_run


def get_model_run_predictions_for_station(session: Session, station_code: int,
                              prediction_run: PredictionModelRunTimestamp) -> List:
    """ Get all the predictions for a provided model run """
    logger.info("Getting model predictions for grid %s", prediction_run)
    return session.query(ModelRunPrediction)\
        .filter(ModelRunPrediction.prediction_model_run_timestamp_id ==
               prediction_run.id)\
        .filter(ModelRunPrediction.station_code == station_code)\
        .order_by(ModelRunPrediction.prediction_timestamp)


def delete_weather_station_model_predictions(session: Session, older_than: datetime):
    """ Delete any weather model prediction older than a certain date.
    """
    logger.info('Deleting weather station model prediction data older than %s...', older_than)
    session.query(WeatherStationModelPrediction)\
        .filter(WeatherStationModelPrediction.prediction_timestamp < older_than)\
        .delete()


def get_station_model_predictions_order_by_prediction_timestamp(
        session: Session,
        station_codes: List,
        model: ModelEnum,
        start_date: datetime.datetime,
        end_date: datetime.datetime) -> List[
            Union[WeatherStationModelPrediction, PredictionModel]]:
    """ Fetch model predictions for given stations within given time range ordered by station code
    and prediction timestamp.

    This is useful if you're interested in seeing all the different predictions regardles of
    model run.
    """
    query = session.query(WeatherStationModelPrediction, PredictionModel).\
        join(PredictionModelRunTimestamp, PredictionModelRunTimestamp.id ==
             WeatherStationModelPrediction.prediction_model_run_timestamp_id).\
        join(PredictionModel, PredictionModel.id ==
             PredictionModelRunTimestamp.prediction_model_id).\
        filter(WeatherStationModelPrediction.station_code.in_(station_codes)).\
        filter(WeatherStationModelPrediction.prediction_timestamp >= start_date).\
        filter(WeatherStationModelPrediction.prediction_timestamp <= end_date).\
        filter(PredictionModel.abbreviation == model).\
        order_by(WeatherStationModelPrediction.station_code).\
        order_by(WeatherStationModelPrediction.prediction_timestamp)
    return query


def get_station_model_predictions(
        session: Session,
        station_codes: List,
        model: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime) -> List[
            Union[WeatherStationModelPrediction, PredictionModelRunTimestamp, PredictionModel]]:
    """ Fetches the model predictions that were most recently issued before the prediction_timestamp.
    Used to compare the most recent model predictions against forecasts and actuals for the same
    weather date and weather station.
    Only fetches WeatherStationModelPredictions for prediction_timestamps in the date range of
    start_date - end_date (inclusive).
    """
    query = session.query(WeatherStationModelPrediction, PredictionModelRunTimestamp, PredictionModel).\
        filter(WeatherStationModelPrediction.station_code.in_(station_codes)).\
        filter(WeatherStationModelPrediction.prediction_timestamp >= start_date).\
        filter(WeatherStationModelPrediction.prediction_timestamp <= end_date).\
        filter(PredictionModelRunTimestamp.id ==
               WeatherStationModelPrediction.prediction_model_run_timestamp_id).\
        filter(PredictionModelRunTimestamp.prediction_model_id == PredictionModel.id,
               PredictionModel.abbreviation == model).\
        order_by(WeatherStationModelPrediction.station_code).\
        order_by(WeatherStationModelPrediction.prediction_timestamp).\
        order_by(PredictionModelRunTimestamp.prediction_run_timestamp.asc())
    return query


def get_latest_station_model_prediction_per_day(session: Session,
                                                station_codes: List[int],
                                                model: str,
                                                day_start: datetime.datetime,
                                                day_end: datetime.datetime):
    """
    All weather station model predictions for:
     - a given day
     - a given model
     - each station in the given list
    ordered by update_timestamp

    This is done by joining the predictions on their runs,
    that are filtered by the day and the 20:00UTC predictions.

    In turn prediction runs are filtered via a join
    on runs that are for the selected model.
    """
    subquery = (
        session.query(
            func.max(WeatherStationModelPrediction.prediction_timestamp).label('latest_prediction'),
            WeatherStationModelPrediction.station_code,
            func.date(WeatherStationModelPrediction.prediction_timestamp).label('unique_day')
        )
        .filter(
            WeatherStationModelPrediction.station_code.in_(station_codes),
            WeatherStationModelPrediction.prediction_timestamp >= day_start,
            WeatherStationModelPrediction.prediction_timestamp <= day_end,
            func.date_part('hour', WeatherStationModelPrediction.prediction_timestamp) == 20
        )
        .group_by(
            WeatherStationModelPrediction.station_code,
            func.date(WeatherStationModelPrediction.prediction_timestamp).label('unique_day')
        )
        .subquery('latest')
    )

    result = session.query(
        WeatherStationModelPrediction.id,
        WeatherStationModelPrediction.prediction_timestamp,
        PredictionModel.abbreviation,
        WeatherStationModelPrediction.station_code,
        WeatherStationModelPrediction.rh_tgl_2,
        WeatherStationModelPrediction.tmp_tgl_2,
        WeatherStationModelPrediction.bias_adjusted_temperature,
        WeatherStationModelPrediction.bias_adjusted_rh,
        WeatherStationModelPrediction.apcp_sfc_0,
        WeatherStationModelPrediction.wdir_tgl_10,
        WeatherStationModelPrediction.wind_tgl_10,
        WeatherStationModelPrediction.update_date)\
        .join(PredictionModelRunTimestamp, WeatherStationModelPrediction.prediction_model_run_timestamp_id == PredictionModelRunTimestamp.id)\
        .join(PredictionModel, PredictionModelRunTimestamp.prediction_model_id == PredictionModel.id)\
        .join(subquery, and_(
            WeatherStationModelPrediction.prediction_timestamp == subquery.c.latest_prediction,
            WeatherStationModelPrediction.station_code == subquery.c.station_code))\
        .filter(PredictionModel.abbreviation == model)\
        .order_by(WeatherStationModelPrediction.update_date.desc())
    return result


def get_latest_station_prediction_mat_view(session: Session,
                                           station_codes: List[int],
                                           day_start: datetime.datetime,
                                           day_end: datetime.datetime):
    logger.info("Getting data from materialized view.")
    result = session.query(MoreCast2MaterializedView.prediction_timestamp,
                           MoreCast2MaterializedView.abbreviation,
                           MoreCast2MaterializedView.station_code,
                           MoreCast2MaterializedView.rh_tgl_2,
                           MoreCast2MaterializedView.tmp_tgl_2,
                           MoreCast2MaterializedView.bias_adjusted_temperature,
                           MoreCast2MaterializedView.bias_adjusted_rh,
                           MoreCast2MaterializedView.bias_adjusted_wind_speed,
                           MoreCast2MaterializedView.bias_adjusted_wdir,
                           MoreCast2MaterializedView.precip_24h,
                           MoreCast2MaterializedView.wdir_tgl_10,
                           MoreCast2MaterializedView.wind_tgl_10,
                           MoreCast2MaterializedView.update_date).\
        filter(MoreCast2MaterializedView.station_code.in_(station_codes),
               MoreCast2MaterializedView.prediction_timestamp >= day_start,
               MoreCast2MaterializedView.prediction_timestamp <= day_end)
    return result


def get_latest_station_prediction_per_day(session: Session,
                                          station_codes: List[int],
                                          day_start: datetime.datetime,
                                          day_end: datetime.datetime):
    """
    All weather station model predictions for:
     - a given day
     - each station in the given list
    ordered by update_timestamp

    This is done by joining the predictions on their runs,
    that are filtered by the day and the 20:00UTC predictions.

    In turn prediction runs are filtered via a join
    on runs that are for the selected model.
    """
    subquery = (
        session.query(
            func.max(WeatherStationModelPrediction.prediction_timestamp).label('latest_prediction'),
            WeatherStationModelPrediction.station_code,
            func.date(WeatherStationModelPrediction.prediction_timestamp).label('unique_day')
        )
        .filter(
            WeatherStationModelPrediction.station_code.in_(station_codes),
            WeatherStationModelPrediction.prediction_timestamp >= day_start,
            WeatherStationModelPrediction.prediction_timestamp <= day_end,
            func.date_part('hour', WeatherStationModelPrediction.prediction_timestamp) == 20
        )
        .group_by(
            WeatherStationModelPrediction.station_code,
            func.date(WeatherStationModelPrediction.prediction_timestamp).label('unique_day')
        )
        .subquery('latest')
    )

    result = session.query(
        WeatherStationModelPrediction.prediction_timestamp,
        PredictionModel.abbreviation,
        WeatherStationModelPrediction.station_code,
        WeatherStationModelPrediction.rh_tgl_2,
        WeatherStationModelPrediction.tmp_tgl_2,
        WeatherStationModelPrediction.bias_adjusted_temperature,
        WeatherStationModelPrediction.bias_adjusted_rh,
        WeatherStationModelPrediction.apcp_sfc_0,
        WeatherStationModelPrediction.wdir_tgl_10,
        WeatherStationModelPrediction.wind_tgl_10,
        WeatherStationModelPrediction.update_date)\
        .join(PredictionModelRunTimestamp, WeatherStationModelPrediction.prediction_model_run_timestamp_id == PredictionModelRunTimestamp.id)\
        .join(PredictionModel, PredictionModelRunTimestamp.prediction_model_id == PredictionModel.id)\
        .join(subquery, and_(
            WeatherStationModelPrediction.prediction_timestamp == subquery.c.latest_prediction,
            WeatherStationModelPrediction.station_code == subquery.c.station_code))\
        .order_by(WeatherStationModelPrediction.update_date.desc())
    return result


def get_station_model_prediction_from_previous_model_run(
        session: Session,
        station_code: int,
        model: ModelEnum,
        prediction_timestamp: datetime.datetime,
        prediction_model_run_timestamp: datetime.datetime) -> List[WeatherStationModelPrediction]:
    """ Fetches the one model prediction for the specified station_code, model, and prediction_timestamp
    from the prediction model run immediately previous to the given prediction_model_run_timestamp.
    """
    # create a lower_bound for time range so that we're not querying timestamps all the way back to the
    # beginning of time
    lower_bound = prediction_model_run_timestamp - datetime.timedelta(days=1)
    response = session.query(WeatherStationModelPrediction).\
        join(PredictionModelRunTimestamp,
             PredictionModelRunTimestamp.id ==
             WeatherStationModelPrediction.prediction_model_run_timestamp_id).\
        join(PredictionModel, PredictionModel.id ==
             PredictionModelRunTimestamp.prediction_model_id).\
        filter(WeatherStationModelPrediction.station_code == station_code).\
        filter(WeatherStationModelPrediction.prediction_timestamp == prediction_timestamp).\
        filter(PredictionModel.abbreviation == model).\
        filter(PredictionModelRunTimestamp.prediction_run_timestamp < prediction_model_run_timestamp).\
        filter(PredictionModelRunTimestamp.prediction_run_timestamp > lower_bound).\
        order_by(PredictionModelRunTimestamp.prediction_run_timestamp.desc()).\
        limit(1).first()

    return response


def get_processed_file_count(session: Session, urls: List[str]) -> int:
    """ Return the number of matching urls """
    return session.query(ProcessedModelRunUrl).filter(ProcessedModelRunUrl.url.in_(urls)).count()


def get_processed_file_record(session: Session, url: str) -> ProcessedModelRunUrl:
    """ Get record corresponding to a processed file. """
    processed_file = session.query(ProcessedModelRunUrl).\
        filter(ProcessedModelRunUrl.url == url).first()
    return processed_file


def get_prediction_model(session: Session,
                         model_enum: ModelEnum,
                         projection: ProjectionEnum) -> PredictionModel:
    """ Get the prediction model corresponding to a particular abbreviation and projection. """
    return session.query(PredictionModel).\
        filter(PredictionModel.abbreviation == model_enum.value).\
        filter(PredictionModel.projection == projection.value).first()


def get_prediction_model_run_timestamp_records(
        session: Session, model_type: ModelEnum, complete: bool = True, interpolated: bool = True):
    """ Get prediction model run timestamps (filter on complete and interpolated if provided.) """
    query = session.query(PredictionModelRunTimestamp, PredictionModel) \
        .join(PredictionModelRunTimestamp,
              PredictionModelRunTimestamp.prediction_model_id == PredictionModel.id)\
        .filter(PredictionModel.abbreviation == model_type.value)
    if interpolated is not None:
        query = query.filter(
            PredictionModelRunTimestamp.interpolated == interpolated)
    if complete is not None:
        query = query.filter(PredictionModelRunTimestamp.complete == complete)
    query = query.order_by(PredictionModelRunTimestamp.prediction_run_timestamp)
    return query


def get_weather_station_model_prediction(session: Session,
                                         station_code: int,
                                         prediction_model_run_timestamp_id: int,
                                         prediction_timestamp: datetime) -> WeatherStationModelPrediction:
    """ Get the model prediction for a weather station given a model run and a timestamp. """
    return session.query(WeatherStationModelPrediction).\
        filter(WeatherStationModelPrediction.station_code == station_code).\
        filter(WeatherStationModelPrediction.prediction_model_run_timestamp_id ==
               prediction_model_run_timestamp_id).\
        filter(WeatherStationModelPrediction.prediction_timestamp ==
               prediction_timestamp).first()


def refresh_morecast2_materialized_view(session: Session):
    start = datetime.datetime.now()
    logger.info("Refreshing morecast_2_materialized_view")
    session.execute(text("REFRESH MATERIALIZED VIEW morecast_2_materialized_view"))
    logger.info(f"Finished mat view refresh with elapsed time: {datetime.datetime.now() - start}")
