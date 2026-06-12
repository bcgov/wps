from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from fuel_grid.fuel_masked_tpi import (
    MissingFuelTypeRasterError,
    create_fuel_masked_tpi_raster,
)


@pytest.mark.anyio
async def test_create_fuel_masked_tpi_raster_uploads_versioned_object(monkeypatch):
    fuel_type_raster = SimpleNamespace(
        year=2026,
        version=3,
        object_store_path="sfms/static/fuel/2026/fbp2026_v3.tif",
    )
    get_processed_fuel_raster_details = AsyncMock(return_value=fuel_type_raster)

    @asynccontextmanager
    async def fake_session_scope():
        yield "session"

    class RecordingS3Client:
        uploaded = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def put_object(self, key, body):
            self.uploaded.append((key, body))

    def prepare_masked_tif(temp_dir, fuel_type_raster_path):
        assert fuel_type_raster_path == "sfms/static/fuel/2026/fbp2026_v3.tif"
        masked_tpi_path = f"{temp_dir}/masked.tif"
        with open(masked_tpi_path, "wb") as masked_tpi:
            masked_tpi.write(b"masked-tpi")
        return masked_tpi_path

    s3_client = RecordingS3Client()
    monkeypatch.setattr(
        "fuel_grid.fuel_masked_tpi.get_async_read_session_scope", fake_session_scope
    )
    monkeypatch.setattr(
        "fuel_grid.fuel_masked_tpi.get_processed_fuel_raster_details",
        get_processed_fuel_raster_details,
    )
    monkeypatch.setattr("fuel_grid.fuel_masked_tpi.S3Client", lambda: s3_client)
    monkeypatch.setattr("fuel_grid.fuel_masked_tpi.prepare_masked_tif", prepare_masked_tif)
    monkeypatch.setattr(
        "fuel_grid.fuel_masked_tpi.config.get",
        lambda key: "bc_dem_250m_tpi_win21_classified.tif",
    )

    key = await create_fuel_masked_tpi_raster(2026, 3)

    assert key == "dem/tpi/bc_dem_250m_tpi_win21_classified_fuel_masked_2026_v3.tif"
    assert s3_client.uploaded == [(key, b"masked-tpi")]
    get_processed_fuel_raster_details.assert_awaited_once_with("session", 2026, 3)


@pytest.mark.anyio
async def test_create_fuel_masked_tpi_raster_fails_when_raster_missing(monkeypatch):
    @asynccontextmanager
    async def fake_session_scope():
        yield "session"

    monkeypatch.setattr(
        "fuel_grid.fuel_masked_tpi.get_async_read_session_scope", fake_session_scope
    )
    monkeypatch.setattr(
        "fuel_grid.fuel_masked_tpi.get_processed_fuel_raster_details",
        AsyncMock(return_value=None),
    )

    with pytest.raises(MissingFuelTypeRasterError):
        await create_fuel_masked_tpi_raster(2026)
