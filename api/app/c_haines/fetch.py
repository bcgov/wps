""" Fetch c-haines geojson
"""
from io import StringIO
from datetime import datetime
from typing import Iterator
from urllib.parse import urljoin
import logging
from app import config
from app.c_haines.kml import (get_look_at, kml_prediction, _yield_folder_parts,
                              get_kml_header, FOLDER_OPEN, FOLDER_CLOSE)
import app.db.database
from app.schemas.weather_models import CHainesModelRuns, CHainesModelRunPredictions, WeatherPredictionModel
from app.weather_models import ModelEnum
from app.db.crud.c_haines import (get_model_run_predictions, get_most_recent_model_run,
                                  get_prediction_geojson, get_prediction_kml, get_model_run_kml)

logger = logging.getLogger(__name__)


async def fetch_prediction_geojson(model: ModelEnum, model_run_timestamp: datetime,
                                   prediction_timestamp: datetime):
    """ Fetch prediction polygon geojson.
    """
    logger.info('model: %s; model_run: %s, prediction: %s', model, model_run_timestamp, prediction_timestamp)
    with app.db.database.get_read_session_scope() as session:
        response = get_prediction_geojson(session, model, model_run_timestamp, prediction_timestamp)
    return response


def fetch_model_run_kml_streamer(
        model: ModelEnum, model_run_timestamp: datetime) -> Iterator[str]:
    """ Yield model run XML (allows streaming response to start while kml is being
    constructed.)
    """
    logger.info('model: %s; model_run: %s', model, model_run_timestamp)

    with app.db.database.get_read_session_scope() as session:

        if model_run_timestamp is None:
            model_run = get_most_recent_model_run(session, model)
            model_run_timestamp = model_run.model_run_timestamp

        # Fetch the KML results from the database.
        result = get_model_run_kml(session, model, model_run_timestamp)

        # Serve up the kml header.
        yield get_kml_header()
        # Serve up the "look_at" which tells google earth when and where to take you.
        yield get_look_at(model, model_run_timestamp)
        # Serve up the name.
        yield '<name>{} {}</name>\n'.format(model, model_run_timestamp)

        # Iterate through all the different folders and placemarks.
        for item in _yield_folder_parts(result, model, model_run_timestamp):
            yield item

        # Close the KML document.
        yield '</Document>\n'
        yield '</kml>\n'
        logger.info('kml complete')


def fetch_network_link_kml() -> str:
    """ Fetch the kml for the network link """
    uri = config.get('BASE_URI')
    writer = StringIO()
    writer.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    writer.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
    writer.write(f'{FOLDER_OPEN}\n')
    writer.write('<name>C-Haines</name>\n')
    visibility = 1
    for model in ['HRDPS', 'RDPS', 'GDPS']:
        kml_url = urljoin(uri, f'/api/c-haines/{model}/predictions?response_format=KML')
        writer.write('<NetworkLink>\n')
        # we make the 1st one visible.
        writer.write(f'<visibility>{visibility}</visibility>\n')
        writer.write(f'<name>{model}</name>\n')
        writer.write('<Link>\n')
        writer.write(f'<href>{kml_url}</href>\n')
        writer.write('</Link>\n')
        writer.write('</NetworkLink>\n')
        visibility = 0
    writer.write(f'{FOLDER_CLOSE}\n')
    writer.write('</kml>')
    return writer.getvalue()


def fetch_prediction_kml_streamer(model: ModelEnum, model_run_timestamp: datetime,
                                  prediction_timestamp: datetime):
    """ Fetch prediction polygon geojson.
    """
    logger.info('model: %s; model_run: %s, prediction: %s', model, model_run_timestamp, prediction_timestamp)
    with app.db.database.get_read_session_scope() as session:
        result = get_prediction_kml(session, model, model_run_timestamp, prediction_timestamp)
        for part in kml_prediction(result, model, model_run_timestamp, prediction_timestamp):
            yield part


async def fetch_model_runs(model_run_timestamp: datetime):
    """ Fetch recent model runs """
    with app.db.database.get_read_session_scope() as session:
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
