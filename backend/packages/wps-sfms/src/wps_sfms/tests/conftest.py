from collections.abc import Generator
from contextlib import contextmanager
from typing import Optional

import numpy as np
import pytest
from osgeo import gdal, osr
from pytest_mock import MockerFixture
from wps_shared.geospatial.wps_dataset import WPSDataset

from wps_sfms.tests.raster_test_utils import TEST_INPUT_NODATA, create_test_wps_dataset


@pytest.fixture
def output_mask(mocker: MockerFixture) -> Generator[WPSDataset, None, None]:
    """Provide and patch the final BC output mask used by processor tests."""
    mask = create_test_wps_dataset("mask.tif", np.ones((1, 1), dtype=np.float32))

    @contextmanager
    def mask_context() -> Generator[WPSDataset, None, None]:
        yield mask

    mocker.patch(
        "wps_sfms.processors.foliar_moisture_content.open_bc_mask_dataset",
        side_effect=mask_context,
    )
    mocker.patch(
        "wps_sfms.processors.surface_fuel_consumption.open_bc_mask_dataset",
        side_effect=mask_context,
    )
    yield mask
    mask.close()


def create_test_raster(
    path: str,
    width: int,
    height: int,
    extent: tuple,
    data: Optional[np.ndarray] = None,
    epsg: int = 4326,
    fill_value: float = 1.0,
    nodata: float = TEST_INPUT_NODATA,
):
    """
    Create a test GeoTIFF raster in memory using GDAL's /vsimem/ filesystem.

    :param path: Output path (should use /vsimem/ prefix)
    :param width: Raster width in pixels
    :param height: Raster height in pixels
    :param extent: (xmin, xmax, ymin, ymax)
    :param data: Optional numpy array for raster data, defaults to fill_value
    :param epsg: EPSG code for projection
    :param fill_value: Value to fill raster with if data not provided
    :param nodata: NoData value
    :return: None
    """
    driver: gdal.Driver = gdal.GetDriverByName("GTiff")
    ds: gdal.Dataset = driver.Create(path, width, height, 1, gdal.GDT_Float32)

    xmin, xmax, ymin, ymax = extent
    xres = (xmax - xmin) / width
    yres = (ymax - ymin) / height
    ds.SetGeoTransform((xmin, xres, 0, ymax, 0, -yres))

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    ds.SetProjection(srs.ExportToWkt())

    band: gdal.Band = ds.GetRasterBand(1)
    band.SetNoDataValue(nodata)

    if data is not None:
        band.WriteArray(data.astype(np.float32))
    else:
        band.WriteArray(np.full((height, width), fill_value, dtype=np.float32))
    band.FlushCache()
    ds = None
