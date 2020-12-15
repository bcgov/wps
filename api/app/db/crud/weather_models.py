""" CRUD operations for management of weather model data.
"""
import logging
import datetime
from typing import List, Union
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.weather_models import ModelEnum
from app.db.models import (
    ProcessedModelRunUrl, PredictionModel, PredictionModelRunTimestamp, PredictionModelGridSubset,
    ModelRunGridSubsetPrediction, WeatherStationModelPrediction)
import app.time_utils as time_utils

logger = logging.getLogger(__name__)

# --------------  COMMON UTILITY FUNCTIONS ---------------------------


def _construct_grid_filter(coordinates):
    # Run through each coordinate, adding it to the "or" construct.
    geom_or = None
    for coordinate in coordinates:
        condition = PredictionModelGridSubset.geom.ST_Contains(
            'POINT({longitude} {latitude})'.format(longitude=coordinate[0], latitude=coordinate[1]))
        if geom_or is None:
            geom_or = or_(condition)
        else:
            geom_or = or_(condition, geom_or)
    return geom_or


# ----------- end of UTILITY FUNCTIONS ------------------------


def get_or_create_grid_subset(session: Session,
                              prediction_model: PredictionModel,
                              geographic_points) -> PredictionModelGridSubset:
    """ Get the subset of grid points of interest. """
    geom = 'POLYGON(({} {}, {} {}, {} {}, {} {}, {} {}))'.format(
        geographic_points[0][0], geographic_points[0][1],
        geographic_points[1][0], geographic_points[1][1],
        geographic_points[2][0], geographic_points[2][1],
        geographic_points[3][0], geographic_points[3][1],
        geographic_points[0][0], geographic_points[0][1])
    grid_subset = session.query(PredictionModelGridSubset).\
        filter(PredictionModelGridSubset.prediction_model_id == prediction_model.id).\
        filter(PredictionModelGridSubset.geom == geom).first()
    if not grid_subset:
        logger.info('creating grid subset %s', geographic_points)
        grid_subset = PredictionModelGridSubset(
            prediction_model_id=prediction_model.id, geom=geom)
        session.add(grid_subset)
        session.commit()
    return grid_subset


def get_most_recent_model_run(
        session: Session, abbreviation: str, projection: str) -> PredictionModelRunTimestamp:
    """
    Get the most recent model run of a specified type. (.e.g. give me the global
    model at 15km resolution)

    params:
    :abbreviation: e.g. GDPS or RDPS
    :projection: e.g. latlon.15x.15
    """
    # NOTE: Don't be fooled into saying "PredictionModelRunTimestamp.complete is True", it won't work.
    # pylint: disable=singleton-comparison
    return session.query(PredictionModelRunTimestamp).\
        join(PredictionModel).\
        filter(PredictionModel.id == PredictionModelRunTimestamp.prediction_model_id).\
        filter(PredictionModel.abbreviation == abbreviation,
               PredictionModel.projection == projection).\
        filter(PredictionModelRunTimestamp.complete == True).\
        order_by(PredictionModelRunTimestamp.prediction_run_timestamp.desc()).\
        first()  # noqa: E712


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


def get_grid_for_coordinate(session: Session,
                            prediction_model: PredictionModel,
                            coordinate) -> PredictionModelGridSubset:
    """ Given a specified coordinate and model, return the appropriate grid. """
    logger.info("Model %s, coords %s,%s", prediction_model.id,
                coordinate[1], coordinate[0])
    query = session.query(PredictionModelGridSubset).\
        filter(PredictionModelGridSubset.geom.ST_Contains(
            'POINT({longitude} {latitude})'.format(longitude=coordinate[0], latitude=coordinate[1]))).\
        filter(PredictionModelGridSubset.prediction_model_id == prediction_model.id)
    return query.first()


def get_model_run_predictions_for_grid(session: Session,
                                       prediction_run: PredictionModelRunTimestamp,
                                       grid: PredictionModelGridSubset) -> List:
    """ Get all the predictions for a provided model run and grid. """
    logger.info("Getting model predictions for grid %s", grid)
    return session.query(ModelRunGridSubsetPrediction).\
        filter(ModelRunGridSubsetPrediction.prediction_model_grid_subset_id == grid.id).\
        filter(ModelRunGridSubsetPrediction.prediction_model_run_timestamp_id ==
               prediction_run.id)


def get_model_run_predictions(
        session: Session,
        prediction_run: PredictionModelRunTimestamp,
        coordinates) -> List:
    """
    Get the predictions for a particular model run, for a specified geographical coordinate.

    Returns a PredictionModelGridSubset with joined Prediction and PredictionValueType."""
    # condition for query: are coordinates within the saved grids
    geom_or = _construct_grid_filter(coordinates)

    # We are only interested in predictions from now onwards
    now = time_utils.get_utc_now()

    # Build up the query:
    query = session.query(PredictionModelGridSubset, ModelRunGridSubsetPrediction).\
        filter(geom_or).\
        filter(ModelRunGridSubsetPrediction.prediction_model_run_timestamp_id == prediction_run.id).\
        filter(ModelRunGridSubsetPrediction.prediction_model_grid_subset_id == PredictionModelGridSubset.id).\
        filter(ModelRunGridSubsetPrediction.prediction_timestamp >= now).\
        order_by(PredictionModelGridSubset.id,
                 ModelRunGridSubsetPrediction.prediction_timestamp.asc())
    return query


def get_predictions_from_coordinates(session: Session, coordinates: List, model: str) -> List:
    """ Get the predictions for a particular model, at a specified geographical coordinate. """
    # condition for query: are coordinates within the saved grids
    geom_or = _construct_grid_filter(coordinates)

    # We are only interested in the last 5 days.
    now = time_utils.get_utc_now()
    back_5_days = now - datetime.timedelta(days=5)

    # Build the query:
    query = session.query(PredictionModelGridSubset,
                          ModelRunGridSubsetPrediction,
                          PredictionModel).\
        filter(geom_or).\
        filter(ModelRunGridSubsetPrediction.prediction_timestamp >= back_5_days,
               ModelRunGridSubsetPrediction.prediction_timestamp <= now).\
        filter(PredictionModelGridSubset.id ==
               ModelRunGridSubsetPrediction.prediction_model_grid_subset_id).\
        filter(PredictionModelGridSubset.prediction_model_id == PredictionModel.id,
               PredictionModel.abbreviation == model).\
        order_by(PredictionModelGridSubset.id,
                 ModelRunGridSubsetPrediction.prediction_timestamp.asc())
    return query


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


def get_station_model_prediction_from_previous_model_run(
        session: Session,
        station_codes: List[int],
        model: str,
        prediction_timestamp: datetime.datetime,
        prediction_model_run_timestamp: datetime.datetime) -> Union[WeatherStationModelPrediction, PredictionModelRunTimestamp, PredictionModel]:
    """ Fetches the one model prediction for the specified station_code, model, and prediction_timestamp
    from the prediction model run immediately previous to the given prediction_model_run_timestamp.
    """
    # create a lower_bound for time range so that we're not querying timestamps all the way back to the
    # beginning of time
    lower_bound = prediction_model_run_timestamp - datetime.timedelta(days=1)
    response = session.query(WeatherStationModelPrediction, PredictionModelRunTimestamp, PredictionModel).\
        filter(WeatherStationModelPrediction.station_code.in_(station_codes)).\
        filter(WeatherStationModelPrediction.prediction_timestamp == prediction_timestamp).\
        filter(PredictionModelRunTimestamp.prediction_model_id == PredictionModel.id, PredictionModel.abbreviation == model).\
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


def get_prediction_model(session: Session, abbreviation: str, projection: str) -> PredictionModel:
    """ Get the prediction model corresponding to a particular abbreviation and projection. """
    return session.query(PredictionModel).\
        filter(PredictionModel.abbreviation == abbreviation).\
        filter(PredictionModel.projection == projection).first()


def get_prediction_model_run_timestamp_records(
        session: Session, model_type: ModelEnum, complete: bool = True, interpolated: bool = True):
    """ Get prediction model run timestamps (filter on complete and interpolated if provided.) """
    query = session.query(PredictionModelRunTimestamp, PredictionModel) \
        .join(PredictionModelRunTimestamp,
              PredictionModelRunTimestamp.prediction_model_id == PredictionModel.id)\
        .filter(PredictionModel.abbreviation == model_type)
    if interpolated is not None:
        query = query.filter(
            PredictionModelRunTimestamp.interpolated == interpolated)
    if complete is not None:
        query = query.filter(PredictionModelRunTimestamp.complete == complete)
    query = query.order_by(
        PredictionModelRunTimestamp.prediction_run_timestamp.desc())
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
