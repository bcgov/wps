from unittest.mock import AsyncMock

import pytest

from app.auto_spatial_advisory.fuel_type_layer import get_fuel_type_raster_by_year


@pytest.mark.anyio
async def test_get_fuel_type_raster_by_year_matching_year(monkeypatch):
    mock_get_processed_fuel_raster_details = AsyncMock()
    monkeypatch.setattr(
        "app.auto_spatial_advisory.fuel_type_layer.config", {"FUEL_RASTER_NAME": "fbp2024.tif"}
    )
    monkeypatch.setattr("app.auto_spatial_advisory.fuel_type_layer.get_processed_fuel_raster_details", mock_get_processed_fuel_raster_details)
    mock_session = AsyncMock()
    await get_fuel_type_raster_by_year(mock_session, 2024)
    mock_get_processed_fuel_raster_details.assert_called_with(mock_session, 2024, None)


@pytest.mark.anyio
async def test_get_fuel_type_raster_by_year_mismatched_year(monkeypatch):
    mock_get_processed_fuel_raster_details = AsyncMock()
    monkeypatch.setattr(
        "app.auto_spatial_advisory.fuel_type_layer.config", {"FUEL_RASTER_NAME": "fbp2024.tif"}
    )
    monkeypatch.setattr("app.auto_spatial_advisory.fuel_type_layer.get_processed_fuel_raster_details", mock_get_processed_fuel_raster_details)
    mock_session = AsyncMock()
    await get_fuel_type_raster_by_year(mock_session, 2025)
    mock_get_processed_fuel_raster_details.assert_called_with(mock_session, 2024, None)

