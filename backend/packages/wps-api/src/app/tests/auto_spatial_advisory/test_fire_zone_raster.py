from contextlib import nullcontext
from unittest.mock import AsyncMock

import numpy as np
import pytest
from osgeo import gdal

from app.auto_spatial_advisory.fire_zone_raster import validate_fire_zone_raster


def create_zone_raster(path: str, values: np.ndarray, nodata_value: int | None = -1) -> None:
    dataset = gdal.GetDriverByName("GTiff").Create(
        path, values.shape[1], values.shape[0], 1, gdal.GDT_Int32
    )
    band = dataset.GetRasterBand(1)
    band.WriteArray(values)
    if nodata_value is not None:
        band.SetNoDataValue(nodata_value)
    dataset = None


@pytest.mark.anyio
async def test_validate_fire_zone_raster_accepts_known_ids_and_background(monkeypatch):
    path = "/vsimem/known_fire_zone_units.tif"
    create_zone_raster(path, np.array([[-1, 7], [8, -1]]))
    monkeypatch.setattr(
        "app.auto_spatial_advisory.fire_zone_raster.BaseRasterAddresser.get_fire_zone_units_path",
        lambda _: path,
    )
    monkeypatch.setattr("app.auto_spatial_advisory.fire_zone_raster.gdal_s3_context", nullcontext)
    session = AsyncMock()
    session.execute.return_value = [("7", 70), ("8", 80)]

    try:
        await validate_fire_zone_raster(session)
    finally:
        gdal.Unlink(path)


@pytest.mark.anyio
async def test_validate_fire_zone_raster_rejects_unknown_ids(monkeypatch):
    path = "/vsimem/unknown_fire_zone_units.tif"
    create_zone_raster(path, np.array([[-1, 7], [9, -1]]))
    monkeypatch.setattr(
        "app.auto_spatial_advisory.fire_zone_raster.BaseRasterAddresser.get_fire_zone_units_path",
        lambda _: path,
    )
    monkeypatch.setattr("app.auto_spatial_advisory.fire_zone_raster.gdal_s3_context", nullcontext)
    session = AsyncMock()
    session.execute.return_value = [("7", 70)]

    try:
        with pytest.raises(ValueError, match=r"unknown source identifiers: \[9\]"):
            await validate_fire_zone_raster(session)
    finally:
        gdal.Unlink(path)


@pytest.mark.anyio
async def test_validate_fire_zone_raster_rejects_missing_nodata(monkeypatch):
    path = "/vsimem/fire_zone_units_without_nodata.tif"
    create_zone_raster(path, np.array([[7, 8]]), nodata_value=None)
    monkeypatch.setattr(
        "app.auto_spatial_advisory.fire_zone_raster.BaseRasterAddresser.get_fire_zone_units_path",
        lambda _: path,
    )
    monkeypatch.setattr("app.auto_spatial_advisory.fire_zone_raster.gdal_s3_context", nullcontext)

    try:
        with pytest.raises(ValueError, match="does not define a nodata value"):
            await validate_fire_zone_raster(AsyncMock())
    finally:
        gdal.Unlink(path)
