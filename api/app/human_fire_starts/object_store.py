""" Object store API wrapper for reading and writing datasets
"""
from datetime import date
import io
import json
import logging
import os
from typing import List
from app.utils.s3 import get_client

logger = logging.getLogger(__name__)
human_fire_starts_folder = 'human-fire-starts'


async def list_datasets():
    logger.info('Retrieving datasets')
    async with get_client() as (client, bucket):
        datasets = await client.list_objects_v2(Bucket=bucket, Prefix=human_fire_starts_folder)
        if 'Contents' in datasets:
            # Iterate through each entry.
            for prediction in datasets['Contents']:
                # Filename is in the "Key" entry.
                object_name = prediction['Key']
                logger.info(object_name)


async def publish_datasets(dataset_paths: List[str]):
    """ Upload datasets by supplied local paths to object store
        Bucket path is: <bucket>/human-fire-starts/<today-iso>/<dataset-filname>
    """
    logger.info('Publishing human fire starts datasets: %s', ', '.join(dataset_paths))
    async with get_client() as (client, bucket):
        for dataset_path in dataset_paths:
            with open(dataset_path, encoding="utf-8") as source_file:
                geojson_data = json.load(source_file)
                filename = os.path.basename(os.path.realpath(dataset_path))
                keypath = os.path.join(human_fire_starts_folder, date.today().isoformat(), filename)
                with io.StringIO() as sio:
                    json.dump(geojson_data, sio)
                    # smash it into binary
                    sio.seek(0)
                    bio = io.BytesIO(sio.read().encode('utf8'))
                    # go back to start
                    bio.seek(0)
                    # smash it into the object store.
                    logger.info('Uploading %s to %s with filename %s', dataset_path, keypath, filename)
                    await client.put_object(Bucket=bucket, Key=keypath, Body=bio)
