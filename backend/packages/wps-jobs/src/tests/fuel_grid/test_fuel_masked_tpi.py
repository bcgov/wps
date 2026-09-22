from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import numpy as np
import pytest
from osgeo import gdal, osr

from wps_shared.geospatial.wps_dataset import Georeference, WPSDataset

from fuel_grid.fuel_masked_tpi import (
    MissingFuelTypeRasterError,
    create_fuel_masked_tpi_raster,
    prepare_masked_tif,
)


def test_prepare_masked_tif_masks_noncombustible_fuel_and_preserves_tpi_grid(
    tmp_path: Path, monkeypatch
):
    fuel_path = str(tmp_path / "fuel.tif")
    tpi_path = str(tmp_path / "classified_tpi.tif")
    georeference = Georeference((0, 10, 0, 20, 0, -10), osr.GetUserInputAsWKT("EPSG:3005"))
    WPSDataset.from_array(
        np.array([[1, 99], [2, 0]], dtype=np.uint8),
        georeference,
        datatype=gdal.GDT_Byte,
        output_path=fuel_path,
    ).close()
    WPSDataset.from_array(
        np.array([[1, 2], [3, 1]], dtype=np.uint8),
        georeference,
        datatype=gdal.GDT_Byte,
        output_path=tpi_path,
    ).close()

    raster_paths = {
        "fuel/source.tif": fuel_path,
        "dem/tpi/classified_tpi.tif": tpi_path,
    }
    addresser = SimpleNamespace(gdal_path=lambda key: raster_paths[str(key)])
    monkeypatch.setattr("fuel_grid.fuel_masked_tpi.set_s3_gdal_config", lambda: None)
    monkeypatch.setattr("fuel_grid.fuel_masked_tpi.BaseRasterAddresser", lambda: addresser)
    monkeypatch.setattr("fuel_grid.fuel_masked_tpi.config.get", lambda _: "classified_tpi.tif")

    output_path = prepare_masked_tif(str(tmp_path), "fuel/source.tif")

    output = gdal.Open(output_path, gdal.GA_ReadOnly)
    output_band = output.GetRasterBand(1)
    np.testing.assert_array_equal(output_band.ReadAsArray(), [[1, 0], [3, 0]])
    assert output.GetGeoTransform() == georeference.geotransform
    assert output.GetSpatialRef().IsSame(osr.SpatialReference(georeference.projection))
    assert output_band.GetBlockSize() == [256, 256]
    output = None


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
