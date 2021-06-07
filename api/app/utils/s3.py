""" Utils to help with minio
"""
from typing import Tuple
from contextlib import asynccontextmanager
from minio import Minio
from aiobotocore.client import AioBaseClient
import aiobotocore
from app import config


def get_minio_client() -> Tuple[Minio, str]:
    """ Return minio client and bucket
    TODO: Deprecated! Please stop using this!
    """
    server = config.get('OBJECT_STORE_SERVER')
    user_id = config.get('OBJECT_STORE_USER_ID')
    secret_key = config.get('OBJECT_STORE_SECRET')
    bucket = config.get('OBJECT_STORE_BUCKET')

    return Minio(server, user_id, secret_key, secure=True), bucket


@asynccontextmanager
async def get_client() -> Tuple[AioBaseClient, str]:
    """ Return minio client and bucket
    """
    server = config.get('OBJECT_STORE_SERVER')
    user_id = config.get('OBJECT_STORE_USER_ID')
    secret_key = config.get('OBJECT_STORE_SECRET')
    bucket = config.get('OBJECT_STORE_BUCKET')

    session = aiobotocore.get_session()
    async with session.create_client('s3',
                                     endpoint_url=f'https://{server}',
                                     aws_secret_access_key=secret_key,
                                     aws_access_key_id=user_id) as client:
        try:
            yield client, bucket
        finally:
            await client.close()


def object_exists(client, bucket, target_path: str):
    """ Check if and object exists in the object store
    TODO: Change this to use async
    """
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
