"""Content-hash archiving for static rasters whose live keys are replaced over time, so a run's
recorded archive key keeps naming the exact bytes it read."""

import hashlib

from wps_shared.sfms.raster_addresser import S3Key
from wps_shared.utils.s3_client import S3Client


def content_hash(raster_bytes: bytes) -> str:
    """Return the SHA-256 hex digest an archive key is addressed by."""
    return hashlib.sha256(raster_bytes).hexdigest()


async def archive_if_missing(s3_client: S3Client, archive_key: S3Key, raster_bytes: bytes) -> bool:
    """
    Write ``raster_bytes`` to ``archive_key`` unless it already exists. An existing archive already
    holds the same bytes, since the key is addressed by their content hash.

    :return: Whether the archive was written
    """
    if await s3_client.object_exists(archive_key):
        return False
    await s3_client.put_object(archive_key, raster_bytes)
    return True
