""" Fetch c-haines geojson
"""
from datetime import datetime
import logging
import app.db.database
from app.schemas.weather_models import CHainesModelRuns, CHainesModelRunPredictions, WeatherPredictionModel
from app.weather_models import ModelEnum
from app.db.crud.c_haines import get_model_run_predictions


logger = logging.getLogger(__name__)


async def fetch(model: ModelEnum, model_run_timestamp: datetime, prediction_timestamp: datetime):
    """ Fetch polygon geojson
    """
    logger.info('model: %s; model_run: %s, prediction: %s', model, model_run_timestamp, prediction_timestamp)
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
        select geom, severity from c_haines_polygons
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
        order by severity asc
    ) as t(geom, severity)""".format(
        prediction_timestamp=prediction_timestamp.isoformat(),
        model_run_timestamp=model_run_timestamp.isoformat(),
        model=model)
    logger.info(query)
    logger.info('fetching geojson from db...')
    # pylint: disable=no-member
    response = session.execute(query)
    row = next(response)
    return row[0]


async def fetch_model_runs(model_run_timestamp: datetime):
    """ Fetch recent model runs """
    session = app.db.database.get_read_session()
    model_runs = get_model_run_predictions(session, model_run_timestamp)

    result = CHainesModelRuns(model_runs=[])
    prev_model_run_id = None

    for model_run_id, model_run_timestamp, name, abbreviation, prediction_timestamp in model_runs:
        if prev_model_run_id != model_run_id:
            model_run_predictions = CHainesModelRunPredictions(
                model=WeatherPredictionModel(name=name, abbrev=abbreviation),
                model_run_timestamp=model_run_timestamp,
                prediction_timestamps=[])
            result.model_runs.append(model_run_predictions)
            prev_model_run_id = model_run_id
        model_run_predictions.prediction_timestamps.append(prediction_timestamp)

    return result


# async def fetch_model_run_predictions(model_run_timestamps):
#     session = app.db.database.get_read_session()
#     model_run_predictions = get_model_run_predictions(session, model_run_timestamps)
#     timestamps = []
#     for prediction in model_run_predictions:
#         timestamps.append(prediction[0])
#     return CHainesModelRunPredictions(prediction_timestamps=timestamps)
