""" Script to migrate c-haines polygons from postgres to object store """
import argparse
import io
from minio import Minio

root_bucket = "gpdqha"
c_haines_polygons_bucket = "c-haines-polygons"
kml_bucket = "kml"
geo_json_bucket = "geo-json"


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
    client.put_object(root_bucket, c_haines_polygons_bucket + '/' +
                      '.placeholder.txt', io.BytesIO(b"test"), 4,)
    # Create kml folder
    client.put_object(root_bucket, c_haines_polygons_bucket + '/' + kml_bucket + '/' +
                      '.placeholder.txt', io.BytesIO(b"test"), 4,)

    # Create geo-json folder
    client.put_object(root_bucket, c_haines_polygons_bucket + '/' + geo_json_bucket + '/' +
                      '.placeholder.txt', io.BytesIO(b"test"), 4,)


if __name__ == '__main__':
    main()
