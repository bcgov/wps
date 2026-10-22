import hashlib
from unittest.mock import AsyncMock, MagicMock

import pytest

from wps_sfms.grass_curing_raster import archive_grass_curing_raster
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser

RASTER_BYTES = b"grass curing tif"
CONTENT_HASH = hashlib.sha256(RASTER_BYTES).hexdigest()
LIVE_KEY = "sfms_ng/static/percent_grass_curing_65.tif"
ARCHIVE_KEY = f"sfms_ng/static/archive/percent_grass_curing_65/{CONTENT_HASH}.tif"


def s3_client(*existing_keys: str) -> MagicMock:
    client = MagicMock()
    client.object_exists = AsyncMock(side_effect=lambda key: key in existing_keys)
    client.read_object = AsyncMock(return_value=RASTER_BYTES)
    client.put_object = AsyncMock()
    return client


@pytest.mark.anyio
async def test_archives_new_raster_by_hash():
    client = s3_client(LIVE_KEY)

    result = await archive_grass_curing_raster(client, SFMSNGRasterAddresser())

    assert result == ARCHIVE_KEY
    client.read_object.assert_awaited_once_with(LIVE_KEY)
    client.put_object.assert_awaited_once_with(ARCHIVE_KEY, RASTER_BYTES)


@pytest.mark.anyio
async def test_existing_archive_is_not_rewritten():
    client = s3_client(LIVE_KEY, ARCHIVE_KEY)

    result = await archive_grass_curing_raster(client, SFMSNGRasterAddresser())

    assert result == ARCHIVE_KEY
    client.put_object.assert_not_awaited()


@pytest.mark.anyio
async def test_missing_live_raster_raises():
    client = s3_client()

    with pytest.raises(RuntimeError, match="Missing grass curing raster"):
        await archive_grass_curing_raster(client, SFMSNGRasterAddresser())

    client.read_object.assert_not_awaited()
