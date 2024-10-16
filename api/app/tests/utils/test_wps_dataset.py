import os
import numpy as np
from osgeo import osr, gdal

from app.utils.wps_dataset import WPSDataset

hfi_tif = os.path.join(os.path.dirname(__file__), "snow_masked_hfi20240810.tif")
zero_tif = os.path.join(os.path.dirname(__file__), "zero_layer.tif")


def create_test_dataset(filename, width, height, extent, projection, data_type=gdal.GDT_Float32) -> gdal.Dataset:
    """
    Create a test GDAL dataset.
    """
    # Create a new GDAL dataset
    driver: gdal.Driver = gdal.GetDriverByName("MEM")
    dataset: gdal.Dataset = driver.Create(filename, width, height, 1, data_type)

    # Set the geotransform
    xmin, xmax, ymin, ymax = extent
    xres = (xmax - xmin) / width
    yres = (ymax - ymin) / height
    geotransform = (xmin, xres, 0, ymax, 0, -yres)  # Top-left corner
    dataset.SetGeoTransform(geotransform)

    # Set the projection
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(projection)
    dataset.SetProjection(srs.ExportToWkt())

    # Create some test data (e.g., random values)
    data = np.random.rand(height, width).astype(np.float32)  # Generate random data

    # Write data to the dataset
    dataset.GetRasterBand(1).WriteArray(data)
    return dataset


def test_raster_with_context():
    """
    with opens the dataset and closes after the context ends
    """
    with WPSDataset(hfi_tif) as wps_ds:
        assert wps_ds.as_gdal_ds() is not None

    assert wps_ds.as_gdal_ds() is None


def test_raster_set_no_data_value():
    with WPSDataset(hfi_tif) as wps_ds:
        assert wps_ds.as_gdal_ds().GetRasterBand(1).GetNoDataValue() == 0

        wps_ds.replace_nodata_with(-1)
        assert wps_ds.as_gdal_ds().GetRasterBand(1).GetNoDataValue() == -1


def test_raster_mul():
    with WPSDataset(hfi_tif) as wps_ds, WPSDataset(zero_tif) as zero_ds:
        output_ds = wps_ds * zero_ds
        raw_ds = output_ds.as_gdal_ds()
        output_values = raw_ds.GetRasterBand(1).ReadAsArray()
        assert np.all(output_values == 0)


def test_raster_warp():
    # Dataset 1: 100x100 pixels, extent in EPSG:4326
    extent1 = (-10, 10, -10, 10)  # xmin, xmax, ymin, ymax
    wgs_84_ds = create_test_dataset("test_dataset_1.tif", 100, 100, extent1, 4326)

    # Dataset 2: 200x200 pixels, extent in EPSG:3857
    extent2 = (-20037508.34, 20037508.34, -20037508.34, 20037508.34)
    mercator_ds = create_test_dataset("test_dataset_2.tif", 200, 200, extent2, 3857)

    with WPSDataset(ds_path=None, ds=wgs_84_ds) as wps1_ds, WPSDataset(ds_path=None, ds=mercator_ds) as wps2_ds:
        output_ds: WPSDataset = wps1_ds.warp_to_match(wps2_ds, "/vsimem/test.tif")
        assert output_ds.as_gdal_ds().GetProjection() == wps2_ds.as_gdal_ds().GetProjection()
        assert output_ds.as_gdal_ds().GetGeoTransform() == wps2_ds.as_gdal_ds().GetGeoTransform()
        assert output_ds.as_gdal_ds().RasterXSize == wps2_ds.as_gdal_ds().RasterXSize
        assert output_ds.as_gdal_ds().RasterYSize == wps2_ds.as_gdal_ds().RasterYSize
