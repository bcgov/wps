""" Fetch c-haines geojson
"""
from io import StringIO
from urllib.parse import urljoin
from datetime import datetime, timedelta
import logging
from app import config
import app.db.database
from app.db.models.c_haines import SeverityEnum
from app.schemas.weather_models import CHainesModelRuns, CHainesModelRunPredictions, WeatherPredictionModel
from app.weather_models import ModelEnum
from app.db.crud.c_haines import (get_model_run_predictions, get_most_recent_model_run,
                                  get_prediction_geojson, get_prediction_kml, get_model_run_kml)

logger = logging.getLogger(__name__)


# Severity enum -> Text description mapping
severity_text_map = {
    SeverityEnum.MODERATE: '4 - 8 Moderate',
    SeverityEnum.HIGH: '8 - 11 High',
    SeverityEnum.EXTREME: '11+ Extreme'
}

# Severity enum -> KML style mapping
severity_style_map = {
    SeverityEnum.LOW: 'low',
    SeverityEnum.MODERATE: 'moderate',
    SeverityEnum.HIGH: 'high',
    SeverityEnum.EXTREME: 'extreme'
}


def get_severity_style(c_haines_index: SeverityEnum) -> str:
    """ Based on the index range, return a style string """
    return severity_style_map[c_haines_index]


def open_placemark(model: ModelEnum, severity: SeverityEnum, timestamp: datetime):
    """ Open kml <Placemark> tag. """
    kml = []
    kml.append('<Placemark>')

    if model == ModelEnum.GDPS:
        end = timestamp + timedelta(hours=3)
    else:
        end = timestamp + timedelta(hours=1)
    kml.append('<TimeSpan>')
    kml.append('<begin>{}</begin>'.format(timestamp.isoformat()))
    kml.append('<end>{}</end>'.format(end.isoformat()))
    kml.append('</TimeSpan>')
    kml.append('<styleUrl>#{}</styleUrl>'.format(get_severity_style(severity)))
    kml.append('<name>{}</name>'.format(severity_text_map[severity]))
    kml.append('<MultiGeometry>')
    return "\n".join(kml)


def close_placemark():
    """ Close kml </Placemark> tag. """
    kml = []
    kml.append('</MultiGeometry>')
    kml.append('</Placemark>')
    return "\n".join(kml)


def add_style(kml, style_id, color):
    """ Add kml <Style> tag """
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
    with app.db.database.get_read_session_scope() as session:
        response = get_prediction_geojson(session, model, model_run_timestamp, prediction_timestamp)
    return response


def get_look_at(model: ModelEnum, model_run_timestamp: datetime):
    """ Return <LookAt> tag to set default position and timespan.
    If this isn't done, then all the predictions will show as a big overlayed mess. """
    if model == ModelEnum.GDPS:
        end = model_run_timestamp + timedelta(hours=3)
    else:
        end = model_run_timestamp + timedelta(hours=1)
    kml = []
    kml.append('<LookAt>')
    kml.append('<gx:TimeSpan>')
    kml.append(f'<begin>{model_run_timestamp.isoformat()}</begin>')
    kml.append(f'<end>{end.isoformat()}</end>')
    kml.append('</gx:TimeSpan>')
    kml.append('<longitude>-123</longitude>')
    kml.append('<latitude>54</latitude>')
    kml.append('<range>3000000</range>')
    kml.append('</LookAt>')
    return '\n'.join(kml)


def fetch_model_run_kml_streamer(model: ModelEnum, model_run_timestamp: datetime):
    """ Yield model run XML (allows streaming response to start while kml is being
    constructed.)
    """
    logger.info('model: %s; model_run: %s', model, model_run_timestamp)

    with app.db.database.get_read_session_scope() as session:

        if model_run_timestamp is None:
            model_run = get_most_recent_model_run(session, model)
            model_run_timestamp = model_run.model_run_timestamp

        result = get_model_run_kml(session, model, model_run_timestamp)

        yield get_kml_header()
        yield get_look_at(model, model_run_timestamp)
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
                yield open_placemark(model, SeverityEnum(severity), prediction_timestamp)
            yield poly

        if not prev_prediction_timestamp is None:
            if not prev_severity is None:
                yield close_placemark()
            yield '</Folder>\n'
        yield '</Document>\n'
        yield '</kml>\n'
        logger.info('kml complete')


def get_kml_header():
    """ Return the kml header (xml header, <xml> tag, <Document> tag and styles.)
    """
    kml = []
    kml.append('<?xml version="1.0" encoding="UTF-8"?>')
    kml.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
    kml.append('<Document>')
    # color format is aabbggrr
    add_style(kml, get_severity_style(SeverityEnum.MODERATE), '9900ffff')
    add_style(kml, get_severity_style(SeverityEnum.HIGH), '9900a5ff')
    add_style(kml, get_severity_style(SeverityEnum.EXTREME), '990000ff')
    return "\n".join(kml)


def fetch_network_link_kml():
    """ Fetch the kml for the network link """
    uri = config.get('BASE_URI')
    writer = StringIO()
    writer.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    writer.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
    writer.write('<Folder>\n')
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
    writer.write('</Folder>\n')
    writer.write('</kml>')
    return writer.getvalue()


def fetch_prediction_kml_streamer(model: ModelEnum, model_run_timestamp: datetime,
                                  prediction_timestamp: datetime):
    """ Fetch prediction polygon geojson.
    """
    logger.info('model: %s; model_run: %s, prediction: %s', model, model_run_timestamp, prediction_timestamp)
    with app.db.database.get_read_session_scope() as session:
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
                kml.append(open_placemark(model, SeverityEnum(severity), prediction_timestamp))
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
