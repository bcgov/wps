import os
import pytest
from osgeo import gdal
import numpy as np

from app.utils.geospatial import raster_mul, warp_to_match_extent

fixture_path = os.path.join(os.path.dirname(__file__), "snow_masked_hfi20240810.tif")


def get_test_tpi_raster(hfi_ds: gdal.Dataset, fill_value: int):
    # Get raster dimensions
    x_size = hfi_ds.RasterXSize
    y_size = hfi_ds.RasterYSize

    # Get the geotransform and projection from the first raster
    geotransform = hfi_ds.GetGeoTransform()
    projection = hfi_ds.GetProjection()

    # Create the output raster
    driver = gdal.GetDriverByName("MEM")
    out_ds: gdal.Dataset = driver.Create("memory", x_size, y_size, 1, gdal.GDT_Byte)

    # Set the geotransform and projection
    out_ds.SetGeoTransform(geotransform)
    out_ds.SetProjection(projection)

    filler_data = hfi_ds.GetRasterBand(1).ReadAsArray()
    tpi_data = np.full_like(filler_data, fill_value)

    # Write the modified data to the new raster
    out_band = out_ds.GetRasterBand(1)
    out_band.SetNoDataValue(0)
    out_band.WriteArray(tpi_data)
    return out_ds


def get_tpi_raster_wrong_shape():
    driver = gdal.GetDriverByName("MEM")
    out_ds: gdal.Dataset = driver.Create("memory", 1, 1, 1, gdal.GDT_Byte)
    out_band = out_ds.GetRasterBand(1)
    out_band.SetNoDataValue(0)
    out_band.WriteArray(np.array([[1]]))
    return out_ds


def test_zero_case():
    hfi_ds: gdal.Dataset = gdal.Open(fixture_path, gdal.GA_ReadOnly)
    tpi_ds: gdal.Dataset = get_test_tpi_raster(hfi_ds, 0)

    masked_raster = raster_mul(tpi_ds, hfi_ds)
    masked_data = masked_raster.GetRasterBand(1).ReadAsArray()

    assert masked_data.shape == hfi_ds.GetRasterBand(1).ReadAsArray().shape
    assert np.all(masked_data == 0) == True

    hfi_ds = None
    tpi_ds = None


def test_identity_case():
    hfi_ds: gdal.Dataset = gdal.Open(fixture_path, gdal.GA_ReadOnly)
    tpi_ds: gdal.Dataset = get_test_tpi_raster(hfi_ds, 1)

    masked_raster = raster_mul(tpi_ds, hfi_ds)
    masked_data = masked_raster.GetRasterBand(1).ReadAsArray()
    hfi_data = hfi_ds.GetRasterBand(1).ReadAsArray()

    # do the simple classification for hfi, pixels >4k are 1
    hfi_data[hfi_data >= 1] = 1
    hfi_data[hfi_data < 1] = 0

    assert masked_data.shape == hfi_data.shape
    assert np.all(masked_data == hfi_data) == True

    hfi_ds = None
    tpi_ds = None


def test_wrong_dimensions():
    hfi_ds: gdal.Dataset = gdal.Open(fixture_path, gdal.GA_ReadOnly)
    tpi_ds: gdal.Dataset = get_tpi_raster_wrong_shape()

    with pytest.raises(ValueError):
        raster_mul(tpi_ds, hfi_ds)

    hfi_ds = None
    tpi_ds = None


def test_warp_to_match_dimension():
    hfi_ds: gdal.Dataset = gdal.Open(fixture_path, gdal.GA_ReadOnly)
    tpi_ds: gdal.Dataset = get_tpi_raster_wrong_shape()

    driver = gdal.GetDriverByName("MEM")
    out_dataset = driver.Create("memory", hfi_ds.RasterXSize, hfi_ds.RasterYSize, 1, gdal.GDT_Byte)

    warp_to_match_extent(tpi_ds, hfi_ds, out_dataset)
    output_data = out_dataset.GetRasterBand(1).ReadAsArray()
    hfi_data = hfi_ds.GetRasterBand(1).ReadAsArray()

    assert hfi_data.shape == output_data.shape

    hfi_ds = None
    tpi_ds = None
