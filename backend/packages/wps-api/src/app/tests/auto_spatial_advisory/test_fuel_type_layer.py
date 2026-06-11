from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.auto_spatial_advisory.fuel_type_layer import get_current_fuel_type_raster
from wps_shared.db.crud.fuel_layer import (
    get_fuel_type_raster_by_year,
    get_ready_fuel_type_raster_by_year_and_hash,
)
from wps_shared.db.models.fuel_type_raster import FUEL_RASTER_STATUS_READY, FuelTypeRaster


@pytest.mark.anyio
async def test_get_current_fuel_type_raster_uses_current_year(monkeypatch):
    mock_session = AsyncMock()
    mock_get_fuel_type_raster_by_year = AsyncMock()
    monkeypatch.setattr(
        "app.auto_spatial_advisory.fuel_type_layer.get_utc_now",
        lambda: datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(
        "app.auto_spatial_advisory.fuel_type_layer.get_fuel_type_raster_by_year",
        mock_get_fuel_type_raster_by_year,
    )
    await get_current_fuel_type_raster(mock_session)
    mock_get_fuel_type_raster_by_year.assert_called_with(mock_session, 2026)


@pytest.mark.anyio
async def test_get_fuel_type_raster_by_year_matching_year(monkeypatch):
    mock_session = AsyncMock()
    mock_raster = FuelTypeRaster(
        year=2024,
        version=1,
        object_store_path="sfms/static/fuel/2024/fbp2024_v1.tif",
        install_status=FUEL_RASTER_STATUS_READY,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_raster
    mock_session.execute.return_value = mock_result

    result = await get_fuel_type_raster_by_year(mock_session, 2024)

    assert result is mock_raster
    mock_session.execute.assert_called_once()
    stmt = mock_session.execute.call_args.args[0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert f"fuel_type_raster.install_status = '{FUEL_RASTER_STATUS_READY}'" in compiled


@pytest.mark.anyio
async def test_get_fuel_type_raster_by_year_returns_none(monkeypatch):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    result = await get_fuel_type_raster_by_year(mock_session, 2025)

    assert result is None


@pytest.mark.anyio
async def test_get_ready_fuel_type_raster_by_year_and_hash(monkeypatch):
    mock_session = AsyncMock()
    mock_raster = FuelTypeRaster(
        year=2026,
        version=1,
        object_store_path="sfms/static/fuel/2026/fbp2026_v1.tif",
        content_hash="hash-2026",
        install_status=FUEL_RASTER_STATUS_READY,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_raster
    mock_session.execute.return_value = mock_result

    result = await get_ready_fuel_type_raster_by_year_and_hash(mock_session, 2026, "hash-2026")

    assert result is mock_raster
    mock_session.execute.assert_called_once()
    stmt = mock_session.execute.call_args.args[0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "fuel_type_raster.year = 2026" in compiled
    assert "fuel_type_raster.content_hash = 'hash-2026'" in compiled
    assert f"fuel_type_raster.install_status = '{FUEL_RASTER_STATUS_READY}'" in compiled
