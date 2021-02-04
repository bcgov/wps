""" Fetch c-haines geojson
"""
from datetime import datetime
import logging
import app.db.database
from app.schemas.weather_models import CHainesModelRuns, CHainesModelRunPredictions, WeatherPredictionModel
from app.weather_models import ModelEnum
from app.db.crud.c_haines import (get_model_run_predictions,
                                  get_prediction_geojson, get_prediction_kml, get_model_run_kml)


logger = logging.getLogger(__name__)


def get_severity_text(severity):
    if severity == 1:
        return '4 - 8 Moderate'
    if severity == 2:
        return '8 - 11 High'
    if severity == 3:
        return '11+ Extreme'
    raise Exception('Unexpected severity')


def get_severity_style(severity):
    if severity == 1:
        return 'moderate'
    if severity == 2:
        return 'high'
    if severity == 3:
        return 'extreme'


def open_placemark(severity, timestamp: datetime):
    kml = []
    kml.append('<Placemark>')
    kml.append('<TimeStamp>')
    kml.append('<when>{}</when>'.format(timestamp.isoformat()))
    kml.append('</TimeStamp>')
    kml.append('<styleUrl>#{}</styleUrl>'.format(get_severity_style(severity)))
    kml.append('<name>{}</name>'.format(get_severity_text(severity)))
    kml.append('<MultiGeometry>')
    return "\n".join(kml)


def close_placemark():
    kml = []
    kml.append('</MultiGeometry>')
    kml.append('</Placemark>')
    return "\n".join(kml)


def add_style(kml, style_id, color):
    kml.append('<Style id="{}">'.format(style_id))
    kml.append('<LineStyle>')
    kml.append('<width>1.5</width>')
    kml.append('<color>{}</color>'.format(color))
    kml.append('</LineStyle>')
    kml.append('<PolyStyle>')
    kml.append('<color>{}</color>'.format(color))
    kml.append('</PolyStyle>')
    kml.append('</Style>')


async def fetch_prediction_geojson(model: ModelEnum, model_run_timestamp: datetime,
                                   prediction_timestamp: datetime):
    """ Fetch prediction polygon geojson.
    """
    logger.info('model: %s; model_run: %s, prediction: %s', model, model_run_timestamp, prediction_timestamp)
    session = app.db.database.get_read_session()
    return get_prediction_geojson(session, model, model_run_timestamp, prediction_timestamp)


def fetch_model_run_kml_streamer(model: ModelEnum, model_run_timestamp: datetime):
    logger.info('model: %s; model_run: %s', model, model_run_timestamp)

    session = app.db.database.get_read_session()
    result = get_model_run_kml(session, model, model_run_timestamp)

    yield get_kml_header()
    yield '<name>{} {}</name>\n'.format(model, model_run_timestamp)

    prev_prediction_timestamp = None
    prev_severity = None
    for poly, severity, prediction_timestamp in result:
        if prediction_timestamp != prev_prediction_timestamp:
            if not prev_severity is None:
                yield close_placemark()
            prev_severity = None
            if not prev_prediction_timestamp is None:
                yield '</Folder>\n'
            prev_prediction_timestamp = prediction_timestamp
            yield '<Folder>\n'
            yield '<name>{} {} {}</name>\n'.format(model, model_run_timestamp, prediction_timestamp)
        if severity != prev_severity:
            if not prev_severity is None:
                yield close_placemark()
            prev_severity = severity
            yield open_placemark(severity, prediction_timestamp)
        yield poly

    if not prev_prediction_timestamp is None:
        if not prev_severity is None:
            yield close_placemark()
        yield '</Folder>\n'
    yield '</Document>\n'
    yield '</kml>\n'


def get_kml_header():
    kml = []
    kml.append('<?xml version="1.0" encoding="UTF-8"?>')
    kml.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
    kml.append('<Document>')
    # color format is aabbggrr
    add_style(kml, get_severity_style(1), '9900ffff')
    add_style(kml, get_severity_style(2), '9900a5ff')
    add_style(kml, get_severity_style(3), '990000ff')
    return "\n".join(kml)


def fetch_prediction_kml_streamer(model: ModelEnum, model_run_timestamp: datetime,
                                  prediction_timestamp: datetime):
    """ Fetch prediction polygon geojson.
    """
    logger.info('model: %s; model_run: %s, prediction: %s', model, model_run_timestamp, prediction_timestamp)
    session = app.db.database.get_read_session()
    result = get_prediction_kml(session, model, model_run_timestamp, prediction_timestamp)

    yield get_kml_header()
    kml = []
    kml.append('<name>{} {} {}</name>'.format(model, model_run_timestamp, prediction_timestamp))
    kml.append('<Folder>')
    kml.append('<name>{} {} {}</name>'.format(model, model_run_timestamp, prediction_timestamp))
    yield "\n".join(kml)
    kml = []
    prev_severity = None
    for poly, severity in result:
        if severity != prev_severity:
            if not prev_severity is None:
                kml.append(close_placemark())
            prev_severity = severity
            kml.append(open_placemark(severity, prediction_timestamp))
        kml.append(poly)

        yield "\n".join(kml)
        kml = []
    if not prev_severity is None:
        kml.append(close_placemark())
    kml.append('</Folder>')
    kml.append('</Document>')
    kml.append('</kml>')
    yield "\n".join(kml)


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
