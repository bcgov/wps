"""Uploads a memray capture file to the object store.

Used by the env_canada job cronjobs (bcgov/wps#5637): when MEMRAY_ENABLED=true, the
container's entrypoint wraps the job with `memray run`, then invokes this script to
push the resulting capture off the pod before it's garbage collected.
"""

import asyncio
import logging
import os
import sys

import aiofiles
from wps_shared.utils.s3_client import S3Client
from wps_shared.wps_logging import configure_logging

logger = logging.getLogger(__name__)


async def upload_profile(file_path: str, model: str):
    filename = os.path.basename(file_path)
    key = f"memray-profiles/{model}/{filename}"
    async with aiofiles.open(file_path, "rb") as f:
        contents = await f.read()
    async with S3Client() as client:
        await client.put_object(key=key, body=contents)
    logger.info("Uploaded memray profile to %s in bucket %s", key, client.bucket)


def main():
    configure_logging()
    file_path, model = sys.argv[1], sys.argv[2]
    asyncio.run(upload_profile(file_path, model))


if __name__ == "__main__":
    main()
