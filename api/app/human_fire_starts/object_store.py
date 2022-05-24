""" Object store API wrapper for reading and writing datasets
"""
from datetime import date, datetime
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


async def get_latest_dataset_path(client, bucket):
    """ Return latest dataset path based on below scheme
        Bucket path is: <bucket>/human-fire-starts/<today-iso>/<dataset-filname>
    """
    datasets = await client.list_objects_v2(Bucket=bucket, Prefix=human_fire_starts_folder)
    timestamps = []
    if 'Contents' in datasets:
        # Iterate through each entry.
        for prediction in datasets['Contents']:
            # Filename is in the "Key" entry.
            object_name = prediction['Key']
            timestamp_str = object_name.split('/')[1]
            timestamp = date.fromisoformat(timestamp_str) if timestamp_str != '' else None
            timestamps.append(timestamp)
    timestamps = [t for t in timestamps if t is not None]
    latest_timestamp = timestamps[-1]
    if latest_timestamp is None:
        return None

    return human_fire_starts_folder + '/' + latest_timestamp.isoformat()


async def get_latest_dataset() -> str:
    """
        Stream latest fire starts dataset content into byte buffer and return as string
        Assumes we just have a fire starts geojson dataset in each date folder
    """
    async with get_client() as (client, bucket):
        latest_datasets_folder = await get_latest_dataset_path(client, bucket)
        latest_datasets = (await client.list_objects_v2(Bucket=bucket, Prefix=latest_datasets_folder))['Contents']

        def get_last_modified(obj): return int(obj['LastModified'].strftime('%s'))
        latest_dataset = [obj['Key'] for obj in sorted(latest_datasets, key=get_last_modified)][0]
        logger.info(latest_dataset)

        bio = io.BytesIO()
        response = await client.get_object(Bucket=bucket, Key=latest_dataset)
        # this will ensure the connection is correctly re-used/closed
        async with response['Body'] as stream:
            bio.write(await stream.read())
            bio.seek(0)
        logger.info('wrote byte stream')
        out = bio.getvalue().decode('utf-8')
        bio.close()
        return out
