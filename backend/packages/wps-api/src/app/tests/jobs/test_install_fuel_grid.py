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
    ProcessedFuelRaster,
    create_fuel_type_raster_record,
    fuel_types_layer_from_db,
    install_fuel_grid,
    populate_static_fuel_grid_data,
    process_fuel_type_raster_for_install,
)
from wps_shared.db.models.fuel_type_raster import (
    FUEL_RASTER_STATUS_INSTALLING,
    FUEL_RASTER_STATUS_READY,
    FuelTypeRaster,
)
from wps_shared.sfms.raster_addresser import BaseRasterAddresser


class MockS3Client:
    object_exists_result = True
    content_hash_result = "hash-2026"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def object_exists(self, key):
        assert key == "sfms/static/fbp2026.tif"
        return self.object_exists_result

    async def get_content_hash(self, key):
        assert key == "sfms/static/fbp2026.tif"
        return self.content_hash_result


def make_mock_session() -> tuple[AsyncSession, MagicMock]:
    session_mock = MagicMock(spec=AsyncSession)
    return cast(AsyncSession, session_mock), session_mock


@asynccontextmanager
async def fake_session_scope() -> AsyncIterator[AsyncSession]:
    session, _ = make_mock_session()
    yield session


def patch_no_matching_fuel_raster(monkeypatch):
    monkeypatch.setattr(
        "app.fuel_grid.install.get_staged_fuel_raster_hash",
        AsyncMock(return_value="hash-2026"),
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.find_ready_fuel_raster_by_year_and_hash",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.find_versioned_fuel_raster_by_hash",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.ensure_fuel_masked_tpi_raster",
        AsyncMock(return_value=True),
    )


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
async def test_create_fuel_type_raster_record_flushes_installing_parent(monkeypatch):
    session, session_mock = make_mock_session()
    added = []
    session_mock.add.side_effect = added.append
    session_mock.flush = AsyncMock()
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

    assert result is added[0]
    assert result.install_status == FUEL_RASTER_STATUS_INSTALLING
    assert result.object_store_path == "sfms/static/fuel/2026/fbp2026_v4.tif"
    session_mock.flush.assert_awaited_once()


@pytest.mark.anyio
async def test_populate_static_fuel_grid_data_flushes_once_after_population(monkeypatch):
    session, session_mock = make_mock_session()
    flush_count = 0

    async def count_flushes():
        nonlocal flush_count
        flush_count += 1

    session_mock.flush = AsyncMock(side_effect=count_flushes)
    fuel_type_raster = FuelTypeRaster(
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
    installing_raster = FuelTypeRaster(
        id=42,
        year=2026,
        version=4,
        object_store_path="sfms/static/fuel/2026/fbp2026_v4.tif",
        content_hash="hash-2026",
        install_status=FUEL_RASTER_STATUS_INSTALLING,
    )
    cleanup = AsyncMock()

    patch_no_matching_fuel_raster(monkeypatch)
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
        AsyncMock(return_value=installing_raster),
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.populate_static_fuel_grid_data",
        AsyncMock(side_effect=RuntimeError("verification failed")),
    )
    monkeypatch.setattr("app.fuel_grid.install.cleanup_object_store_artifacts", cleanup)

    with pytest.raises(RuntimeError, match="verification failed"):
        await install_fuel_grid(2026, "fbp2026.tif")

    cleanup.assert_awaited_once_with(processed_raster, "dem/tpi/masked.tif")


@pytest.mark.anyio
async def test_install_fuel_grid_marks_raster_ready_after_verification(monkeypatch):
    processed_raster = ProcessedFuelRaster(
        year=2026,
        version=4,
        xsize=100,
        ysize=200,
        object_store_path="sfms/static/fuel/2026/fbp2026_v4.tif",
        content_hash="hash-2026",
        create_timestamp=datetime(2026, 6, 1),
    )
    installing_raster = FuelTypeRaster(
        id=42,
        year=2026,
        version=4,
        object_store_path="sfms/static/fuel/2026/fbp2026_v4.tif",
        content_hash="hash-2026",
        install_status=FUEL_RASTER_STATUS_INSTALLING,
    )
    expected_counts = FuelGridInstallCounts(
        advisory_fuel_types=1,
        advisory_shape_fuels=1,
        combustible_area=1,
        tpi_fuel_area=1,
        advisory_shape_fuels_duplicates=0,
    )

    patch_no_matching_fuel_raster(monkeypatch)
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
        AsyncMock(return_value=installing_raster),
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.populate_static_fuel_grid_data",
        AsyncMock(return_value=expected_counts),
    )

    result = await install_fuel_grid(2026, "fbp2026.tif")

    assert installing_raster.install_status == FUEL_RASTER_STATUS_READY
    assert installing_raster.ready_timestamp is not None
    assert result is not None
    assert result.fuel_type_raster.install_status == FUEL_RASTER_STATUS_READY
    assert result.counts == expected_counts


@pytest.mark.anyio
async def test_install_fuel_grid_reuses_existing_versioned_s3_raster(monkeypatch):
    existing_processed_raster = ProcessedFuelRaster(
        year=2026,
        version=1,
        xsize=100,
        ysize=200,
        object_store_path="sfms/static/fuel/2026/fbp2026_v1.tif",
        content_hash="hash-2026",
        create_timestamp=datetime(2026, 6, 1),
    )
    installing_raster = FuelTypeRaster(
        id=42,
        year=2026,
        version=1,
        object_store_path="sfms/static/fuel/2026/fbp2026_v1.tif",
        content_hash="hash-2026",
        install_status=FUEL_RASTER_STATUS_INSTALLING,
    )
    expected_counts = FuelGridInstallCounts(
        advisory_fuel_types=1,
        advisory_shape_fuels=1,
        combustible_area=1,
        tpi_fuel_area=1,
        advisory_shape_fuels_duplicates=0,
    )
    find_versioned_fuel_raster = AsyncMock(return_value=existing_processed_raster)
    process_fuel_type_raster_for_install = AsyncMock()
    ensure_fuel_masked_tpi_raster = AsyncMock(return_value=False)
    create_fuel_type_raster_record = AsyncMock(return_value=installing_raster)
    populate_static_fuel_grid_data = AsyncMock(return_value=expected_counts)

    monkeypatch.setattr(
        "app.fuel_grid.install.get_staged_fuel_raster_hash",
        AsyncMock(return_value="hash-2026"),
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.find_ready_fuel_raster_by_year_and_hash",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.find_versioned_fuel_raster_by_hash",
        find_versioned_fuel_raster,
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.process_fuel_type_raster_for_install",
        process_fuel_type_raster_for_install,
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.get_fuel_masked_tpi_key", lambda _: "dem/tpi/masked.tif"
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.ensure_fuel_masked_tpi_raster", ensure_fuel_masked_tpi_raster
    )
    monkeypatch.setattr("app.fuel_grid.install.get_async_write_session_scope", fake_session_scope)
    monkeypatch.setattr(
        "app.fuel_grid.install.create_fuel_type_raster_record",
        create_fuel_type_raster_record,
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.populate_static_fuel_grid_data",
        populate_static_fuel_grid_data,
    )

    result = await install_fuel_grid(2026, "fbp2026.tif")

    assert result is not None
    assert result.fuel_type_raster.version == 1
    assert result.fuel_type_raster.object_store_path == "sfms/static/fuel/2026/fbp2026_v1.tif"
    assert result.counts == expected_counts
    find_versioned_fuel_raster.assert_awaited_once()
    process_fuel_type_raster_for_install.assert_not_awaited()
    ensure_fuel_masked_tpi_raster.assert_awaited_once_with(
        existing_processed_raster, "dem/tpi/masked.tif"
    )
    create_fuel_type_raster_record.assert_awaited_once()
    assert create_fuel_type_raster_record.await_args.args[1] == existing_processed_raster


@pytest.mark.anyio
async def test_install_fuel_grid_skips_ready_raster_with_matching_year_and_hash(
    monkeypatch,
):
    existing_raster = FuelTypeRaster(
        id=42,
        year=2026,
        version=1,
        object_store_path="sfms/static/fuel/2026/fbp2026_v1.tif",
        content_hash="hash-2026",
        install_status=FUEL_RASTER_STATUS_READY,
    )
    get_staged_fuel_raster_hash = AsyncMock(return_value="hash-2026")
    find_ready_fuel_raster = AsyncMock(return_value=existing_raster)
    process_fuel_type_raster_for_install = AsyncMock()
    generate_fuel_masked_tpi_raster = AsyncMock()
    cleanup_object_store_artifacts = AsyncMock()
    logger_mock = MagicMock()

    monkeypatch.setattr(
        "app.fuel_grid.install.get_staged_fuel_raster_hash", get_staged_fuel_raster_hash
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.find_ready_fuel_raster_by_year_and_hash",
        find_ready_fuel_raster,
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.get_fuel_masked_tpi_key_for_version",
        lambda year, version: f"dem/tpi/masked_{year}_v{version}.tif",
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.process_fuel_type_raster_for_install",
        process_fuel_type_raster_for_install,
    )
    monkeypatch.setattr(
        "app.fuel_grid.install.generate_fuel_masked_tpi_raster",
        generate_fuel_masked_tpi_raster,
    )
    monkeypatch.setattr("app.fuel_grid.install.get_async_write_session_scope", fake_session_scope)
    monkeypatch.setattr(
        "app.fuel_grid.install.cleanup_object_store_artifacts", cleanup_object_store_artifacts
    )
    monkeypatch.setattr("app.fuel_grid.install.logger", logger_mock)

    result = await install_fuel_grid(2026, "fbp2026.tif")

    assert result is None
    logger_mock.warning.assert_called_once()
    logger_mock.info.assert_any_call("fuel_type_raster_id: %s", 42)
    logger_mock.info.assert_any_call("staged_source_key: %s", "sfms/static/fbp2026.tif")
    logger_mock.info.assert_any_call("fuel_masked_tpi_key: %s", "dem/tpi/masked_2026_v1.tif")
    get_staged_fuel_raster_hash.assert_awaited_once_with("sfms/static/fbp2026.tif")
    find_ready_fuel_raster.assert_awaited_once()
    process_fuel_type_raster_for_install.assert_not_awaited()
    generate_fuel_masked_tpi_raster.assert_not_awaited()
    cleanup_object_store_artifacts.assert_not_awaited()
