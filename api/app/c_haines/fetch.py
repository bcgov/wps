""" Fetch c-haines geojson
"""
from datetime import datetime
import logging
import app.db.database
from app.schemas.weather_models import CHainesModelRuns, CHainesModelRunPredictions, WeatherPredictionModel
from app.weather_models import ModelEnum
from app.db.crud.c_haines import get_model_run_predictions, get_prediction_geojson


logger = logging.getLogger(__name__)


async def fetch_prediction(model: ModelEnum, model_run_timestamp: datetime, prediction_timestamp: datetime):
    """ Fetch prediction polygon geojson.
    """
    logger.info('model: %s; model_run: %s, prediction: %s', model, model_run_timestamp, prediction_timestamp)
    session = app.db.database.get_read_session()
    return get_prediction_geojson(session, model, model_run_timestamp, prediction_timestamp)


async def fetch_model_runs(model_run_timestamp: datetime):
    """ Fetch recent model runs """
    session = app.db.database.get_read_session()
    model_runs = get_model_run_predictions(session, model_run_timestamp)

    result = CHainesModelRuns(model_runs=[])
    prev_model_run_id = None

    for model_run_id, tmp_model_run_timestamp, name, abbreviation, prediction_timestamp in model_runs:
        if prev_model_run_id != model_run_id:
            model_run_predictions = CHainesModelRunPredictions(
                model=WeatherPredictionModel(name=name, abbrev=abbreviation),
                model_run_timestamp=tmp_model_run_timestamp,
                prediction_timestamps=[])
            result.model_runs.append(model_run_predictions)
            prev_model_run_id = model_run_id
        model_run_predictions.prediction_timestamps.append(prediction_timestamp)

    return result
