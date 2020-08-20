""" CRUD operations for management of resources
"""
import logging
import datetime
from typing import List
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.db.models import (
    ProcessedModelRunUrl, PredictionModel, PredictionModelRunTimestamp, PredictionModelGridSubset,
    ModelRunGridSubsetPrediction)


logger = logging.getLogger(__name__)

LATLON_15X_15 = 'latlon.15x.15'


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
        filter(PredictionModel.abbreviation == abbreviation, PredictionModel.projection == projection).\
        filter(PredictionModelRunTimestamp.complete == True).\
        order_by(PredictionModelRunTimestamp.prediction_run_timestamp.desc()).\
        first()


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
        complete: bool) -> PredictionModelRunTimestamp:
    """ Create a model prediction run for a particular model.
    """
    prediction_run = PredictionModelRunTimestamp(
        prediction_model_id=prediction_model_id,
        prediction_run_timestamp=prediction_run_timestamp,
        complete=complete)
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
            session, prediction_model.id, prediction_run_timestamp, False)
    return prediction_run


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
    now = datetime.datetime.now(tz=datetime.timezone.utc)

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
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    back_5_days = now - datetime.timedelta(days=5)

    # Build the query:
    query = session.query(PredictionModelGridSubset, ModelRunGridSubsetPrediction, PredictionModel).\
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
