""" Utils to help with s3
"""
from typing import Generator, Tuple
from contextlib import asynccontextmanager
from aiobotocore.client import AioBaseClient
from aiobotocore import get_session
from app import config


@asynccontextmanager
async def get_client() -> Generator[Tuple[AioBaseClient, str], None, None]:
    """ Return AioBaseClient client and bucket
    """
    server = config.get('OBJECT_STORE_SERVER')
    user_id = config.get('OBJECT_STORE_USER_ID')
    secret_key = config.get('OBJECT_STORE_SECRET')
    bucket = config.get('OBJECT_STORE_BUCKET')

    session = get_session()
    async with session.create_client('s3',
                                     endpoint_url=f'https://{server}',
                                     aws_secret_access_key=secret_key,
                                     aws_access_key_id=user_id) as client:
        try:
            yield client, bucket
        finally:
            await client.close()


async def object_exists(client: AioBaseClient, bucket: str, target_path: str):
    """ Check if and object exists in the object store
    """
    # using list_objects, but could be using stat as well? don't know what's best.
    result = await client.list_objects_v2(Bucket=bucket,
                                          Prefix=target_path)
    contents = result.get('Contents', None)
    if contents:
        for content in contents:
            key = content.get('Key')
            if key == target_path:
                return True
    return False


async def object_exists_v2(target_path: str):
    """ Check if and object exists in the object store
    """
    async with get_client() as (client, bucket):
        return await object_exists(client, bucket, target_path)
