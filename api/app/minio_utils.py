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
