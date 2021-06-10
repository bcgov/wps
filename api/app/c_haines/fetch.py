""" Fetch c-haines geojson
"""
from io import StringIO
from datetime import datetime, timedelta, timezone
from typing import Iterator, Tuple
from urllib.parse import urljoin, urlencode
import asyncio
import logging

from app import config
from app.utils.s3 import get_client
from app.c_haines.kml import (get_look_at,
                              get_kml_header, FOLDER_OPEN, FOLDER_CLOSE)
from app.c_haines.object_store import ObjectTypeEnum, generate_object_store_model_run_path
from app.schemas.weather_models import CHainesModelRuns, CHainesModelRunPredictions, WeatherPredictionModel
from app.weather_models import ModelEnum

logger = logging.getLogger(__name__)


async def fetch_model_run_kml_streamer(model: ModelEnum, model_run_timestamp: datetime) -> Iterator[str]:
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

    async with get_client() as (client, bucket):

        model_run_path = generate_object_store_model_run_path(model, model_run_timestamp, ObjectTypeEnum.KML)
        predictions = await client.list_objects_v2(Bucket=bucket, Prefix=model_run_path)
        if 'Contents' in predictions:
            for prediction in predictions['Contents']:
                object_name = prediction['Key']
                prediction_timestamp = object_name.split('/')[-1].split('.')[0]

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


def extract_model_run_prediction_from_path(prediction_path: str) -> Tuple[str, datetime, datetime]:
    """ Extract model abbreviation, model run timestamp and prediction timestamp from prediction path """
    name_split = prediction_path.strip('/').split('/')

    prediction_timestamp = datetime.fromisoformat(name_split[-1].rstrip('.json')+'+00:00')

    hour = int(name_split[-2])
    day = int(name_split[-3])
    month = int(name_split[-4])
    year = int(name_split[-5])
    model_run_timestamp = datetime(year=year, month=month, day=day, hour=hour, tzinfo=timezone.utc)

    model = name_split[-6]

    return model, model_run_timestamp, prediction_timestamp


def extract_model_run_timestamp_from_path(model_run_path: str) -> datetime:
    """ Take the model run path, and get back the model run datetime """
    name_split = model_run_path.strip('/').split('/')
    hour = int(name_split[-1])
    day = int(name_split[-2])
    month = int(name_split[-3])
    year = int(name_split[-4])
    return datetime(year=year, month=month, day=day, hour=hour, tzinfo=timezone.utc)


def extract_model_from_path(model_run_path: str) -> str:
    """ Take the model run path, and get back the model abbreviation """
    name_split = model_run_path.strip('/').split('/')
    return name_split[-5]


async def fetch_model_runs(model_run_timestamp: datetime):
    """ Fetch recent model runs."""
    # NOTE: This is a horribly inefficient way of listing model runs - we're making 6 calls just to
    # list model runs.
    result = CHainesModelRuns(model_runs=[])
    # Get an async S3 client.
    async with get_client() as (client, bucket):
        # Create tasks for listing all the model runs.
        tasks = []
        # Iterate for date of interest and day before. If you only look for today, you may have an empty
        # list until the latest model runs come in, so better to also list data from the day before.
        for date in [model_run_timestamp, model_run_timestamp-timedelta(days=1)]:
            # We're interested in all the model runs.
            for model in ['GDPS', 'RDPS', 'HRDPS']:
                # Construct a prefix to search for in S3 (basically path matching).
                prefix = 'c-haines-polygons/json/{model}/{year}/{month}/{day}/'.format(
                    model=model,
                    year=date.year, month=date.month, day=date.day)
                logger.info(prefix)
                # Create the task to go and fetch the listing from S3.
                tasks.append(asyncio.create_task(client.list_objects_v2(
                    Bucket=bucket,
                    Prefix=prefix)))

        # Run all the tasks at once. (Basically listing folder contents on S3.)
        model_run_prediction_results = await asyncio.gather(*tasks)
        # Iterate through results.
        for prediction_result in model_run_prediction_results:
            # S3 data comes back as a dictionary with "Contents"
            if 'Contents' in prediction_result:
                model_run_predictions = None
                prev_model_run_timestamp = None
                # Iterate through all the contents.
                for prediction in prediction_result['Contents']:
                    # The path is stored in the "Key" field. We infer the model, model run timestamp and
                    # prediction timestamp from the path.
                    model, model_run_timestamp, prediction_timestamp = extract_model_run_prediction_from_path(
                        prediction['Key'])
                    # Check for new model runs to add to our list.
                    if prev_model_run_timestamp != model_run_timestamp:
                        # New model run? Make it and add it to the list.
                        prev_model_run_timestamp = model_run_timestamp
                        model_run_predictions = CHainesModelRunPredictions(
                            model=WeatherPredictionModel(name=model, abbrev=model),
                            model_run_timestamp=model_run_timestamp,
                            prediction_timestamps=[prediction_timestamp, ])
                        result.model_runs.append(model_run_predictions)
                    else:
                        # Already have a model run, just at the prediction
                        model_run_predictions.prediction_timestamps.append(prediction_timestamp)

    # Sort evertyhign by model run timestamp.
    result.model_runs.sort(key=lambda model_run: model_run.model_run_timestamp, reverse=True)
    return result
