import os
import numpy as np
from osgeo import osr, gdal
import pytest
import tempfile

from app.geospatial.wps_dataset import WPSDataset

hfi_tif = os.path.join(os.path.dirname(__file__), "snow_masked_hfi20240810.tif")
zero_tif = os.path.join(os.path.dirname(__file__), "zero_layer.tif")


def create_test_dataset(filename, width, height, extent, projection, data_type=gdal.GDT_Float32, fill_value=None) -> gdal.Dataset:
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
    rng = np.random.default_rng(seed=42)  # Reproducible random generator
    random_data = rng.random((height, width)).astype(np.float32)

    if fill_value is None:
        # Write data to the dataset
        dataset.GetRasterBand(1).WriteArray(random_data)
    else:
        fill_data = np.full_like(random_data, fill_value)
        dataset.GetRasterBand(1).WriteArray(fill_data)

    dataset.GetRasterBand(1).SetNoDataValue(0)

    return dataset


def test_raster_with_context():
    """
    with opens the dataset and closes after the context ends
    """
    with WPSDataset(hfi_tif) as wps_ds:
        assert wps_ds.as_gdal_ds() is not None

    assert wps_ds.as_gdal_ds() is None


def test_raster_set_no_data_value():
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    ds_1 = create_test_dataset("test_dataset_no_data_value.tif", 1, 1, extent, 4326, data_type=gdal.GDT_Byte, fill_value=2)
    with WPSDataset(ds_path=None, ds=ds_1) as wps_ds:
        assert wps_ds.as_gdal_ds().GetRasterBand(1).GetNoDataValue() == 0

        wps_ds.replace_nodata_with(-1)
        assert wps_ds.as_gdal_ds().GetRasterBand(1).GetNoDataValue() == -1


def test_raster_mul():
    with WPSDataset(hfi_tif) as wps_ds, WPSDataset(zero_tif) as zero_ds:
        output_ds = wps_ds * zero_ds
        raw_ds = output_ds.as_gdal_ds()
        output_values = raw_ds.GetRasterBand(1).ReadAsArray()
        assert np.all(output_values == 0)


def test_raster_mul_identity():
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    ds_1 = create_test_dataset("test_dataset_1.tif", 1, 1, extent, 4326, data_type=gdal.GDT_Byte, fill_value=2)
    ds_2 = create_test_dataset("test_dataset_2.tif", 1, 1, extent, 4326, data_type=gdal.GDT_Byte, fill_value=1)

    with WPSDataset(ds_path=None, ds=ds_1) as wps1_ds, WPSDataset(ds_path=None, ds=ds_2) as wps2_ds:
        output_ds = wps1_ds * wps2_ds
        output_values = output_ds.as_gdal_ds().GetRasterBand(1).ReadAsArray()
        left_side_values = wps1_ds.as_gdal_ds().GetRasterBand(1).ReadAsArray()
        assert np.all(output_values == left_side_values) == True


def test_raster_mul_wrong_dimensions():
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    wgs_84_ds1 = create_test_dataset("test_dataset_1.tif", 1, 1, extent, 4326)
    wgs_84_ds2 = create_test_dataset("test_dataset_2.tif", 2, 2, extent, 4326)

    with pytest.raises(ValueError):
        with WPSDataset(ds_path=None, ds=wgs_84_ds1) as wps1_ds, WPSDataset(ds_path=None, ds=wgs_84_ds2) as wps2_ds:
            _ = wps1_ds * wps2_ds

    wgs_84_ds1 = None
    wgs_84_ds2 = None


def test_raster_mul_wrong_projections():
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    wgs_84_ds = create_test_dataset("test_dataset_1.tif", 1, 1, extent, 4326)
    mercator_ds = create_test_dataset("test_dataset_2.tif", 1, 1, extent, 3857)

    with pytest.raises(ValueError):
        with WPSDataset(ds_path=None, ds=wgs_84_ds) as wps1_ds, WPSDataset(ds_path=None, ds=mercator_ds) as wps2_ds:
            _ = wps1_ds * wps2_ds

    wgs_84_ds = None
    mercator_ds = None


def test_raster_mul_wrong_origins():
    extent1 = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    wgs_84_ds1 = create_test_dataset("test_dataset_1.tif", 1, 1, extent1, 4326)
    extent2 = (-2, 2, -2, 2)  # xmin, xmax, ymin, ymax
    wgs_84_ds2 = create_test_dataset("test_dataset_2.tif", 1, 1, extent2, 4326)

    with pytest.raises(ValueError):
        with WPSDataset(ds_path=None, ds=wgs_84_ds1) as wps1_ds, WPSDataset(ds_path=None, ds=wgs_84_ds2) as wps2_ds:
            _ = wps1_ds * wps2_ds

    wgs_84_ds1 = None
    wgs_84_ds2 = None


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

    wgs_84_ds = None
    mercator_ds = None


def test_export_to_geotiff():
    extent1 = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    ds_1 = create_test_dataset("test_dataset_1.tif", 3, 3, extent1, 4326, data_type=gdal.GDT_Byte, fill_value=1)

    with WPSDataset(ds_path=None, ds=ds_1) as wps_ds:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "test_export.tif")
            wps_ds.export_to_geotiff(temp_path)

            with WPSDataset(ds_path=temp_path) as exported_ds:
                assert wps_ds.as_gdal_ds().GetProjection() == exported_ds.as_gdal_ds().GetProjection()
                assert wps_ds.as_gdal_ds().GetGeoTransform() == exported_ds.as_gdal_ds().GetGeoTransform()
                assert wps_ds.as_gdal_ds().RasterXSize == exported_ds.as_gdal_ds().RasterXSize
                assert wps_ds.as_gdal_ds().RasterYSize == exported_ds.as_gdal_ds().RasterYSize

                original_values = wps_ds.as_gdal_ds().GetRasterBand(1).ReadAsArray()
                exported_values = exported_ds.as_gdal_ds().GetRasterBand(1).ReadAsArray()
                assert np.all(original_values == exported_values) == True

    ds_1 = None
