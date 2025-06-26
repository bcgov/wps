from unittest.mock import AsyncMock

import pytest

from app.auto_spatial_advisory.fuel_type_layer import (
    get_current_fuel_type_raster,
    get_fuel_type_raster_by_year,
)

FUEL_RASTER_NAME = "fbp2024.tif"


@pytest.mark.anyio
async def test_get_current_fuel_type_raster_uses_correct_name(monkeypatch):
    mock_session = AsyncMock()
    mock_get_latest_fuel_type_raster_by_fuel_raster_name = AsyncMock()
    monkeypatch.setattr(
        "app.auto_spatial_advisory.fuel_type_layer.config", {"FUEL_RASTER_NAME": FUEL_RASTER_NAME}
    )
    monkeypatch.setattr(
        "app.auto_spatial_advisory.fuel_type_layer.get_latest_fuel_type_raster_by_fuel_raster_name",
        mock_get_latest_fuel_type_raster_by_fuel_raster_name,
    )
    await get_current_fuel_type_raster(mock_session)
    mock_get_latest_fuel_type_raster_by_fuel_raster_name.assert_called_with(
        mock_session, FUEL_RASTER_NAME[:-4]
    )


@pytest.mark.anyio
async def test_get_fuel_type_raster_by_year_matching_year(monkeypatch):
    mock_session = AsyncMock()
    mock_get_processed_fuel_raster_details = AsyncMock()
    monkeypatch.setattr(
        "app.auto_spatial_advisory.fuel_type_layer.config", {"FUEL_RASTER_NAME": FUEL_RASTER_NAME}
    )
    monkeypatch.setattr(
        "app.auto_spatial_advisory.fuel_type_layer.get_processed_fuel_raster_details",
        mock_get_processed_fuel_raster_details,
    )

    await get_fuel_type_raster_by_year(mock_session, 2024)
    mock_get_processed_fuel_raster_details.assert_called_with(mock_session, 2024, None)


@pytest.mark.anyio
async def test_get_fuel_type_raster_by_year_mismatched_year(monkeypatch):
    mock_session = AsyncMock()
    mock_get_processed_fuel_raster_details = AsyncMock()
    monkeypatch.setattr(
        "app.auto_spatial_advisory.fuel_type_layer.config", {"FUEL_RASTER_NAME": FUEL_RASTER_NAME}
    )
    monkeypatch.setattr(
        "app.auto_spatial_advisory.fuel_type_layer.get_processed_fuel_raster_details",
        mock_get_processed_fuel_raster_details,
    )
    await get_fuel_type_raster_by_year(mock_session, 2025)
    mock_get_processed_fuel_raster_details.assert_called_with(mock_session, 2024, None)
