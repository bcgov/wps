import pytest
from unittest.mock import AsyncMock
from wps_shared.sfms.raster_addresser import RasterKeyAddresser
from wps_shared.geospatial.fuel_raster import get_versioned_fuel_raster_key


@pytest.mark.anyio
async def test_get_fuel_layer_key_returns_processed(monkeypatch):
    mock_raster = type("MockRaster", (), {"object_store_path": "sfms/static/2025/fbp2025.tif"})

    monkeypatch.setattr("wps_shared.geospatial.fuel_raster.set_s3_gdal_config", lambda: None)
    monkeypatch.setattr(
        "wps_shared.geospatial.fuel_raster.config", {"OBJECT_STORE_BUCKET": "my-bucket"}
    )
    monkeypatch.setattr(
        "wps_shared.geospatial.fuel_raster.get_most_recent_fuel_layer",
        AsyncMock(return_value=mock_raster),
    )

    key = await get_versioned_fuel_raster_key(
        session="mock_session", raster_addresser=RasterKeyAddresser(), year=2025, version=1
    )

    assert key == "/vsis3/my-bucket/sfms/static/2025/fbp2025.tif"


@pytest.mark.anyio
async def test_get_fuel_layer_key_returns_unprocessed(monkeypatch):
    monkeypatch.setattr("wps_shared.geospatial.fuel_raster.set_s3_gdal_config", lambda: None)
    monkeypatch.setattr(
        "wps_shared.geospatial.fuel_raster.config",
        {"OBJECT_STORE_BUCKET": "my-bucket", "FUEL_RASTER_NAME": "fuel-unprocessed.tif"},
    )
    monkeypatch.setattr(
        "wps_shared.geospatial.fuel_raster.get_most_recent_fuel_layer", AsyncMock(return_value=None)
    )

    key = await get_versioned_fuel_raster_key(
        session="mock_session", raster_addresser=RasterKeyAddresser(), year=2025, version=1
    )

    assert key == "sfms/static/fuel-unprocessed.tif"
