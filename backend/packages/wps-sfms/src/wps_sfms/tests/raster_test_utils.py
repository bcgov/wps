"""Shared raster construction helpers for SFMS processor tests."""

import numpy as np
from osgeo import gdal, osr
from wps_shared.geospatial.wps_dataset import WPSDataset

# use an input nodata value that differs from SFMS_NO_DATA to verify output normalization
TEST_INPUT_NODATA = -9999.0


def create_test_wps_dataset(
    path: str,
    values: np.ndarray,
    nodata: float = TEST_INPUT_NODATA,
) -> WPSDataset:
    """Create an in-memory float raster on the standard SFMS test grid."""
    rows, columns = values.shape
    dataset = gdal.GetDriverByName("MEM").Create("", columns, rows, 1, gdal.GDT_Float32)
    dataset.SetGeoTransform((0, 2_000, 0, 10_000, 0, -2_000))

    spatial_reference = osr.SpatialReference()
    spatial_reference.ImportFromEPSG(3005)
    dataset.SetProjection(spatial_reference.ExportToWkt())

    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(nodata)
    band.WriteArray(values)
    return WPSDataset(ds_path=path, ds=dataset)
