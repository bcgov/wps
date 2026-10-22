"""The percent grass curing raster primary FBP reads, archived by content hash so each run's exact
grass curing input survives the live key being replaced."""

import logging

from wps_shared.sfms.raster_addresser import S3Key
from wps_shared.utils.s3_client import S3Client

from wps_sfms.raster_archive import archive_if_missing, content_hash
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
    archive_key = raster_addresser.get_grass_curing_archive_key(content_hash(raster_bytes))
    if await archive_if_missing(s3_client, archive_key, raster_bytes):
        logger.info("Archived grass curing raster: %s", archive_key)
    return archive_key
