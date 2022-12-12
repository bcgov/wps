from typing import Generator, Tuple
from contextlib import asynccontextmanager
from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session
from decouple import config


@asynccontextmanager
async def get_client() -> Generator[Tuple[AioBaseClient, str], None, None]:
    """ Return AioBaseClient client and bucket
    """
    server = config('OBJECT_STORE_SERVER')
    user_id = config('OBJECT_STORE_USER_ID')
    secret_key = config('OBJECT_STORE_SECRET')
    bucket = config('OBJECT_STORE_BUCKET')

    session = get_session()
    async with session.create_client('s3',
                                     endpoint_url=f'https://{server}',
                                     aws_secret_access_key=secret_key,
                                     aws_access_key_id=user_id) as client:
        try:
            yield client, bucket
        finally:
            del client
