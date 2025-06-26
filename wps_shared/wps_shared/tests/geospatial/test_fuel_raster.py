from unittest.mock import AsyncMock

import pytest

from wps_shared.geospatial.fuel_raster import get_versioned_fuel_raster_key
from wps_shared.sfms.raster_addresser import RasterKeyAddresser


@pytest.mark.anyio
async def test_get_fuel_layer_key_returns_processed(monkeypatch):
    monkeypatch.setattr(
        "wps_shared.geospatial.fuel_raster.config", {"OBJECT_STORE_BUCKET": "my-bucket"}
    )

    key = get_versioned_fuel_raster_key(
        raster_addresser=RasterKeyAddresser(),
        object_store_path="sfms/static/fuel/2024/fbp2024_v2.tif",
    )

    assert key == "/vsis3/my-bucket/sfms/static/fuel/2024/fbp2024_v2.tif"


@pytest.mark.anyio
async def test_get_fuel_layer_key_returns_unprocessed(monkeypatch):
    monkeypatch.setattr(
        "wps_shared.geospatial.fuel_raster.config",
        {"OBJECT_STORE_BUCKET": "my-bucket", "FUEL_RASTER_NAME": "fuel-unprocessed.tif"},
    )

    key = get_versioned_fuel_raster_key(
        raster_addresser=RasterKeyAddresser(),
        object_store_path=None,
    )

    assert key == "sfms/static/fuel-unprocessed.tif"
