""" CRUD for CHaines
"""
from datetime import timedelta, datetime
import logging
from sqlalchemy import desc, asc
from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from app.weather_models import ModelEnum
from app.db.models import CHainesPrediction, CHainesModelRun, PredictionModel, CHainesPoly
from app.utils.time import get_utc_now


logger = logging.getLogger(__name__)


def delete_older_than(session: Session, point_in_time: datetime):
    """ Delete any c-haines data older than the specified point in time """
    # NOTE: I couldn't get cascading to work - and gave up as it was taking too
    # much time. It seems deleting records in sqlalchmey isn't all that straight
    # forward.

    logger.info('deleting c-haines model run data older than %s', point_in_time)

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


def get_prediction_geojson(session: Session,
                           model: ModelEnum,
                           model_run_timestamp: datetime,
                           prediction_timestamp: datetime):
    """ Get the geojson for a particular prediction, in WGS84. (Stored as NAD83 in DB, but KML and GeoJSON
    expect WGS84)
    """
    query = text("""select json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(ST_AsGeoJSON(t.*)::json)
    )
        from (
        select ST_Transform(geom, 'epsg:4269', 'epsg:4326'), c_haines_index from c_haines_polygons
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
            prediction_timestamp = :prediction_timestamp and
            model_run_timestamp = :model_run_timestamp and
            prediction_models.abbreviation = :model
        order by c_haines_index asc
    ) as t(geom, c_haines_index)""")
    # pylint: disable=no-member
    response = session.execute(query, {
        "prediction_timestamp": prediction_timestamp.isoformat(),
        "model_run_timestamp": model_run_timestamp.isoformat(),
        "model": model
    })
    row = next(response)
    return row[0]
