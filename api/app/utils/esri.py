"""
Functions for talking to ESRI ARC servers.
"""
import urllib.parse
import urllib.request
import json
import logging
from app.geospatial import NAD83_BC_ALBERS

logger = logging.getLogger(__name__)


def fetch_object_list(url: str):
    """
    Fetch object list from a feature layer.

    url: layer url to fetch
    (e.g. https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/2)
    """
    logger.info('fetching object list for %s...', url)

    # 1=1 ???
    # There's no direct way of asking for all records, so the hack is to pass a condition that
    # is true for all records.
    params = {
        'where': '1=1',
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        'returnGeometry': 'false',
        'returnIdsOnly': 'true',
        'f': 'json'
    }

    encode_params = urllib.parse.urlencode(params).encode("utf-8")
    logger.info('%s/query?%s', url, encode_params.decode())
    with urllib.request.urlopen(f'{url}/query?', encode_params) as response:
        json_data = json.loads(response.read())
    return json_data['objectIds']


def fetch_object(object_id: int, url: str, out_sr: str = str(NAD83_BC_ALBERS), response_format: str = 'json') -> dict:
    """
    Fetch a single object from a feature layer. By default the output is
    json in BC Albers (EPSG:3005)
    We have to fetch objects one by one, because they
    can get pretty big. Big enough, that if you ask for more than one at a time, you're likely to
    encounter 500 errors.

    object_id: object id to fetch (e.g. 1)
    url: layer url to fetch
    (e.g. https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/2)
    out_sr: Spatial reference, e.g. '4326' (WGS84 EPSG:4326) or '3005' (BC Albers EPSG:3005)
    response_format: output format, e.g. 'geoJSON', 'json'

    For more information see:
    https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer-.htm
    """
    logger.info('fetching object %s', object_id)

    # Note: If you drop outSR, and set f to geoJSON, you get a GeoJSON geometry in WGS84.
    params = {
        'where': f'objectid={object_id}',
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        'outSR': out_sr,
        'outFields': '*',
        'returnGeometry': 'true',
        'returnIdsOnly': 'false',
        'f': response_format
    }

    encode_params = urllib.parse.urlencode(params).encode("utf-8")
    logger.info('%s/query?%s', object_id, encode_params.decode())
    with urllib.request.urlopen(f'{url}/query?', encode_params) as response:
        json_data = json.loads(response.read())
    return json_data
