import os
import logging
from typing import Any
from aiobotocore.session import get_session
from app import config
from app.geospatial.wps_dataset import WPSDataset

logger = logging.getLogger(__name__)


class S3Client:
    def __init__(
        self,
        server=config.get("OBJECT_STORE_SERVER"),
        user_id=config.get("OBJECT_STORE_USER_ID"),
        secret_key=config.get("OBJECT_STORE_SECRET"),
        bucket=config.get("OBJECT_STORE_BUCKET"),
    ):
        self.server = server
        self.user_id = user_id
        self.secret_key = secret_key
        self.bucket = bucket
        self.session = get_session()

    async def __aenter__(self):
        client_context = self.session.create_client("s3", endpoint_url=f"https://{self.server}", aws_secret_access_key=self.secret_key, aws_access_key_id=self.user_id)
        self.client = await client_context.__aenter__()
        return self

    async def __aexit__(self, *_):
        self.client = None
        self.session = None
        del self.client
        del self.session

    async def object_exists(self, target_path: str):
        """Check if and object exists in the object store"""
        # using list_objects, but could be using stat as well? don't know what's best.
        result = await self.client.list_objects_v2(Bucket=self.bucket, Prefix=target_path)
        contents = result.get("Contents", None)
        if contents:
            for content in contents:
                key = content.get("Key")
                if key == target_path:
                    return True
        return False

    async def all_objects_exist(self, *s3_keys: str):
        for key in s3_keys:
            key_exists = await self.object_exists(key)
            if not key_exists:
                return False
        return True

    async def put_object(self, key: str, body: Any):
        await self.client.put_object(Bucket=self.bucket, Key=key, Body=body)

    async def persist_raster_data(self, temp_dir: str, key: str, transform, projection, values, no_data_value) -> str:
        """
        Persists a geotiff in s3 based on transform, projection, values and no data value.

        :param temp_dir: temporary directory to write geotiff
        :param key: s3 key to store output dataset
        :param transform: gdal geotransform
        :param projection: gdal projection
        :param values: array of values
        :param no_data_value: array no data value
        :return: path to temporary written geotiff file
        """
        temp_geotiff = os.path.join(temp_dir, os.path.basename(key))
        with WPSDataset.from_array(values, transform, projection, no_data_value) as ds:
            ds.export_to_geotiff(temp_geotiff)

        logger.info(f"Writing to s3 -- {key}")
        await self.put_object(key=key, body=open(temp_geotiff, "rb"))
        return temp_geotiff
