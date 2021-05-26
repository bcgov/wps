""" Script to migrate c-haines polygons from postgres to object store """
import argparse
import io
from minio import Minio
from app.db.crud.c_haines import get_all_kml, get_all_geojson

root_bucket = "gpdqha"
c_haines_polygons_folder = "c-haines-polygons"
kml_folder = "kml"
geo_json_folder = "geo-json"
placeholder_file = ".placeholder.txt"
placeholder_content = io.BytesIO(b"")


def migrate_kml(client):
    """Query db for all kml polygons and store in object store"""
    with app.db.database.get_read_session_scope() as session:
        result = get_all_kml(session)
        for row in result:
            client.put_object(root_bucket, c_haines_polygons_folder + '/' + kml_folder + '/' +
                              row['c_haines_prediction_id'], io.BytesIO(row))


def migrate_geo_json(client):
    """Query db for all geojson and store in object store"""
    with app.db.database.get_read_session_scope() as session:
        result = get_all_geojson(session)
        for row in result:
            client.put_object(root_bucket, c_haines_polygons_folder + '/' + geo_json_folder + '/' +
                              row['c_haines_prediction_id'], io.BytesIO(row))


def main():
    """ Script to migrate c-haines polygons from postgres to object store.
        Assumes you're logged into OpenShift.
    """

    parser = argparse.ArgumentParser(
        description='Migrates c-haines polygons to object store')
    parser.add_argument('-o', '--object-store', required=True,
                        help='Object store server to push to')
    parser.add_argument('-u', '--user-id', required=True,
                        help='User id to authenticate with object store')
    parser.add_argument('-s', '--secret-key', required=True,
                        help='Secret key to authenticate with object store')
    parser.add_argument('-b', '--bucket', required=True,
                        help='Root bucket to add data to')

    args = parser.parse_args()
    object_store = args.object_store
    user_id = args.user_id
    secret_key = args.secret_key
    bucket = args.bucket

    client = Minio(object_store, user_id, secret_key, secure=True)
    if not client.bucket_exists(bucket):
        print("Bucket specified does not exist")
        exit(1)

    # Create c-haines folder
    client.put_object(root_bucket, c_haines_polygons_folder + '/' +
                      placeholder_file, placeholder_content, 0,)
    # Create kml folder
    client.put_object(root_bucket, c_haines_polygons_folder + '/' + kml_folder + '/' +
                      placeholder_file, placeholder_content, 0,)

    # Create geo-json folder
    client.put_object(root_bucket, c_haines_polygons_folder + '/' + geo_json_folder + '/' +
                      placeholder_file, placeholder_content, 0,)

    migrate_kml(client)
    migrate_geo_json(client)


if __name__ == '__main__':
    main()
