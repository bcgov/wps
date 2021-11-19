# Taken from:
# https://support.esri.com/en/technical-article/000019645
# Minus the token stuff

# referenced https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer-.htm


import urllib.parse
import urllib.request
import os
import json
# import arcpy

# arcpy.env.overwriteOutput = True

# Specify REST URL for service JSON to be returned
url = "https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/8/query?"


def fetch_object_list():

    params = {
        #     'where': '1=1',
        'where': 'objectid<800',
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        'outSR': '102100',
        'outFields': '*',
        'returnGeometry': 'false',
        'returnIdsOnly': 'true',
        #           'relationParam': '',
        #           'geometryPrecision': '',
        #           'returnIdsOnly': 'false',
        #           'returnCountOnly': 'false',
        #           'orderByFields': '',
        #           'groupByFieldsForStatistics': '',
        #           'returnZ': 'false',
        #           'returnM': 'false',
        #           'returnDistinctValues': 'false',
        #             'f': 'json'
        'f': 'json'
    }

    encode_params = urllib.parse.urlencode(params).encode("utf-8")

    print('url open...')
    response = urllib.request.urlopen(url, encode_params)
    print('read...')
    json_data = json.loads(response.read())
    return json_data['objectIds']


def fetch_object(object_id):

    params = {
        'where': 'objectid=' + str(object_id),
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        'outSR': '102100',
        'outFields': '*',
        'returnGeometry': 'true',
        'returnIdsOnly': 'false',
        'f': 'geojson'
    }

    encode_params = urllib.parse.urlencode(params).encode("utf-8")

    print('url open...')
    response = urllib.request.urlopen(url, encode_params)
    print('read...')
    json_data = json.loads(response.read())
    return json_data


# print('write json...')
# with open("mapservice.json", "wb") as ms_json:
#     ms_json.write(json)

# # ws = os.getcwd() + os.sep
# # arcpy.JSONToFeatures_conversion("mapservice.json", ws + "mapservice.shp", )

# print('done.')
if __name__ == "__main__":
    ids = fetch_object_list()
    for id in ids:
        print(f'process {id}...')
        obj = fetch_object(id)
        filename = f'obj_{id}.json'
        with open(filename, "w") as f:
            json.dump(obj, f)
        print(f'dump to database {filename}')
        # TODO: there's some issue with 453 (that's the Fraser Fire Zone)
        os.system(
            f'ogr2ogr -f "PostgreSQL" PG:"dbname=wps host=localhost user=wps password=wps" "{filename}" -nln fire_zones')

        # ogr2ogr -f "PostgreSQL" PG:"dbname=wps host=localhost user=wps password=wps" "obj_453.json" -nln fire_zones
