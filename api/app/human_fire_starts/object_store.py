""" Object store API wrapper for reading and writing datasets
"""
import logging
from app.utils.s3 import get_client

logger = logging.getLogger(__name__)


async def list():
    logger.info('Retrieving datasets')
    async with get_client() as (client, bucket):
        datasets = await client.list_objects_v2(Bucket=bucket, Prefix='human-fire-starts')
        if 'Contents' in datasets:
            # Iterate through each entry.
            for prediction in datasets['Contents']:
                # Filename is in the "Key" entry.
                object_name = prediction['Key']
                logger.info(object_name)
