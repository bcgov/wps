""" KML related code
"""
import io
from datetime import datetime, timedelta
from typing import Final, Iterator, IO
import json
import logging
from pyproj import Transformer, Proj
from shapely.ops import transform
from shapely.geometry import shape, Polygon
from wps_shared.utils.s3 import object_exists
from wps_shared.geospatial.geospatial import WGS84
from wps_shared.weather_models import ModelEnum
from wps_shared.utils.s3 import get_client
from app.c_haines import get_severity_string, SeverityEnum
from app.c_haines.object_store import (ObjectTypeEnum,
                                       generate_full_object_store_path)

logger = logging.getLogger(__name__)

FOLDER_OPEN: Final = '<Folder>'
FOLDER_CLOSE: Final = '</Folder>'
C_HAINES_KML_PERMISSIONS = 'public-read'


# Severity enum -> Text description mapping
severity_text_map = {
    SeverityEnum.LOW: '<4 Low',
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


async def save_as_kml_to_s3(json_filename: str,
                            source_projection,
                            prediction_model: ModelEnum,
                            model_run_timestamp: datetime,
                            prediction_timestamp: datetime):
    """ Given a geojson file, generate KML and store to S3 """
    target_kml_path = generate_full_object_store_path(
        prediction_model, model_run_timestamp, prediction_timestamp, ObjectTypeEnum.KML)
    async with get_client() as (client, bucket):
        # let's save some time, and check if the file doesn't already exists.
        # it's super important we do this, since there are many c-haines cronjobs running in dev, all
        # pointing to the same s3 bucket.
        if await object_exists(client, bucket, target_kml_path):
            logger.info('kml (%s) already exists - skipping', target_kml_path)
            return

        # generate the kml file
        with io.StringIO() as sio:
            severity_geojson_to_kml(json_filename, source_projection, sio,
                                    prediction_model, model_run_timestamp, prediction_timestamp)
            # smash it into binary
            sio.seek(0)
            bio = io.BytesIO(sio.read().encode('utf8'))
            # go back to start
            bio.seek(0)
            # save it to s3
            logger.info('uploading %s', target_kml_path)
            await client.put_object(Bucket=bucket,
                                    Key=target_kml_path,
                                    ACL=C_HAINES_KML_PERMISSIONS,  # We need these to be accessible to everyone
                                    Body=bio)


def open_placemark(model: ModelEnum, severity: SeverityEnum, timestamp: datetime) -> str:
    """ Open kml <Placemark> tag. """
    kml = []
    kml.append('<Placemark>')

    if model == ModelEnum.GDPS:
        end = timestamp + timedelta(hours=3)
    else:
        end = timestamp + timedelta(hours=1)
    kml.append('<TimeSpan>')
    kml.append(f"<begin>{timestamp.isoformat()}</begin>")
    kml.append(f"<end>{end.isoformat()}</end>")
    kml.append('</TimeSpan>')
    kml.append(f"<styleUrl>#{get_severity_style(severity)}</styleUrl>")
    kml.append(f"<name>{severity_text_map[severity]}</name>")
    kml.append('<MultiGeometry>')
    return "\n".join(kml)


def close_placemark() -> str:
    """ Close kml </Placemark> tag. """
    kml = []
    kml.append('</MultiGeometry>')
    kml.append('</Placemark>')
    return "\n".join(kml)


def add_style(kml, style_id, color):
    """ Add kml <Style> tag """
    kml.append(f'<Style id="{style_id}">')
    kml.append('<LineStyle>')
    kml.append('<width>1.5</width>')
    kml.append(f'<color>{color}</color>')
    kml.append('</LineStyle>')
    kml.append('<PolyStyle>')
    kml.append(f'<color>{color}</color>')
    kml.append('</PolyStyle>')
    kml.append('</Style>')


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
    # Center at an appropriate coordinate somewhere in the middle of B.C.
    kml.append('<longitude>-123</longitude>')
    kml.append('<latitude>54</latitude>')
    # https://developers.google.com/kml/documentation/kmlreference#range
    # Distance in meters from the point specified:
    kml.append('<range>3000000</range>')
    kml.append('</LookAt>')
    return '\n'.join(kml)


def get_kml_header() -> str:
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


def format_coordinates(coordinates: Polygon) -> str:
    """ Format geojson coordinates for kml """
    result = []
    result.append('<coordinates>')
    # all coordinates have a space at the end.
    x_array = coordinates.exterior.coords.xy[0]
    y_array = coordinates.exterior.coords.xy[1]
    for x_coordinate, y_coordinate in zip(x_array[:-1], y_array[:-1]):
        result.append(f'{x_coordinate},{y_coordinate} ')
    # except for the very last one.
    x_coordinate = x_array[-1]
    y_coordinate = y_array[-1]
    result.append(f'{x_coordinate},{y_coordinate}')
    result.append('</coordinates>')
    return ''.join(result)


def feature_2_kml_polygon(feature: dict, project: Transformer) -> str:
    """ Given a geojson file, yield kml polygons """
    polygon = []
    polygon.append('<Polygon>')
    polygon.append('<outerBoundaryIs>')
    polygon.append('<LinearRing>')
    source_geometry = shape(feature['geometry'])
    if project:
        geometry = transform(project.transform, source_geometry)
    else:
        geometry = source_geometry
    polygon.append(format_coordinates(geometry))
    polygon.append('</LinearRing>')
    polygon.append('</outerBoundaryIs>')
    polygon.append('</Polygon>')
    return '\n'.join(polygon)


class KMLGeojsonPolygonIterator:
    """ Generator that produces a kml polygon for every geojson feature. This generator assumes
    GeoJSON as produced by the process that generates GeoJSON by severity level. """

    def __init__(self, file_pointer: IO, projection: str):
        geojson = json.load(file_pointer)
        # We need to sort the geojson by severity
        geojson['features'].sort(key=lambda feature: feature['properties']['severity'])
        self.features = iter(geojson['features'])
        # Source coordinate system, must match source data.
        proj_from = Proj(projparams=projection)
        # Destination coordinate systems (WGS84, geographic coordinates)
        proj_to = Proj(WGS84)
        self.project = Transformer.from_proj(proj_from, proj_to, always_xy=True)

    def __iter__(self):
        return self

    def __next__(self):
        feature = next(self.features)
        severity = get_severity_string(feature['properties']['severity'])
        return feature_2_kml_polygon(feature, self.project), severity


def generate_kml_prediction(result: Iterator[list], model: ModelEnum, model_run_timestamp: datetime,
                            prediction_timestamp: datetime) -> Iterator[str]:
    """
    Create KML prediction given some result iterator
    """
    yield get_kml_header()
    kml = []
    kml.append(f'<name>{model.value} {model_run_timestamp} {prediction_timestamp}</name>')
    kml.append(f'{FOLDER_OPEN}')
    kml.append(f'<name>{model.value} {model_run_timestamp} {prediction_timestamp}</name>')
    yield "\n".join(kml)
    kml = []
    prev_severity = None
    for poly, severity in result:
        if severity != prev_severity:
            if prev_severity is not None:
                kml.append(close_placemark())
            prev_severity = severity
            kml.append(open_placemark(model, SeverityEnum(severity), prediction_timestamp))
        kml.append(poly)

        yield "\n".join(kml)
        kml = []
    if prev_severity is not None:
        kml.append(close_placemark())
    kml.append(f'{FOLDER_CLOSE}')
    kml.append('</Document>')
    kml.append('</kml>')
    yield "\n".join(kml)


def severity_geojson_to_kml(geojson_filename: str,
                            geojson_projection: str,
                            sio: io.StringIO,
                            model: ModelEnum,
                            model_run_timestamp: datetime,
                            prediction_timestamp: datetime):
    """ Given a severity geojson file, create a KML file.
    """
    with open(geojson_filename, encoding="utf-8") as geojson_file_pointer:
        kml_file_result = KMLGeojsonPolygonIterator(geojson_file_pointer, geojson_projection)
        for part in generate_kml_prediction(kml_file_result,
                                            model,
                                            model_run_timestamp,
                                            prediction_timestamp):
            sio.write(part)
