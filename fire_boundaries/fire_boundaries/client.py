import json
import requests
import jwt
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
import ee
from osgeo import gdal, ogr


def maskS2clouds(image):
    """ function from online example """
    qa = image.select('QA60') # Bits 10, 11: clouds, cirrus, resp.
    cloudBitMask = 1 << 10 # set both 0 == clear conditions
    cirrusBitMask = 1 << 11
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
    return image.updateMask(mask).divide(10000)

def apply_cloud_cover_threshold(start_date, n_days, cloud_threshold):
    data = ee.ImageCollection('COPERNICUS/S2_SR').filterDate(
        start_date,
        start_date.advance(n_days, 'day'))

    # apply cloud threshold and mask
    data = data.filter(ee.Filter.lt(
        'CLOUDY_PIXEL_PERCENTAGE',
        cloud_threshold)).map(maskS2clouds).mean()

    return data


def apply_classification_rule(data):
    # get DEM, LandCover, Sentinel-2 "L2A" (level two atmospherically-
    # corrected "bottom of atmosphere (BOA) reflectance) data """
    nasa_dem = ee.Image('NASA/NASADEM_HGT/001').select('elevation') 
    land_cover = ee.ImageCollection("ESA/WorldCover/v100").first()
    

    # apply classification rule
    rule = 'R > G && R > B && (LC != 80) && (LC != 50) && (LC != 70) && (DEM < 1500)'
    r = data.expression(rule, {'R': data.select('B12'),
                            'G': data.select('B11'),
                            'B': data.select('B9'),
                            'LC': land_cover.select('Map'),
                            'DEM': nasa_dem})
    
    return r


def write_geotiff(data, bbox, filename, params={}):
    # https://developers.google.com/earth-engine/apidocs/ee-image-getthumburl
    base_params = {'min': 0, 'max': 1, 'dimensions': 1024, 'region': bbox, 'format': 'GEO_TIFF'}

    url = data.getDownloadUrl(dict(base_params, **params))
    response = requests.get(url, timeout=60)

    print(response.status_code)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f'{filename} written')

    

def polygonize(geotiff_filename, geojson_filename):
    # TODO: we only need polygons for 1, not for 0!
    classification = gdal.Open(geotiff_filename, gdal.GA_ReadOnly)
    band = classification.GetRasterBand(1)

    # Create a GeoJSON layer.
    geojson_driver = ogr.GetDriverByName('GeoJSON')
    dst_ds = geojson_driver.CreateDataSource(geojson_filename)
    dst_layer = dst_ds.CreateLayer('fire')
    field_name = ogr.FieldDefn("fire", ogr.OFTInteger)
    field_name.SetWidth(24)
    dst_layer.CreateField(field_name)

    # Turn the rasters into polygons.
    gdal.Polygonize(band, None, dst_layer, 0, [], callback=None)

    # Ensure that all data in the target dataset is written to disk.
    dst_ds.FlushCache()
    # Explicitly clean up (is this needed?)
    del dst_ds, classification


def main():
    # construct jwt token
    token = jwt_token()

    # from google.oauth2.credentials import Credentials - only works with python 3.8.* or earlier.
    credentials = Credentials(token=token)
    ee.Initialize(credentials)

    # https://developers.google.com/earth-engine/guides/python_install#syntax

    data = apply_cloud_cover_threshold(
        ee.Date('2021-08-02T00:00', 'Etc/GMT-8'),
        14, # date range: [t1, t1 + N_DAYS]
        22.2 # cloud cover max %
        )

    fires =  apply_classification_rule(data)

    # ee.Geometry.BBox(west, south, east, north)
    bbox = ee.Geometry.BBox(-122, 51.3, -121.2, 51.7)

    write_geotiff(fires, bbox, 'binary_classification.tif')
    write_geotiff(data, bbox, 'rgb.tif', {'bands': ['B12', 'B11', 'B9']})
    polygonize('binary_classification.tif', 'binary_classification.json')


    

def jwt_token():
    """
    https://developers.google.com/identity/protocols/oauth2#serviceaccount
    """

    # https://developers.google.com/identity/protocols/oauth2/service-account
    # https://developers.google.com/earth-engine/reference/rest?hl=en_GB
    # https://developers.google.com/identity/protocols/oauth2/service-account#python_2

    # we take our service account details as provided by the google console:
    with open('/Users/sybrand/Workspace/fire-350717-ca75193a59cc.json') as f:
        service_account = json.load(f)

    iat = datetime.now()
    exp = iat + timedelta(seconds=3600)

    payload = {
        'iss': service_account['client_email'],
        'sub': service_account['client_email'],
        'aud': 'https://earthengine.googleapis.com/',
        'iat': int(iat.timestamp()),
        'exp': int(exp.timestamp())
    }

    additional_headers = {
        'kid': service_account['private_key_id']
    }

    # sign the payload using the private key
    token = jwt.encode(
        payload,
        service_account['private_key'],
        headers=additional_headers,
        algorithm='RS256')

    return token


if __name__ == '__main__':
    main()
    # once you have a polygon, you can calculate the area: https://pyproj4.github.io/pyproj/stable/examples.html#geodesic-area