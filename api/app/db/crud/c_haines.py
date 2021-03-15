""" CRUD for CHaines
"""
from datetime import timedelta, datetime
import logging
from sqlalchemy import desc, asc
from sqlalchemy.orm import Session
from app.weather_models import ModelEnum
from app.db.models import CHainesPrediction, CHainesModelRun, PredictionModel, CHainesPoly
from app.time_utils import get_utc_now


logger = logging.getLogger(__name__)


def delete_older_than(session: Session, point_in_time: datetime):
    """ Delete any c-haines data older than the specified point in time """
    # NOTE: I couldn't get cascading to work - and gave up as it was taking too
    # much time. It seems deleting records in sqlalchmey isn't all that straight
    # forward.

    logger.info('deleting c-hains model run data older than %s', point_in_time)

    # Fetch all the model runs.
    model_runs = session.query(CHainesModelRun)\
        .filter(CHainesModelRun.model_run_timestamp < point_in_time)
    for model_run in model_runs:
        # Fetch all the predictions for this model run.
        predictions = session.query(CHainesPrediction)\
            .filter(CHainesPrediction.model_run_id == model_run.id)

        logger.info('delete polygons for model run %s', model_run)
        for prediction in predictions:
            # Delete all the polygons for this prediction.
            polygons_deleted = session.query(CHainesPoly)\
                .filter(CHainesPoly.c_haines_prediction_id == prediction.id)\
                .delete()
            logger.debug('deleted %s polygons for %s', polygons_deleted, prediction)

        logger.info('delete predictions for model run: %s', model_run)
        # Delete predictions.
        predictions = session.query(CHainesPrediction)\
            .filter(CHainesPrediction.model_run_id == model_run.id)\
            .delete()
        logger.info('deleted %s predictions', predictions)

    # Delete model runs.
    # synchronize_session=False ??
    # NOTE: In a perfect world we'd need only this command, and everything would cascade.
    model_runs = session.query(CHainesModelRun)\
        .filter(CHainesModelRun.model_run_timestamp < point_in_time).delete()
    logger.info('deleted %s model runs', model_runs)


def get_most_recent_model_run(session: Session, model: ModelEnum) -> CHainesModelRun:
    """ Return the most recent model run for which we have at least one prediction. """
    return session.query(CHainesModelRun)\
        .join(PredictionModel, PredictionModel.id == CHainesModelRun.prediction_model_id)\
        .join(CHainesPrediction, CHainesPrediction.model_run_id == CHainesModelRun.id)\
        .filter(PredictionModel.abbreviation == model)\
        .order_by(desc(CHainesModelRun.model_run_timestamp)).limit(1).first()


def get_c_haines_model_run(
        session: Session,
        model_run_timestamp: datetime,
        prediction_model: PredictionModel) -> CHainesModelRun:
    """ Return a single c-haines model run for a given timestamp. """
    return session.query(CHainesModelRun).filter(
        CHainesModelRun.model_run_timestamp == model_run_timestamp,
        CHainesModelRun.prediction_model_id == prediction_model.id
    ).first()


def create_c_haines_model_run(
        session: Session,
        model_run_timestamp: datetime,
        prediction_model: PredictionModel) -> CHainesModelRun:
    """ Create a c-haines model run. """
    model_run = CHainesModelRun(model_run_timestamp=model_run_timestamp,
                                prediction_model=prediction_model)
    session.add(model_run)
    return model_run


def get_or_create_c_haines_model_run(
        session: Session,
        model_run_timestamp: datetime,
        prediction_model: PredictionModel) -> CHainesModelRun:
    """ Get a model run, creating on if it doesn't exist. """
    model_run = get_c_haines_model_run(session, model_run_timestamp, prediction_model)
    if not model_run:
        model_run = create_c_haines_model_run(session, model_run_timestamp, prediction_model)
    return model_run


def get_c_haines_prediction(
        session: Session,
        model_run: CHainesModelRun,
        prediction_timestamp: datetime) -> CHainesPrediction:
    """ Get the c-haines prediction """
    return session.query(CHainesPrediction)\
        .filter(CHainesPrediction.model_run_id == model_run.id,
                CHainesPrediction.prediction_timestamp == prediction_timestamp)


def get_model_run_predictions(session: Session, model_run_timestamp: datetime):
    """ Get some recent model runs """
    if model_run_timestamp:
        # Get the day before and after the specified timestamp.
        end_date = model_run_timestamp + timedelta(days=1)
        start_date = model_run_timestamp - timedelta(days=1)
    else:
        # No timestamp? Get the last three days.
        end_date = get_utc_now()
        start_date = get_utc_now() - timedelta(days=3)

    query = session.query(CHainesModelRun.id,
                          CHainesModelRun.model_run_timestamp,
                          PredictionModel.name, PredictionModel.abbreviation,
                          CHainesPrediction.prediction_timestamp)\
        .join(CHainesModelRun, CHainesModelRun.id == CHainesPrediction.model_run_id)\
        .join(PredictionModel, PredictionModel.id == CHainesModelRun.prediction_model_id)\
        .filter(CHainesModelRun.model_run_timestamp >= start_date,
                CHainesModelRun.model_run_timestamp < end_date)\
        .order_by(desc(CHainesModelRun.model_run_timestamp), CHainesModelRun.id,
                  asc(CHainesPrediction.prediction_timestamp))
    return query


def get_model_run_kml(session: Session,
                      model: ModelEnum,
                      model_run_timestamp: datetime):
    """ Get the kml for a particular prediction """
    query = """select ST_AsKML(ST_SetSRID(t.geom, 4269)), t.c_haines_index, t.prediction_timestamp from (
        select geom, c_haines_index, prediction_timestamp from c_haines_polygons
        inner join c_haines_predictions on
            c_haines_predictions.id =
            c_haines_polygons.c_haines_prediction_id
        inner join c_haines_model_runs on
            c_haines_model_runs.id = 
            c_haines_predictions.model_run_id
        inner join prediction_models on
            prediction_models.id =
            c_haines_model_runs.prediction_model_id
        where
            model_run_timestamp = '{model_run_timestamp}' and
            prediction_models.abbreviation = '{model}'
        order by prediction_timestamp asc, c_haines_index asc
    ) as t(geom, c_haines_index)""".format(
        model_run_timestamp=model_run_timestamp.isoformat(),
        model=model)
    # pylint: disable=no-member
    return session.execute(query)


def get_prediction_kml(session: Session,
                       model: ModelEnum,
                       model_run_timestamp: datetime,
                       prediction_timestamp: datetime):
    """ Get the kml for a particular prediction """
    query = """select ST_AsKML(ST_SetSRID(t.geom, 4269)), t.c_haines_index from (
        select geom, c_haines_index from c_haines_polygons
        inner join c_haines_predictions on
            c_haines_predictions.id =
            c_haines_polygons.c_haines_prediction_id
        inner join c_haines_model_runs on
            c_haines_model_runs.id = 
            c_haines_predictions.model_run_id
        inner join prediction_models on
            prediction_models.id =
            c_haines_model_runs.prediction_model_id
        where
            prediction_timestamp = '{prediction_timestamp}' and
            model_run_timestamp = '{model_run_timestamp}' and
            prediction_models.abbreviation = '{model}'
        order by c_haines_index asc
    ) as t(geom, c_haines_index)""".format(
        prediction_timestamp=prediction_timestamp.isoformat(),
        model_run_timestamp=model_run_timestamp.isoformat(),
        model=model)
    # pylint: disable=no-member
    return session.execute(query)


def get_prediction_geojson(session: Session,
                           model: ModelEnum,
                           model_run_timestamp: datetime,
                           prediction_timestamp: datetime):
    """ Get the geojson for a particular prediction """
    query = """select json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(ST_AsGeoJSON(t.*)::json)
    )
        from (
        select geom, c_haines_index from c_haines_polygons
        inner join c_haines_predictions on
            c_haines_predictions.id =
            c_haines_polygons.c_haines_prediction_id
        inner join c_haines_model_runs on
            c_haines_model_runs.id = 
            c_haines_predictions.model_run_id
        inner join prediction_models on
            prediction_models.id =
            c_haines_model_runs.prediction_model_id
        where
            prediction_timestamp = '{prediction_timestamp}' and
            model_run_timestamp = '{model_run_timestamp}' and
            prediction_models.abbreviation = '{model}'
        order by c_haines_index asc
    ) as t(geom, c_haines_index)""".format(
        prediction_timestamp=prediction_timestamp.isoformat(),
        model_run_timestamp=model_run_timestamp.isoformat(),
        model=model)
    # pylint: disable=no-member
    response = session.execute(query)
    row = next(response)
    return row[0]
