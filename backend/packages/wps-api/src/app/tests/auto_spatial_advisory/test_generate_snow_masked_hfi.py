import os
import tempfile
from datetime import date
from types import SimpleNamespace

import numpy as np
from osgeo import gdal, osr

from app.auto_spatial_advisory.generate_snow_masked_hfi import generate_snow_masked_hfi
from app.auto_spatial_advisory.snow import MASKED_HFI_PATH_NAME
from wps_shared.geospatial.raster_processor import TileConfig
from wps_shared.geospatial.wps_dataset import WPSDataset

WGS84_WKT = osr.SpatialReference()
WGS84_WKT.ImportFromEPSG(4326)
WGS84_WKT = WGS84_WKT.ExportToWkt()

GEOTRANSFORM = (0, 1, 0, 0, 0, -1)


def _make_raster(path: str, values, geotransform=GEOTRANSFORM, projection=WGS84_WKT):
    array = np.array(values, dtype=np.float32)
    height, width = array.shape
    ds = gdal.GetDriverByName("GTiff").Create(path, width, height, 1, gdal.GDT_Float32)
    ds.SetGeoTransform(geotransform)
    ds.SetProjection(projection)
    ds.GetRasterBand(1).WriteArray(array)
    ds.FlushCache()
    return ds


def _patch_snow_s3_source(mocker, snow_path: str):
    """generate_snow_masked_hfi reads the snow coverage raster from a /vsis3/ path - substitute
    a real local raster for it instead of hitting S3."""
    real_gdal_open = gdal.Open
    mocker.patch.object(
        gdal,
        "Open",
        side_effect=lambda path, *args, **kwargs: real_gdal_open(
            snow_path if path.startswith("/vsis3/") else path, *args, **kwargs
        ),
    )


def test_generate_snow_masked_hfi_classifies_and_masks_in_one_pass(mocker):
    """0 = below 4000 or snow-masked, 1 = 4000-10000, 2 = above 10000 (unmasked)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        hfi_path = os.path.join(temp_dir, "hfi.tif")
        _make_raster(hfi_path, [[3000, 6000], [12000, 7000]])

        snow_path = os.path.join(temp_dir, "snow.tif")
        # 5 -> snow free, 101 -> QA/snow free, 5 -> snow free, 20 -> snow covered
        _make_raster(snow_path, [[5, 101], [5, 20]])
        _patch_snow_s3_source(mocker, snow_path)

        result_path = generate_snow_masked_hfi(
            hfi_path, SimpleNamespace(for_date=date(2024, 1, 1)), temp_dir
        )

        assert result_path == os.path.join(temp_dir, MASKED_HFI_PATH_NAME)
        with WPSDataset(result_path) as result:
            assert result.ds.GetRasterBand(1).ReadAsArray().tolist() == [[0, 1], [2, 0]]
            assert result.ds.GetRasterBand(1).DataType == gdal.GDT_Byte
            assert result.ds.GetRasterBand(1).GetNoDataValue() == 0
            assert result.ds.GetGeoTransform() == GEOTRANSFORM


def test_generate_snow_masked_hfi_treats_source_nodata_as_zero(mocker):
    """A real GDAL nodata value on the source (not just NaN) must classify to 0."""
    with tempfile.TemporaryDirectory() as temp_dir:
        hfi_path = os.path.join(temp_dir, "hfi.tif")
        hfi_ds = _make_raster(hfi_path, [[-9999, 6000]])
        hfi_ds.GetRasterBand(1).SetNoDataValue(-9999)
        hfi_ds.FlushCache()
        hfi_ds = None

        snow_path = os.path.join(temp_dir, "snow.tif")
        _make_raster(snow_path, [[5, 5]])  # snow free everywhere
        _patch_snow_s3_source(mocker, snow_path)

        result_path = generate_snow_masked_hfi(
            hfi_path, SimpleNamespace(for_date=date(2024, 1, 1)), temp_dir
        )

        with WPSDataset(result_path) as result:
            assert result.ds.GetRasterBand(1).ReadAsArray().tolist() == [[0, 1]]


def test_generate_snow_masked_hfi_treats_nan_as_nodata_not_highest_severity(mocker):
    """Regression test: NaN compares False against every threshold, so np.select would
    otherwise fall through to `default=2` (the highest severity bucket) instead of being
    treated as nodata."""
    with tempfile.TemporaryDirectory() as temp_dir:
        hfi_path = os.path.join(temp_dir, "hfi.tif")
        _make_raster(hfi_path, [[1000, np.nan]])

        snow_path = os.path.join(temp_dir, "snow.tif")
        _make_raster(snow_path, [[5, 5]])
        _patch_snow_s3_source(mocker, snow_path)

        result_path = generate_snow_masked_hfi(
            hfi_path, SimpleNamespace(for_date=date(2024, 1, 1)), temp_dir
        )

        with WPSDataset(result_path) as result:
            assert result.ds.GetRasterBand(1).ReadAsArray().tolist() == [[0, 0]]


def test_generate_snow_masked_hfi_tiling_matches_single_tile_result(mocker):
    """Windowed tiling must produce the same classified+masked result as one big tile."""
    with tempfile.TemporaryDirectory() as temp_dir:
        rng = np.random.default_rng(seed=11)
        hfi_values = rng.uniform(0, 20000, size=(7, 5)).astype(np.float32)
        snow_values = rng.uniform(0, 100, size=(7, 5)).astype(np.float32)

        hfi_path = os.path.join(temp_dir, "hfi.tif")
        _make_raster(hfi_path, hfi_values)

        snow_path = os.path.join(temp_dir, "snow.tif")
        _make_raster(snow_path, snow_values)
        _patch_snow_s3_source(mocker, snow_path)

        single_tile_dir = os.path.join(temp_dir, "single")
        os.mkdir(single_tile_dir)
        single_tile_result = generate_snow_masked_hfi(
            hfi_path,
            SimpleNamespace(for_date=date(2024, 1, 1)),
            single_tile_dir,
            tile_config=TileConfig(tile_width=100, tile_height=100),
        )

        multi_tile_dir = os.path.join(temp_dir, "multi")
        os.mkdir(multi_tile_dir)
        multi_tile_result = generate_snow_masked_hfi(
            hfi_path,
            SimpleNamespace(for_date=date(2024, 1, 1)),
            multi_tile_dir,
            tile_config=TileConfig(tile_width=2, tile_height=3),
        )

        with WPSDataset(single_tile_result) as single, WPSDataset(multi_tile_result) as multi:
            np.testing.assert_array_equal(
                single.ds.GetRasterBand(1).ReadAsArray(),
                multi.ds.GetRasterBand(1).ReadAsArray(),
            )


def test_generate_snow_masked_hfi_closes_the_output_before_returning(mocker):
    """Regression test: the output dataset is written directly to masked_hfi_path via GDAL's
    GTiff driver. If it isn't closed before generate_snow_masked_hfi returns, callers reopening
    masked_hfi_path right away (as process_hfi.py would) can hit a malformed GeoTIFF - GDAL
    doesn't finalize a GTiff's directory structure until the writing dataset is closed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        hfi_path = os.path.join(temp_dir, "hfi.tif")
        _make_raster(hfi_path, [[5000, 8000], [12000, 3000]])

        snow_path = os.path.join(temp_dir, "snow.tif")
        _make_raster(snow_path, [[50, 5], [90, 20]])
        _patch_snow_s3_source(mocker, snow_path)

        result_path = generate_snow_masked_hfi(
            hfi_path, SimpleNamespace(for_date=date(2024, 1, 1)), temp_dir
        )

        # confirm the file is actually readable, not left with a malformed/incomplete directory
        with WPSDataset(result_path) as reopened:
            assert (reopened.ds.RasterXSize, reopened.ds.RasterYSize) == (2, 2)
