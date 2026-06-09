from contextlib import asynccontextmanager
from datetime import datetime
from types import SimpleNamespace
from typing import AsyncIterator, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from shapely import wkb
from shapely.geometry import Polygon
from sqlalchemy.ext.asyncio import AsyncSession

from app.fuel_grid.install import (
    FuelGridInstallCounts,
    InstalledFuelRaster,
    ProcessedFuelRaster,
    create_fuel_type_raster_record,
    fuel_types_layer_from_db,
    install_fuel_grid,
    populate_static_fuel_grid_data,
    process_fuel_type_raster_for_install,
)
from wps_shared.sfms.raster_addresser import BaseRasterAddresser


class MockS3Client:
    object_exists_result = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def object_exists(self, key):
        assert key == "sfms/static/fbp2026.tif"
        return self.object_exists_result


def make_mock_session() -> tuple[AsyncSession, MagicMock]:
    session_mock = MagicMock(spec=AsyncSession)
    return cast(AsyncSession, session_mock), session_mock


@asynccontextmanager
async def fake_session_scope() -> AsyncIterator[AsyncSession]:
    session, _ = make_mock_session()
    yield session


def test_fuel_types_layer_from_db_accepts_unflushed_hex_wkb():
    geom = wkb.dumps(
        Polygon([(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)]),
        hex=True,
        srid=3005,
    )
    row = SimpleNamespace(id=None, fuel_type_id=1, geom=geom)

    with fuel_types_layer_from_db([row]) as layer:
        layer.ResetReading()
        feature = layer.GetNextFeature()

        assert layer.GetFeatureCount() == 1
        assert feature.GetField("id") == 1
        assert feature.GetField("fuel_type_id") == 1
        assert feature.GetGeometryRef().GetArea() == 100


@pytest.mark.anyio
async def test_process_fuel_type_raster_for_install_creates_new_version(monkeypatch):
    mock_process = AsyncMock(
        return_value=(
            2026,
            4,
            100,
            200,
            "sfms/static/fuel/2026/fbp2026_v4.tif",
            "hash-2026",
            datetime(2026, 6, 1),
        )
    )

    monkeypatch.setattr("app.fuel_grid.install.S3Client", lambda: MockS3Client())
    monkeypatch.setattr("app.fuel_grid.install.process_fuel_type_raster", mock_process)

    result = await process_fuel_type_raster_for_install(2026, "fbp2026.tif", BaseRasterAddresser())

    assert result == ProcessedFuelRaster(
        year=2026,
        version=4,
        xsize=100,
        ysize=200,
        object_store_path="sfms/static/fuel/2026/fbp2026_v4.tif",
        content_hash="hash-2026",
        create_timestamp=datetime(2026, 6, 1),
    )
    mock_process.assert_awaited_once()


@pytest.mark.anyio
async def test_process_fuel_type_raster_for_install_fails_when_source_missing(monkeypatch):
    missing_s3_client = MockS3Client()
    missing_s3_client.object_exists_result = False
    mock_process = AsyncMock()
    monkeypatch.setattr("app.fuel_grid.install.S3Client", lambda: missing_s3_client)
    monkeypatch.setattr("app.fuel_grid.install.process_fuel_type_raster", mock_process)

    with pytest.raises(FileNotFoundError, match="sfms/static/fbp2026.tif"):
        await process_fuel_type_raster_for_install(2026, "fbp2026.tif", BaseRasterAddresser())

    mock_process.assert_not_called()


@pytest.mark.anyio
async def test_create_fuel_type_raster_record_reserves_id_without_flushing(monkeypatch):
    session, session_mock = make_mock_session()
    added = []
    session_mock.add.side_effect = added.append
    session_mock.flush = AsyncMock(
        side_effect=AssertionError("flush should not happen before static data is staged")
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.reserve_fuel_type_raster_id", AsyncMock(return_value=42)
    )
    processed_raster = ProcessedFuelRaster(
        year=2026,
        version=4,
        xsize=100,
        ysize=200,
        object_store_path="sfms/static/fuel/2026/fbp2026_v4.tif",
        content_hash="hash-2026",
        create_timestamp=datetime(2026, 6, 1),
    )

    result = await create_fuel_type_raster_record(session, processed_raster)

    assert result == InstalledFuelRaster(
        id=42,
        year=2026,
        version=4,
        object_store_path="sfms/static/fuel/2026/fbp2026_v4.tif",
        content_hash="hash-2026",
    )
    assert added[0].id == 42
    assert result.record is added[0]


@pytest.mark.anyio
async def test_populate_static_fuel_grid_data_flushes_once_after_population(monkeypatch):
    session, session_mock = make_mock_session()
    flush_count = 0

    async def count_flushes():
        nonlocal flush_count
        flush_count += 1

    session_mock.flush = AsyncMock(side_effect=count_flushes)
    fuel_type_raster = InstalledFuelRaster(
        id=42,
        year=2026,
        version=4,
        object_store_path="sfms/static/fuel/2026/fbp2026_v4.tif",
        content_hash="hash-2026",
    )
    expected_counts = FuelGridInstallCounts(
        advisory_fuel_types=1,
        advisory_shape_fuels=1,
        combustible_area=1,
        tpi_fuel_area=1,
        advisory_shape_fuels_duplicates=0,
    )
    populate_advisory_fuel_types = MagicMock(return_value=["fuel-type-row"])
    populate_advisory_shape_fuels = AsyncMock()
    populate_combustible_area = MagicMock()
    populate_tpi_fuel_area = MagicMock()
    verify_static_fuel_grid_data = AsyncMock(return_value=expected_counts)

    monkeypatch.setattr(
        "app.fuel_grid.install.get_versioned_fuel_raster_key", lambda *_: "fuel-key"
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.get_fire_zone_unit_shape_type_id", AsyncMock(return_value=1)
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.get_fire_zone_units", AsyncMock(return_value=["zone"])
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.populate_advisory_fuel_types", populate_advisory_fuel_types
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.populate_advisory_shape_fuels", populate_advisory_shape_fuels
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.populate_combustible_area", populate_combustible_area
    )
    monkeypatch.setattr("app.fuel_grid.install.populate_tpi_fuel_area", populate_tpi_fuel_area)
    monkeypatch.setattr(
        "app.fuel_grid.install.verify_static_fuel_grid_data", verify_static_fuel_grid_data
    )

    counts = await populate_static_fuel_grid_data(
        session, fuel_type_raster, "dem/tpi/tpi_fuel_masked.tif"
    )

    assert counts == expected_counts
    assert flush_count == 1
    populate_advisory_fuel_types.assert_called_once()
    populate_advisory_shape_fuels.assert_awaited_once()
    populate_combustible_area.assert_called_once()
    populate_tpi_fuel_area.assert_called_once()
    verify_static_fuel_grid_data.assert_awaited_once_with(session, 42)


@pytest.mark.anyio
async def test_install_fuel_grid_cleans_up_object_store_artifacts_on_failure(monkeypatch):
    processed_raster = ProcessedFuelRaster(
        year=2026,
        version=4,
        xsize=100,
        ysize=200,
        object_store_path="sfms/static/fuel/2026/fbp2026_v4.tif",
        content_hash="hash-2026",
        create_timestamp=datetime(2026, 6, 1),
    )
    installed_raster = InstalledFuelRaster(
        id=42,
        year=2026,
        version=4,
        object_store_path="sfms/static/fuel/2026/fbp2026_v4.tif",
        content_hash="hash-2026",
    )
    cleanup = AsyncMock()

    monkeypatch.setattr(
        "app.fuel_grid.install.process_fuel_type_raster_for_install",
        AsyncMock(return_value=processed_raster),
    )
    monkeypatch.setattr("app.fuel_grid.install.generate_fuel_masked_tpi_raster", AsyncMock())
    monkeypatch.setattr(
        "app.fuel_grid.install.get_fuel_masked_tpi_key", lambda _: "dem/tpi/masked.tif"
    )
    monkeypatch.setattr("app.fuel_grid.install.get_async_write_session_scope", fake_session_scope)
    monkeypatch.setattr(
        "app.fuel_grid.install.create_fuel_type_raster_record",
        AsyncMock(return_value=installed_raster),
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.populate_static_fuel_grid_data",
        AsyncMock(side_effect=RuntimeError("verification failed")),
    )
    monkeypatch.setattr("app.fuel_grid.install.cleanup_object_store_artifacts", cleanup)

    with pytest.raises(RuntimeError, match="verification failed"):
        await install_fuel_grid(2026, "fbp2026.tif")

    cleanup.assert_awaited_once_with(processed_raster, "dem/tpi/masked.tif")
