""" Fetch c-haines geojson
"""
from io import StringIO
from datetime import datetime
from typing import Iterator
from urllib.parse import urljoin, urlencode
import logging

from app import config
from app.utils.minio import get_minio_client
from app.c_haines.severity_index import generate_kml_model_run_path
from app.c_haines.kml import (get_look_at, get_kml_header, FOLDER_OPEN, FOLDER_CLOSE)
import app.db.database
from app.schemas.weather_models import CHainesModelRuns, CHainesModelRunPredictions, WeatherPredictionModel
from app.weather_models import ModelEnum
from app.db.crud.c_haines import (get_model_run_predictions, get_prediction_geojson)

logger = logging.getLogger(__name__)


async def fetch_prediction_geojson(model: ModelEnum, model_run_timestamp: datetime,
                                   prediction_timestamp: datetime):
    """ Fetch prediction polygon geojson.
    """
    logger.info('model: %s; model_run: %s, prediction: %s', model, model_run_timestamp, prediction_timestamp)
    with app.db.database.get_read_session_scope() as session:
        response = get_prediction_geojson(session, model, model_run_timestamp, prediction_timestamp)
    return response


def fetch_model_run_kml_streamer(model: ModelEnum, model_run_timestamp: datetime) -> Iterator[str]:
    """ Yield model run XML (allows streaming response to start while kml is being
    constructed.)
    """

    uri = config.get('BASE_URI')

    yield get_kml_header()
    # Serve up the "look_at" which tells google earth when and where to take you.
    yield get_look_at(model, model_run_timestamp)
    # Serve up the name.
    yield '<name>{} {}</name>\n'.format(model, model_run_timestamp)
    yield '<Folder>'
    yield f'<name>{model}</name>\n'
    yield '<Folder>'
    yield f'<name>{model_run_timestamp} model run</name>\n'

    client, bucket = get_minio_client()

    model_run_path = generate_kml_model_run_path(model, model_run_timestamp)
    predictions = client.list_objects(bucket, prefix=model_run_path, recursive=True)
    for prediction in predictions:
        prediction_timestamp = prediction.object_name.split('/')[-1].split('.')[0]

        kml_params = {'model_run_timestamp': model_run_timestamp,
                      'prediction_timestamp': prediction_timestamp,
                      'response_format': 'KML'}
        # create url (remembering to escape & for xml)
        kml_url = urljoin(uri, f'/api/c-haines/{model}/prediction') + \
            '?' + urlencode(kml_params).replace('&', '&amp;')
        yield '<NetworkLink>\n'
        yield '<visibility>1</visibility>\n'
        yield f'<name>{prediction_timestamp}</name>\n'
        yield '<Link>\n'
        yield f'<href>{kml_url}</href>\n'
        yield '</Link>\n'
        yield '</NetworkLink>\n'

    yield '</Folder>'
    yield '</Folder>'
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
