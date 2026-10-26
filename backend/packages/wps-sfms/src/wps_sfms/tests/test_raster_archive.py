import hashlib
from unittest.mock import AsyncMock, MagicMock

import pytest

from wps_sfms.raster_archive import archive_if_missing, content_hash

RASTER_BYTES = b"raster bytes"
ARCHIVE_KEY = "sfms_ng/static/archive/raster/abc123.tif"


def s3_client(archive_exists: bool) -> MagicMock:
    client = MagicMock()
    client.object_exists = AsyncMock(return_value=archive_exists)
    client.put_object = AsyncMock()
    return client


def test_content_hash_is_sha256_hex_digest():
    assert content_hash(RASTER_BYTES) == hashlib.sha256(RASTER_BYTES).hexdigest()


def test_content_hash_differs_for_different_bytes():
    assert content_hash(b"a") != content_hash(b"b")


@pytest.mark.anyio
async def test_archive_if_missing_writes_missing_archive():
    client = s3_client(archive_exists=False)

    written = await archive_if_missing(client, ARCHIVE_KEY, RASTER_BYTES)

    assert written is True
    client.object_exists.assert_awaited_once_with(ARCHIVE_KEY)
    client.put_object.assert_awaited_once_with(ARCHIVE_KEY, RASTER_BYTES)


@pytest.mark.anyio
async def test_archive_if_missing_skips_existing_archive():
    client = s3_client(archive_exists=True)

    written = await archive_if_missing(client, ARCHIVE_KEY, RASTER_BYTES)

    assert written is False
    client.object_exists.assert_awaited_once_with(ARCHIVE_KEY)
    client.put_object.assert_not_awaited()
