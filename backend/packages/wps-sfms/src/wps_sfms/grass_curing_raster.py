"""The percent grass curing raster primary FBP reads, archived by content hash so each run's exact
grass curing input survives the live key being replaced."""

import hashlib
import logging

from wps_shared.sfms.raster_addresser import S3Key
from wps_shared.utils.s3_client import S3Client

from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

logger = logging.getLogger(__name__)


async def archive_grass_curing_raster(
    s3_client: S3Client, raster_addresser: SFMSNGRasterAddresser
) -> S3Key:
    """
    Archive the current grass curing raster by content hash.

    :param s3_client: Client the raster is read and archived with
    :param raster_addresser: Addresser naming the live and archive keys
    :return: Archive key of the raster, which holds exactly the bytes that were hashed
    """
    key = raster_addresser.get_grass_curing_key()
    if not await s3_client.object_exists(key):
        raise RuntimeError(f"Missing grass curing raster: {key}")
    raster_bytes = await s3_client.read_object(key)
    content_hash = hashlib.sha256(raster_bytes).hexdigest()
    archive_key = raster_addresser.get_grass_curing_archive_key(content_hash)
    # an existing archive already holds the same bytes
    if not await s3_client.object_exists(archive_key):
        await s3_client.put_object(archive_key, raster_bytes)
        logger.info("Archived grass curing raster: %s", archive_key)
    return archive_key
