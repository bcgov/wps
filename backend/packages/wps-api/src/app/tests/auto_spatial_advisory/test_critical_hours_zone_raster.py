from contextlib import nullcontext
from unittest.mock import AsyncMock

import numpy as np
import pytest
from osgeo import gdal, osr
from wps_shared.schemas.stations import WFWXWeatherStation

from app.auto_spatial_advisory.critical_hours import group_stations_by_zone


def create_zone_raster(path: str) -> None:
    dataset = gdal.GetDriverByName("GTiff").Create(path, 2, 2, 1, gdal.GDT_Int32)
    dataset.SetGeoTransform((-2, 1, 0, 2, 0, -1))
    spatial_reference = osr.SpatialReference()
    spatial_reference.ImportFromEPSG(4326)
    dataset.SetProjection(spatial_reference.ExportToWkt())
    band = dataset.GetRasterBand(1)
    band.WriteArray(np.array([[-1, 7], [8, -1]]))
    band.SetNoDataValue(-1)
    dataset = None


def station(code: int, longitude: float, latitude: float) -> WFWXWeatherStation:
    return WFWXWeatherStation(
        wfwx_id=str(code),
        code=code,
        name=str(code),
        longitude=longitude,
        latitude=latitude,
        elevation=100,
        zone_code=None,
    )


@pytest.mark.anyio
async def test_group_stations_by_zone_samples_source_identifiers(monkeypatch):
    path = "/vsimem/critical_hours_zone_units.tif"
    create_zone_raster(path)
    monkeypatch.setattr(
        "app.auto_spatial_advisory.critical_hours.BaseRasterAddresser.get_fire_zone_units_path",
        lambda _: path,
    )
    monkeypatch.setattr("app.auto_spatial_advisory.critical_hours.gdal_s3_context", nullcontext)
    session = AsyncMock()
    session.execute.return_value = [("7", 70), ("8", 80)]

    result = await group_stations_by_zone(
        session,
        [
            station(1, -0.5, 1.5),
            station(2, -1.5, 0.5),
            station(3, -1.5, 1.5),
            station(4, 5, 5),
        ],
    )

    assert {zone_id: [item.code for item in items] for zone_id, items in result.items()} == {
        70: [1],
        80: [2],
    }
