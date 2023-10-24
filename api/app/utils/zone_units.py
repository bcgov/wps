
import json
from app import config
from botocore.session import get_session


def get_zone_units_geojson():
    """
    Fetches a dem from S3 storage, opens it with gdal and assigns it to a global variable
    for use in other functions. This is a little clunky, but we only want to grab the dem from
    object storage once because it is a slow process.
    """

    server = config.get('OBJECT_STORE_SERVER')
    user_id = config.get('OBJECT_STORE_USER_ID')
    secret_key = config.get('OBJECT_STORE_SECRET')
    bucket = config.get('OBJECT_STORE_BUCKET')
    session = get_session()
    # Create an S3 client
    client = session.create_client('s3',
                                   endpoint_url=f'https://{server}',
                                   aws_secret_access_key=secret_key,
                                   aws_access_key_id=user_id)

    fire_zone_units = client.get_object(Bucket=bucket, Key='zone-units/fire_zone_units.geojson')
    data = json.loads(fire_zone_units['Body'].read().decode('utf-8'))
    return data
