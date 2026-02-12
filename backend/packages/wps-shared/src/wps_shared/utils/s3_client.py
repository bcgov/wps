import os
import io
import logging
import hashlib
from typing import Any
from aiobotocore.session import get_session
from wps_shared import config
from wps_shared.geospatial.wps_dataset import WPSDataset

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
        self.client_context = self.session.create_client(
            "s3",
            endpoint_url=f"https://{self.server}",
            aws_secret_access_key=self.secret_key,
            aws_access_key_id=self.user_id,
        )
        self.client = await self.client_context.__aenter__()
        return self

    async def __aexit__(self, *args):
        if hasattr(self, "client_context") and self.client_context:
            await self.client_context.__aexit__(*args)
        self.client = None
        self.client_context = None

    async def object_exists(self, target_path: str):
        """Check if and object exists in the object store"""
        try:
            await self.client.head_object(Bucket=self.bucket, Key=target_path)
            return True
        except Exception:
            return False

    async def all_objects_exist(self, *s3_keys: str):
        for key in s3_keys:
            key_exists = await self.object_exists(key)
            if not key_exists:
                return False
        return True

    async def get_content_hash(self, key, hash_alg: str = "sha256"):
        response = await self.client.get_object(Bucket=self.bucket, Key=key)
        async with response["Body"] as stream:
            fuel_layer_bytes = await stream.read()
            with io.BytesIO(fuel_layer_bytes) as f:
                content_hash = hashlib.file_digest(f, hash_alg).hexdigest()
                return content_hash

    async def get_fuel_raster(self, key: str, expected_hash: str, hash_alg: str = "sha256"):
        response = await self.client.get_object(Bucket=self.bucket, Key=key)
        async with response["Body"] as stream:
            fuel_layer_bytes = await stream.read()
            with io.BytesIO(fuel_layer_bytes) as f:
                content_hash = hashlib.file_digest(f, hash_alg).hexdigest()
                if content_hash != expected_hash:
                    raise ValueError(
                        "Content hash: %s, does not match expected hash: %s for file key: %s",
                        content_hash,
                        expected_hash,
                        key,
                    )
                return fuel_layer_bytes

    async def put_object(self, key: str, body: Any):
        await self.client.put_object(Bucket=self.bucket, Key=key, Body=body)

    async def copy_object(self, old_key: str, new_key: str):
        await self.client.copy_object(
            Bucket=self.bucket, CopySource={"Bucket": self.bucket, "Key": old_key}, Key=new_key
        )

    async def delete_object(self, key: str):
        await self.client.delete_object(Bucket=self.bucket, Key=key)

    async def delete_all_objects(self, keys: list[str], quiet: bool = True):
        """Delete up to 1000 keys in a single request."""
        if not keys:
            return

        await self.client.delete_objects(
            Bucket=self.bucket,
            Delete={
                "Objects": [{"Key": k} for k in keys],
                "Quiet": quiet,
            },
        )

    async def iter_common_prefixes(self, prefix: str):
        """Paginated yield CommonPrefixes under a prefix (Delimiter='/')."""
        continuation_token = None

        while True:
            kwargs = {
                "Bucket": self.bucket,
                "Prefix": prefix,
                "Delimiter": "/",
                "MaxKeys": 1000,
            }
            if continuation_token:
                kwargs["ContinuationToken"] = continuation_token

            res = await self.client.list_objects_v2(**kwargs)

            for cp in res.get("CommonPrefixes", []):
                yield cp["Prefix"]

            if not res.get("IsTruncated"):
                break

            continuation_token = res.get("NextContinuationToken")

    async def iter_keys(self, prefix: str):
        """Yield all object keys under a prefix (paginated)."""
        continuation_token = None

        while True:
            kwargs = {
                "Bucket": self.bucket,
                "Prefix": prefix,
                "MaxKeys": 1000,
            }
            if continuation_token:
                kwargs["ContinuationToken"] = continuation_token

            res = await self.client.list_objects_v2(**kwargs)

            for obj in res.get("Contents", []):
                yield obj["Key"]

            if not res.get("IsTruncated"):
                break

            continuation_token = res.get("NextContinuationToken")

    async def delete_prefix(self, prefix: str, dry_run: bool = False) -> int:
        """
        Delete all objects under a prefix.
        Returns number of objects deleted.
        """
        batch: list[str] = []
        total = 0

        async for key in self.iter_keys(prefix):
            batch.append(key)

            if len(batch) == 1000:
                if not dry_run:
                    await self.delete_all_objects(batch)
                total += len(batch)
                batch.clear()

        if batch:
            if not dry_run:
                await self.delete_all_objects(batch)
            total += len(batch)

        return total

    async def persist_raster_data(
        self, temp_dir: str, key: str, transform, projection, values, no_data_value
    ) -> str:
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

    @staticmethod
    async def stream_object(key: str, byte_range: str = None, chunk_size: int = 65536):
        """
        Stream an object from S3 with automatic client lifecycle management.

        This function manages the S3Client lifecycle internally - the client will be
        closed when the generator is exhausted or an error occurs.

        :param key: s3 key to stream
        :param byte_range: Optional byte range string (e.g., "bytes=0-1023")
        :param chunk_size: size of chunks to yield (default: 64KB)
        :return: tuple of (async generator, response dict) - generator yields chunks, response contains metadata
        """
        s3_client = S3Client()
        await s3_client.__aenter__()

        try:
            params = {"Bucket": s3_client.bucket, "Key": key}
            if byte_range:
                params["Range"] = byte_range

            response = await s3_client.client.get_object(**params)
            stream = response["Body"]

            async def gen():
                try:
                    while True:
                        chunk = await stream.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    stream.close()
                    await s3_client.__aexit__(None, None, None)

            return gen(), response

        except Exception:
            await s3_client.__aexit__(None, None, None)
            raise
