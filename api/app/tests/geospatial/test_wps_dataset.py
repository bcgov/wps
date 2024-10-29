import os
import numpy as np
from osgeo import osr, gdal
import pytest
import tempfile

from app.geospatial.wps_dataset import WPSDataset

hfi_tif = os.path.join(os.path.dirname(__file__), "snow_masked_hfi20240810.tif")
zero_tif = os.path.join(os.path.dirname(__file__), "zero_layer.tif")


def create_test_dataset(filename, width, height, extent, projection, data_type=gdal.GDT_Float32, fill_value=None, no_data_value=None) -> gdal.Dataset:
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
    fill_data = rng.random((height, width)).astype(np.float32)

    if fill_value is not None:
        fill_data = np.full((height, width), fill_value)

    dataset.GetRasterBand(1).SetNoDataValue(0)
    dataset.GetRasterBand(1).WriteArray(fill_data)

    return dataset


def test_raster_with_context():
    """
    with opens the dataset and closes after the context ends
    """
    with WPSDataset(hfi_tif) as wps_ds:
        assert wps_ds.as_gdal_ds() is not None

    assert wps_ds.as_gdal_ds() is None


def test_raster_set_no_data_value():
    original_no_data_value = 0
    driver: gdal.Driver = gdal.GetDriverByName("MEM")
    dataset: gdal.Dataset = driver.Create("test_dataset_no_data_value.tif", 2, 2, 1, eType=gdal.GDT_Int32)
    fill_data = np.full((2, 2), 2)
    fill_data[0, 0] = original_no_data_value
    dataset.GetRasterBand(1).SetNoDataValue(original_no_data_value)
    dataset.GetRasterBand(1).WriteArray(fill_data)

    with WPSDataset(ds_path=None, ds=dataset) as wps_ds:
        original_array = wps_ds.as_gdal_ds().GetRasterBand(1).ReadAsArray()
        original_nodata_value = wps_ds.as_gdal_ds().GetRasterBand(1).GetNoDataValue()
        updated_array, updated_nodata_value = wps_ds.replace_nodata_with(-1)

        assert original_array[0, 0] == original_nodata_value
        assert updated_array[0, 0] == updated_nodata_value


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


def test_latitude_array():
    lats_3005_tif = os.path.join(os.path.dirname(__file__), "3005_lats.tif")
    lats_4326_tif = os.path.join(os.path.dirname(__file__), "4326_lats.tif")
    with WPSDataset(ds_path=lats_3005_tif) as lats_3005_ds, WPSDataset(ds_path=lats_4326_tif) as lats_4326_ds:
        output_ds: WPSDataset = lats_3005_ds.warp_to_match(lats_4326_ds, "/vsimem/test_lats.tif")
        original_ds = gdal.Open(lats_4326_tif)
        original_lats = original_ds.GetRasterBand(1).ReadAsArray()
        warped_lats = output_ds.generate_latitude_array()
        assert np.all(original_lats == warped_lats) == True
        output_ds = None


def test_get_nodata_mask():
    set_no_data_value = 0
    driver: gdal.Driver = gdal.GetDriverByName("MEM")
    dataset: gdal.Dataset = driver.Create("test_dataset_no_data_value.tif", 2, 2, 1, eType=gdal.GDT_Int32)
    fill_data = np.full((2, 2), 2)
    fill_data[0, 0] = set_no_data_value
    dataset.GetRasterBand(1).SetNoDataValue(set_no_data_value)
    dataset.GetRasterBand(1).WriteArray(fill_data)

    with WPSDataset(ds_path=None, ds=dataset) as ds:
        mask, nodata_value = ds.get_nodata_mask()
        assert nodata_value == set_no_data_value
        assert mask[0, 0] == True  # The first pixel should return True as nodata
        assert mask[0, 1] == False  # Any other pixel should return False


def test_from_array():
    extent1 = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    original_ds = create_test_dataset("test_dataset_1.tif", 100, 100, extent1, 4326)
    original_ds.GetRasterBand(1).SetNoDataValue(-99)
    og_band = original_ds.GetRasterBand(1)
    og_array = og_band.ReadAsArray()
    dtype = og_band.DataType
    og_transform = original_ds.GetGeoTransform()
    og_proj = original_ds.GetProjection()

    with WPSDataset.from_array(og_array, og_transform, og_proj, nodata_value=-99, datatype=dtype) as wps:
        wps_ds = wps.as_gdal_ds()
        assert wps_ds.ReadAsArray()[1, 2] == og_array[1, 2]
        assert wps_ds.GetGeoTransform() == og_transform
        assert wps_ds.GetProjection() == og_proj
        assert wps_ds.GetRasterBand(1).DataType == dtype
        assert wps_ds.GetRasterBand(1).GetNoDataValue() == -99
