""" Utils to help with minio
"""
from typing import Tuple
from minio import Minio
from app import config


def get_minio_client() -> Tuple[Minio, str]:
    """ Return minio client and bucket
    """
    server = config.get('OBJECT_STORE_SERVER')
    user_id = config.get('OBJECT_STORE_USER_ID')
    secret_key = config.get('OBJECT_STORE_SECRET')
    bucket = config.get('OBJECT_STORE_BUCKET')

    return Minio(server, user_id, secret_key, secure=True), bucket


def object_exists(client, bucket, target_path: str):
    """ Check if an object exists in the object store """
    # using list_objects, but could be using stat as well? don't know what's best.
    item_gen = client.list_objects(bucket, target_path)
    item = None
    try:
        item = next(item_gen)
    except StopIteration:
        # this means the item doesn't exist
        return False
    if item:
        return True
    return False
