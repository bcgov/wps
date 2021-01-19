""" Fetch c-haines geojson
"""
from datetime import datetime
import logging
import app.db.database
from app.schemas.weather_models import CHainesModelRuns, CHainesModelRunPredictions
from app.db.crud.c_haines import get_model_runs


logger = logging.getLogger(__name__)


async def fetch(model_run_timestamp: datetime, prediction_timestamp: datetime):
    """ Fetch polygon geojson
    """
    logger.info('model: %s; prediction: %s', model_run_timestamp, prediction_timestamp)
    # TODO: Add filters for model and timestamp (returning only the most recent model run)
    session = app.db.database.get_read_session()
    # Ordering by severity, ascending is important to ensure that
    # higher severity is placed over lower severity. (On the front end,
    # it makes it easier to have the high severity border sit on top and
    # pop nicely.)
    # TODO: This isn't safe - sql injection could happen! Fix.
    query = """select json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(ST_AsGeoJSON(t.*)::json)
    )
        from (
        select geom, severity from prediction_model_c_haines_polygons
        where 
            prediction_timestamp = '{prediction_timestamp}' and
            model_run_timestamp = '{model_run_timestamp}'
        order by severity asc
    ) as t(geom, severity)""".format(
        prediction_timestamp=prediction_timestamp.isoformat(),
        model_run_timestamp=model_run_timestamp.isoformat())
    # something is wrong here.
    logger.info('fetching geojson from db...')
    # pylint: disable=no-member
    response = session.execute(query)
    row = next(response)
    logger.info('returning response...')
    return row[0]


async def fetch_model_runs():
    """ Fetch recent model runs """
    session = app.db.database.get_read_session()
    model_runs = get_model_runs(session)

    result = CHainesModelRuns(model_runs=[])
    model_run_predictions = None
    prev_model_run_timestamp = None

    for model_run_timestamp, prediction_timestamp in model_runs:
        if model_run_timestamp != prev_model_run_timestamp:
            model_run_predictions = CHainesModelRunPredictions(
                model_run_timestamp=model_run_timestamp, prediction_timestamps=[])
            result.model_runs.append(model_run_predictions)
            prev_model_run_timestamp = model_run_timestamp
        model_run_predictions.prediction_timestamps.append(prediction_timestamp)

    return result


# async def fetch_model_run_predictions(model_run_timestamps):
#     session = app.db.database.get_read_session()
#     model_run_predictions = get_model_run_predictions(session, model_run_timestamps)
#     timestamps = []
#     for prediction in model_run_predictions:
#         timestamps.append(prediction[0])
#     return CHainesModelRunPredictions(prediction_timestamps=timestamps)
