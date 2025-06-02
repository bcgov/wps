import os
import numpy as np
from app.utils import generate_fuel_cog
from tempfile import TemporaryDirectory
from osgeo import gdal

fuel_tif_500m = os.path.join(os.path.dirname(__file__), "fuel_sample.tif")


def test_reclassify_geotiff():
    with TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "reclassified_fuel.tif")
        result = generate_fuel_cog.reclassify_fuel_geotiff(fuel_tif_500m, output_path)
        assert result == output_path

        assert os.path.exists(output_path)

        ds = gdal.Open(output_path)
        band = ds.GetRasterBand(1)
        array = band.ReadAsArray()
        assert array.dtype == np.uint8  # Ensure it's byte data type


def test_reclassify_fuel_array_basic():
    arr = np.array([[2010, 2030, 2050, 500, 2020, 2000, 8], [2060, 2070, 2080, 595, 2040, 2, 8]])
    expected = np.array([[8, 10, 12, 14, 14, 99, 8], [8, 8, 12, 14, 99, 2, 8]])
    result = generate_fuel_cog.reclassify_fuel_array(arr)
    np.testing.assert_array_equal(result, expected)


def test_reclassify_fuel_array_with_no_data():
    arr = np.array(
        [[2010, 2030, 2050, 500, 2020, 2000, 9999], [2060, 2070, 2080, 595, 2040, 2, 9999]]
    )
    expected = np.array([[8, 10, 12, 14, 14, 99, 255], [8, 8, 12, 14, 99, 2, 255]])
    result = generate_fuel_cog.reclassify_fuel_array(arr, no_data_value=9999)
    np.testing.assert_array_equal(result, expected)


def test_reclassify_fuel_array_nothing_to_reclass():
    arr = np.array([[1, 2], [3, 4]])
    expected = np.array([[1, 2], [3, 4]])
    result = generate_fuel_cog.reclassify_fuel_array(arr)
    np.testing.assert_array_equal(result, expected)
