""" Object store API wrapper for reading and writing datasets
"""
from datetime import datetime
import io
import json
import logging
import os
from typing import List
from app.utils.s3 import get_client
from os.path import dirname, abspath
from dataclasses import dataclass

logger = logging.getLogger(__name__)
DATASET_FOLDER_PATH = os.path.join(dirname(abspath(__file__)), 'data')
human_fire_starts_folder = 'human-fire-starts'


@dataclass
class Dataset:
    """ Struct to keep dataset name and content together"""
    name: str
    content: io.BytesIO


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
    folder_timestamp = datetime.now().isoformat()
    async with get_client() as (client, bucket):
        for dataset_path in dataset_paths:
            with open(dataset_path, encoding="utf-8") as source_file:
                geojson_data = json.load(source_file)
                filename = os.path.basename(os.path.realpath(dataset_path))
                keypath = os.path.join(human_fire_starts_folder, folder_timestamp, filename)
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
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str != '' else None
            timestamps.append(timestamp)
    timestamps = [t for t in timestamps if t is not None]
    latest_timestamp = timestamps[-1]
    if latest_timestamp is None:
        return None

    return human_fire_starts_folder + '/' + latest_timestamp.isoformat()


async def get_latest_datasets() -> List[Dataset]:
    """
        Stream latest fire starts dataset content into byte buffer and return as string
        Assumes we just have a fire starts geojson dataset in each date folder
    """
    async with get_client() as (client, bucket):
        latest_datasets_folder = await get_latest_dataset_path(client, bucket)
        logger.info("Latest dataset folder: %s", latest_datasets_folder)
        latest_datasets = (await client.list_objects_v2(Bucket=bucket, Prefix=latest_datasets_folder))['Contents']

        datasets = []
        for dataset in latest_datasets:
            logger.info("Streaming object: %s", dataset.get('Key'))
            bio = io.BytesIO()
            response = await client.get_object(Bucket=bucket, Key=dataset.get('Key'))
            # this will ensure the connection is correctly re-used/closed
            async with response['Body'] as stream:
                bio.write(await stream.read())
                bio.seek(0)
            logger.info('Wrote byte stream')
            object_name = dataset.get('Key').split('/')[-1]
            datasets.append(Dataset(name=object_name, content=bio))
        return datasets


async def download_latest_dataset() -> str:
    """
        Download latest datasets to data folder
    """
    latest_datasets = await get_latest_datasets()
    for latest_dataset in latest_datasets:
        dest_pathname = os.path.join(DATASET_FOLDER_PATH, latest_dataset.name)
        logger.info("Saving %s to %s", latest_dataset.name, dest_pathname)
        with open(dest_pathname, 'wb') as outfile:
            outfile.write(latest_dataset.content.getbuffer())
