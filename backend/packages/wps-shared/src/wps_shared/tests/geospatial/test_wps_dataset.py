import os
import numpy as np
from osgeo import gdal
import pytest
import tempfile

from wps_shared.geospatial.wps_dataset import WPSDataset, multi_wps_dataset_context
from wps_shared.tests.geospatial.dataset_common import create_mock_gdal_dataset, create_test_dataset

hfi_tif = os.path.join(os.path.dirname(__file__), "snow_masked_hfi20240810.tif")  # Byte data
zero_tif = os.path.join(os.path.dirname(__file__), "zero_layer.tif")


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
        output_band = raw_ds.GetRasterBand(1)
        output_values = output_band.ReadAsArray()
        output_datatype = output_band.DataType
        assert np.all(output_values == 0)
        assert output_datatype == gdal.GDT_Byte


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


def test_raster_warp_max_value():
    # Dataset 1: 100x100 pixels, extent in EPSG:3857
    extent1 = (-20037508.34, 20037508.34, -20037508.34, 20037508.34)
    wgs_84_ds = create_test_dataset("test_dataset_1.tif", 100, 100, extent1, 3857, fill_value=90)

    band = wgs_84_ds.GetRasterBand(1)
    array = band.ReadAsArray()
    array[0, 0] = 101  # value to be clamped
    band.WriteArray(array)
    band.FlushCache()

    # Dataset 2: 100x100 pixels, extent in EPSG:3857
    extent2 = (-20037508.34, 20037508.34, -20037508.34, 20037508.34)
    mercator_ds = create_test_dataset("test_dataset_2.tif", 100, 100, extent2, 3857)

    with WPSDataset(ds_path=None, ds=wgs_84_ds) as wps1_ds, WPSDataset(ds_path=None, ds=mercator_ds) as wps2_ds:
        output_ds: WPSDataset = wps1_ds.warp_to_match(wps2_ds, "/vsimem/test.grib2", max_value=100)  # test that we can update an output path with any extension
        out_array = output_ds.as_gdal_ds().GetRasterBand(1).ReadAsArray()
        assert out_array.max() == 100

        # Ensure 90 stayed 90 everywhere since we're doing Nearest Neighbour interp. 100*100 array minus the 1 value we changed
        assert np.count_nonzero(out_array == 90) == (100 * 100 - 1), "Expected at least one value to remain 99"

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


def test_get_nodata_mask_empty():
    dataset: gdal.Dataset = create_mock_gdal_dataset()

    with WPSDataset(ds_path=None, ds=dataset) as ds:
        mask, nodata_value = ds.get_nodata_mask()
        assert mask is None
        assert nodata_value is None


def test_from_array():
    extent1 = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    original_ds = create_test_dataset("test_dataset_1.tif", 100, 100, extent1, 4326)  # float32 datatype
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


def test_from_bytes():
    with open(hfi_tif, "rb") as f:
        file_bytes = f.read()
        with WPSDataset.from_bytes(file_bytes) as wps_ds:
            ds = wps_ds.as_gdal_ds()
            assert ds.RasterCount == 1
            assert ds.RasterXSize == 778
            assert ds.RasterYSize == 683
            assert ds.GetGeoTransform() == (-758000.0, 2000.0, 0.0, 1290000.0, 0.0, -2000.0)
            assert (
                ds.GetProjection()
                == """PROJCS["Lambert Conformal Conic",GEOGCS["NAD83",DATUM["North_American_Datum_1983",SPHEROID["GRS 1980",6378137,298.257222101004,AUTHORITY["EPSG","7019"]],AUTHORITY["EPSG","6269"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4269"]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["latitude_of_origin",49],PARAMETER["central_meridian",-125],PARAMETER["standard_parallel_1",49],PARAMETER["standard_parallel_2",77],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH]]"""
            )
            assert ds.GetMetadata() == {"AREA_OR_POINT": "Area"}


def test_multi_wps_dataset_context(mocker):
    # mock WPSDataset and define the mock dataset paths
    dataset_paths = ["path1", "path2"]
    mock_wps_dataset = mocker.patch("wps_shared.geospatial.wps_dataset.WPSDataset")
    mock_datasets = [mocker.MagicMock(), mocker.MagicMock()]
    mock_wps_dataset.side_effect = mock_datasets  # WPSDataset(path) returns each mock in sequence

    # set each mock to return itself when its context is entered
    for mock_ds in mock_datasets:
        mock_ds.__enter__.return_value = mock_ds

    with multi_wps_dataset_context(dataset_paths) as datasets:
        # check that WPSDataset was called once per path
        mock_wps_dataset.assert_any_call("path1")
        mock_wps_dataset.assert_any_call("path2")

        # verify that the yielded datasets are the mocked instances
        assert datasets == mock_datasets

        # ensure each dataset's context was entered
        for ds in datasets:
            ds.__enter__.assert_called_once()

    # ensure each dataset was closed after the context exited
    for ds in mock_datasets:
        ds.close.assert_called_once()
