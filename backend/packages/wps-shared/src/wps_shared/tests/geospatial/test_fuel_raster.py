import pytest

from wps_shared.geospatial.fuel_raster import get_versioned_fuel_raster_key


@pytest.mark.anyio
async def test_get_fuel_layer_key_returns_processed(monkeypatch):
    monkeypatch.setattr(
        "wps_shared.geospatial.fuel_raster.config", {"OBJECT_STORE_BUCKET": "my-bucket"}
    )

    key = get_versioned_fuel_raster_key("sfms/static/fuel/2024/fbp2024_v2.tif")

    assert key == "/vsis3/my-bucket/sfms/static/fuel/2024/fbp2024_v2.tif"


def test_get_fuel_layer_key_requires_processed_path(monkeypatch):
    monkeypatch.setattr(
        "wps_shared.geospatial.fuel_raster.config",
        {"OBJECT_STORE_BUCKET": "my-bucket"},
    )

    with pytest.raises(ValueError, match="processed fuel raster"):
        get_versioned_fuel_raster_key(None)
