import urllib.parse
import urllib.request
import json


def fetch_object_list(url: str):
    """
    Fetch object list from a feature layer.

    url: layer url to fetch (e.g. https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/2)
    """
    print(f'fetching object list for {url}...')

    params = {
        'where': '1=1',
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        # 'outSR': '102100',
        # 'outFields': '*',
        'returnGeometry': 'false',
        'returnIdsOnly': 'true',
        'f': 'json'
    }

    encode_params = urllib.parse.urlencode(params).encode("utf-8")
    print(f'{url}/query?{encode_params.decode()}')
    with urllib.request.urlopen(f'{url}/query?', encode_params) as response:
        json_data = json.loads(response.read())
    return json_data['objectIds']


def fetch_object(object_id: int, url: str, outSR: str = '3005', f: str = 'geoJSON') -> dict:
    """
    Fetch a single object from a feature layer. By default the output is
    json in BC Albers (EPSG:3005)
    We have to fetch objects one by one, because they
    can get pretty big. Big enough, that if you ask for more than one at a time, you're likely to
    encounter 500 errors.

    object_id: object id to fetch (e.g. 1)
    url: layer url to fetch (e.g. https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/2)
    outSR: Spatial reference, e.g. '4326' (WGS84 EPSG:4326) or '3005' (BC Albers EPSG:3005)
    f: output format, e.g. 'geoJSON', 'json'

    For more information see:
    https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer-.htm
    """
    print(f'fetching object {object_id}')

    # Note: If you drop outSR, and set f to geoJSON, you get a GeoJSON geometry in WGS84.
    params = {
        'where': f'objectid={object_id}',
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        'outSR': outSR,
        'outFields': '*',
        'returnGeometry': 'true',
        'returnIdsOnly': 'false',
        'f': f
    }

    encode_params = urllib.parse.urlencode(params).encode("utf-8")
    print(f'{url}/query?{encode_params.decode()}')
    with urllib.request.urlopen(f'{url}/query?', encode_params) as response:
        json_data = json.loads(response.read())
    return json_data
