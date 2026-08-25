import json
import os
import tempfile

import numpy as np
import pytest
from osgeo import gdal, ogr, osr

from wps_shared.geospatial.wps_dataset import Georeference, WPSDataset, multi_wps_dataset_context
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
    dataset: gdal.Dataset = driver.Create(
        "test_dataset_no_data_value.tif", 2, 2, 1, eType=gdal.GDT_Int32
    )
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


def test_replace_nodata_with_nan_casts_integer_array():
    """replace_nodata_with(np.nan) on an integer raster should cast to float64 and replace nodata with nan."""
    driver: gdal.Driver = gdal.GetDriverByName("MEM")
    dataset: gdal.Dataset = driver.Create("test_nan_int.tif", 2, 2, 1, eType=gdal.GDT_Int32)
    fill_data = np.full((2, 2), 5, dtype=np.int32)
    fill_data[0, 0] = -9999
    dataset.GetRasterBand(1).SetNoDataValue(-9999)
    dataset.GetRasterBand(1).WriteArray(fill_data)

    with WPSDataset(ds_path=None, ds=dataset) as wps_ds:
        array, nodata = wps_ds.replace_nodata_with(np.nan)

        assert array.dtype == np.float64
        assert np.isnan(nodata)
        assert np.isnan(array[0, 0])
        assert array[0, 1] == pytest.approx(5.0)


def test_replace_nodata_with_nan_float_array():
    """replace_nodata_with(np.nan) on a float raster should replace nodata with nan."""
    driver: gdal.Driver = gdal.GetDriverByName("MEM")
    dataset: gdal.Dataset = driver.Create("test_nan_float.tif", 2, 2, 1, eType=gdal.GDT_Float32)
    fill_data = np.full((2, 2), 3.0, dtype=np.float32)
    fill_data[1, 1] = -9999.0
    dataset.GetRasterBand(1).SetNoDataValue(-9999.0)
    dataset.GetRasterBand(1).WriteArray(fill_data)

    with WPSDataset(ds_path=None, ds=dataset) as wps_ds:
        array, nodata = wps_ds.replace_nodata_with(np.nan)

        assert array.dtype == np.float32
        assert np.isnan(nodata)
        assert np.isnan(array[1, 1])
        assert array[0, 0] == pytest.approx(3.0)


def test_replace_nodata_with_no_nodata_set():
    """replace_nodata_with(np.nan) when the band has no nodata value set should not raise and should leave all pixels unchanged."""
    driver: gdal.Driver = gdal.GetDriverByName("MEM")
    dataset: gdal.Dataset = driver.Create("test_no_nodata.tif", 2, 2, 1, eType=gdal.GDT_Float32)
    fill_data = np.full((2, 2), 5.0, dtype=np.float32)
    # deliberately do NOT call SetNoDataValue
    dataset.GetRasterBand(1).WriteArray(fill_data)

    with WPSDataset(ds_path=None, ds=dataset) as wps_ds:
        array, nodata = wps_ds.replace_nodata_with(np.nan)

        assert np.isnan(nodata)
        assert not np.any(np.isnan(array))  # no pixels replaced
        assert np.all(array == pytest.approx(5.0))


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
    ds_1 = create_test_dataset(
        "test_dataset_1.tif", 1, 1, extent, 4326, data_type=gdal.GDT_Byte, fill_value=2
    )
    ds_2 = create_test_dataset(
        "test_dataset_2.tif", 1, 1, extent, 4326, data_type=gdal.GDT_Byte, fill_value=1
    )

    with WPSDataset(ds_path=None, ds=ds_1) as wps1_ds, WPSDataset(ds_path=None, ds=ds_2) as wps2_ds:
        output_ds = wps1_ds * wps2_ds
        output_values = output_ds.as_gdal_ds().GetRasterBand(1).ReadAsArray()
        left_side_values = wps1_ds.as_gdal_ds().GetRasterBand(1).ReadAsArray()
        assert np.all(output_values == left_side_values) == True


def test_raster_mul_defaults_to_memory_backed():
    """Without output_path set on the left operand, `*` keeps its original in-memory (MEM driver) behaviour."""
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    ds_1 = create_test_dataset(
        "test_dataset_1.tif", 1, 1, extent, 4326, data_type=gdal.GDT_Byte, fill_value=2
    )
    ds_2 = create_test_dataset(
        "test_dataset_2.tif", 1, 1, extent, 4326, data_type=gdal.GDT_Byte, fill_value=1
    )

    with (
        WPSDataset(ds_path=None, ds=ds_1) as wps1_ds,
        WPSDataset(ds_path=None, ds=ds_2) as wps2_ds,
    ):
        output_ds = wps1_ds * wps2_ds
        assert output_ds.as_gdal_ds().GetDriver().ShortName == "MEM"


def test_raster_mul_disk_backed():
    """Setting output_path on the left operand backs the `*` result with a real GTiff on disk instead of MEM."""
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    ds_1 = create_test_dataset(
        "test_dataset_1.tif", 2, 2, extent, 4326, data_type=gdal.GDT_Byte, fill_value=2
    )
    ds_2 = create_test_dataset(
        "test_dataset_2.tif", 2, 2, extent, 4326, data_type=gdal.GDT_Byte, fill_value=1
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "masked.tif")

        with (
            WPSDataset(ds_path=None, ds=ds_1, output_path=output_path) as wps1_ds,
            WPSDataset(ds_path=None, ds=ds_2) as wps2_ds,
        ):
            output_ds = wps1_ds * wps2_ds
            raw_ds = output_ds.as_gdal_ds()

            assert raw_ds.GetDriver().ShortName == "GTiff"
            assert np.all(raw_ds.GetRasterBand(1).ReadAsArray() == 2)
            raw_ds.FlushCache()  # caller's responsibility, same as process_elevation_hfi.py

        assert os.path.exists(output_path)

        # confirm the file actually persisted to disk with the multiplied result, not just an in-process handle
        with WPSDataset(output_path) as reopened:
            assert np.all(reopened.as_gdal_ds().GetRasterBand(1).ReadAsArray() == 2)


def test_raster_mul_disk_backed_corrupt_read_if_not_closed_before_reopen():
    """Regression test for https://github.com/bcgov/wps/pull/5754#discussion_r3855512495.

    Reopening a disk-backed `*` result's output_path while the writer dataset is still open
    (only FlushCache()'d, not closed) triggers a GDAL warning that the GeoTIFF's directory is
    malformed, because GDAL doesn't finalize a GTiff's directory structure until the writing
    dataset is closed. Closing the writer first (as process_elevation_hfi.py's
    process_tpi_by_firezone now does) avoids this.
    """
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    ds_1 = create_test_dataset(
        "test_dataset_1.tif", 2, 2, extent, 4326, data_type=gdal.GDT_Byte, fill_value=9
    )
    ds_2 = create_test_dataset(
        "test_dataset_2.tif", 2, 2, extent, 4326, data_type=gdal.GDT_Byte, fill_value=1
    )

    warnings = []
    gdal.PushErrorHandler(lambda err_class, err_num, msg: warnings.append(msg))
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "masked.tif")

            with (
                WPSDataset(ds_path=None, ds=ds_1, output_path=output_path) as wps1_ds,
                WPSDataset(ds_path=None, ds=ds_2) as wps2_ds,
            ):
                # bug reproduction: hold the writer open (FlushCache only) and reopen its path
                with wps1_ds * wps2_ds as writer_result:
                    writer_result.as_gdal_ds().FlushCache()

                    with WPSDataset(output_path):
                        pass

                assert any("StripByteCounts" in w for w in warnings)
                warnings.clear()

                # fix: reopening after the writer's `with` block has closed it is clean
                with WPSDataset(output_path):
                    pass

        assert warnings == []
    finally:
        gdal.PopErrorHandler()


def test_array_protocol_lets_dataset_be_used_as_a_numpy_array():
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    ds = create_test_dataset(
        "test_dataset_1.tif", 2, 2, extent, 4326, data_type=gdal.GDT_Int16, fill_value=5
    )
    ds.GetRasterBand(1).WriteArray(np.array([[1, 5000], [11000, 0]], dtype=np.int16))

    with WPSDataset(ds_path=None, ds=ds) as wps_ds:
        assert np.array_equal(np.asarray(wps_ds), np.array([[1, 5000], [11000, 0]]))
        assert np.array_equal(
            np.where(np.asarray(wps_ds) >= 10000, 1, 0), np.array([[0, 0], [1, 0]])
        )
        # __array__ lets numpy FUNCTIONS treat wps_ds as array-like directly
        assert np.count_nonzero(wps_ds) == 3


def test_ordering_comparisons_against_a_threshold():
    """source < 4000 etc. return a plain boolean array, for classify-style code written
    directly against a WPSDataset (see transform())."""
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    ds = create_test_dataset(
        "test_dataset_1.tif", 2, 2, extent, 4326, data_type=gdal.GDT_Int16, fill_value=0
    )
    ds.GetRasterBand(1).WriteArray(np.array([[1000, 5000], [11000, 0]], dtype=np.int16))

    with WPSDataset(ds_path=None, ds=ds) as wps_ds:
        assert np.array_equal(wps_ds < 4000, np.array([[True, False], [False, True]]))
        assert np.array_equal(wps_ds <= 5000, np.array([[True, True], [False, True]]))
        assert np.array_equal(wps_ds > 4000, np.array([[False, True], [True, False]]))
        assert np.array_equal(wps_ds >= 5000, np.array([[False, True], [True, False]]))


def test_repeated_comparisons_only_read_the_band_once(mocker):
    """Multi-condition classify-style code (np.select([source < 4000, source < 10000], ...)) does
    two comparisons against the same instance - the underlying GDAL read must not happen twice."""
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    ds = create_test_dataset(
        "test_dataset_1.tif", 2, 2, extent, 4326, data_type=gdal.GDT_Int16, fill_value=0
    )
    ds.GetRasterBand(1).WriteArray(np.array([[1000, 5000], [11000, 0]], dtype=np.int16))

    # gdal.Band.ReadAsArray is patched at the class level since GetRasterBand(1) returns a new
    # Python wrapper object each call, even though it's the same underlying band.
    read_spy = mocker.patch.object(
        gdal.Band, "ReadAsArray", wraps=gdal.Band.ReadAsArray, autospec=True
    )

    with WPSDataset(ds_path=None, ds=ds) as wps_ds:
        classified = np.select([wps_ds < 4000, wps_ds < 10000], [0, 1], default=2)

        assert np.array_equal(classified, np.array([[0, 1], [2, 0]]))
        read_spy.assert_called_once()


def test_from_array_disk_backed_via_output_path():
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "from_array.tif")
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)

        result = WPSDataset.from_array(
            np.array([[7, 7], [7, 7]], dtype=np.uint8),
            Georeference((0, 1, 0, 0, 0, -1), srs.ExportToWkt()),
            datatype=gdal.GDT_Byte,
            output_path=output_path,
        )
        assert result.as_gdal_ds().GetDriver().ShortName == "GTiff"

        assert os.path.exists(output_path)
        with WPSDataset(output_path) as reopened:
            assert np.all(reopened.as_gdal_ds().GetRasterBand(1).ReadAsArray() == 7)


def test_raster_mul_wrong_dimensions():
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    wgs_84_ds1 = create_test_dataset("test_dataset_1.tif", 1, 1, extent, 4326)
    wgs_84_ds2 = create_test_dataset("test_dataset_2.tif", 2, 2, extent, 4326)

    with pytest.raises(ValueError):
        with (
            WPSDataset(ds_path=None, ds=wgs_84_ds1) as wps1_ds,
            WPSDataset(ds_path=None, ds=wgs_84_ds2) as wps2_ds,
        ):
            _ = wps1_ds * wps2_ds

    wgs_84_ds1 = None
    wgs_84_ds2 = None


def test_raster_mul_wrong_projections():
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    wgs_84_ds = create_test_dataset("test_dataset_1.tif", 1, 1, extent, 4326)
    mercator_ds = create_test_dataset("test_dataset_2.tif", 1, 1, extent, 3857)

    with pytest.raises(ValueError):
        with (
            WPSDataset(ds_path=None, ds=wgs_84_ds) as wps1_ds,
            WPSDataset(ds_path=None, ds=mercator_ds) as wps2_ds,
        ):
            _ = wps1_ds * wps2_ds

    wgs_84_ds = None
    mercator_ds = None


def test_raster_mul_wrong_origins():
    extent1 = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    wgs_84_ds1 = create_test_dataset("test_dataset_1.tif", 1, 1, extent1, 4326)
    extent2 = (-2, 2, -2, 2)  # xmin, xmax, ymin, ymax
    wgs_84_ds2 = create_test_dataset("test_dataset_2.tif", 1, 1, extent2, 4326)

    with pytest.raises(ValueError):
        with (
            WPSDataset(ds_path=None, ds=wgs_84_ds1) as wps1_ds,
            WPSDataset(ds_path=None, ds=wgs_84_ds2) as wps2_ds,
        ):
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

    with (
        WPSDataset(ds_path=None, ds=wgs_84_ds) as wps1_ds,
        WPSDataset(ds_path=None, ds=mercator_ds) as wps2_ds,
    ):
        output_ds: WPSDataset = wps1_ds.warp_to_match(wps2_ds, "/vsimem/test.tif")
        assert output_ds.as_gdal_ds().GetProjection() == wps2_ds.as_gdal_ds().GetProjection()
        assert output_ds.as_gdal_ds().GetGeoTransform() == wps2_ds.as_gdal_ds().GetGeoTransform()
        assert output_ds.as_gdal_ds().RasterXSize == wps2_ds.as_gdal_ds().RasterXSize
        assert output_ds.as_gdal_ds().RasterYSize == wps2_ds.as_gdal_ds().RasterYSize


def test_close_is_a_noop_for_mem_driver_dataset_with_no_real_backing_file():
    """A MEM-driver dataset can be named with a /vsimem/-looking path but MEM never
    registers a real VSI file there, so GetFileList() is None and close() has nothing to do."""
    mem_ds = gdal.GetDriverByName("MEM").Create("/vsimem/no_such_file.tif", 2, 2, 1)
    assert mem_ds.GetFileList() is None

    with WPSDataset(ds_path=None, ds=mem_ds) as wps_ds:
        wps_ds.close()  # no-op, must not raise


def test_close_unlinks_vsimem_file_even_when_referenced_via_mem_driver_dataset():
    """If a /vsimem/ file genuinely exists at the path a MEM-driver dataset happens to be named
    after, gdal's own GetFileList() reports it and close() unlinks it automatically, same as
    for a real GTiff-on-vsimem result. WPSDataset doesn't special-case the driver."""
    vsimem_path = "/vsimem/masked_fuel_type_1.tif"
    real_ds = gdal.GetDriverByName("GTiff").Create(vsimem_path, 2, 2, 1)
    del real_ds  # drop the only reference to close/flush the GTiff onto the vsimem filesystem
    assert gdal.VSIStatL(vsimem_path) is not None

    mem_ds = gdal.GetDriverByName("MEM").Create(vsimem_path, 2, 2, 1)
    with WPSDataset(ds_path=None, ds=mem_ds) as wps_ds:
        wps_ds.close()

    assert gdal.VSIStatL(vsimem_path) is None  # unlinked automatically


def test_clip_to_geometry_with_ogr_geometry():
    # 10x10 px, 2 units/px, covering (-10,-10) to (10,10). Cutline (-5,-5)-(5,5) keeps only the
    # 4 columns/rows whose pixel centres (-3,-1,1,3) fall strictly inside it - GDAL excludes the
    # ring of pixels centred exactly on the cutline edge (-5 and 5) - giving a 4x4 result
    # anchored at (-4, 4) with the source's original 2-unit pixel size preserved.
    extent = (-10, 10, -10, 10)  # xmin, xmax, ymin, ymax
    ds = create_test_dataset(
        "test_dataset_1.tif", 10, 10, extent, 4326, data_type=gdal.GDT_Byte, fill_value=7
    )

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    cutline = ogr.CreateGeometryFromWkt("POLYGON((-5 -5, 5 -5, 5 5, -5 5, -5 -5))")
    cutline.AssignSpatialReference(srs)

    with WPSDataset(ds_path=None, ds=ds) as wps_ds:
        clipped = wps_ds.clip_to_geometry(cutline)
        raw = clipped.as_gdal_ds()

        assert (raw.RasterXSize, raw.RasterYSize) == (4, 4)
        assert raw.GetGeoTransform() == (-4.0, 2.0, 0.0, 4.0, 0.0, -2.0)
        assert np.array_equal(raw.GetRasterBand(1).ReadAsArray(), np.full((4, 4), 7))


def test_clip_to_geometry_unlinks_vsimem_output_on_close():
    extent = (-10, 10, -10, 10)  # xmin, xmax, ymin, ymax
    ds = create_test_dataset(
        "test_dataset_1.tif", 10, 10, extent, 4326, data_type=gdal.GDT_Byte, fill_value=7
    )

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    cutline = ogr.CreateGeometryFromWkt("POLYGON((-5 -5, 5 -5, 5 5, -5 5, -5 -5))")
    cutline.AssignSpatialReference(srs)

    with WPSDataset(ds_path=None, ds=ds) as wps_ds:
        clipped = wps_ds.clip_to_geometry(cutline)  # no output_path -> auto /vsimem/ path
        vsimem_path = clipped.as_gdal_ds().GetFileList()[0]

        assert vsimem_path.startswith("/vsimem/")
        assert gdal.VSIStatL(vsimem_path) is not None  # backing file exists while open

        clipped.close()

        assert gdal.VSIStatL(vsimem_path) is None  # gdal.Unlink'd automatically


def test_clip_to_geometry_does_not_unlink_real_output_path():
    extent = (-10, 10, -10, 10)  # xmin, xmax, ymin, ymax
    ds = create_test_dataset(
        "test_dataset_1.tif", 10, 10, extent, 4326, data_type=gdal.GDT_Byte, fill_value=7
    )

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    cutline = ogr.CreateGeometryFromWkt("POLYGON((-5 -5, 5 -5, 5 5, -5 5, -5 -5))")
    cutline.AssignSpatialReference(srs)

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "clipped.tif")

        with WPSDataset(ds_path=None, ds=ds) as wps_ds:
            clipped = wps_ds.clip_to_geometry(cutline, output_path=output_path)
            assert clipped.as_gdal_ds().GetFileList() == [output_path]

            clipped.close()

        assert os.path.exists(output_path)  # real files are left alone by close()


def test_clip_to_geometry_with_vector_file_path():
    # Same source raster and cutline extent as test_clip_to_geometry_with_ogr_geometry, so the
    # same 4x4 result at (-4, 4) is expected - this exercises the cutlineDSName branch instead.
    extent = (-10, 10, -10, 10)  # xmin, xmax, ymin, ymax
    ds = create_test_dataset(
        "test_dataset_1.tif", 10, 10, extent, 4326, data_type=gdal.GDT_Byte, fill_value=3
    )

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]]],
                },
            }
        ],
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        cutline_path = os.path.join(temp_dir, "cutline.geojson")
        with open(cutline_path, "w") as f:
            json.dump(geojson, f)

        output_path = os.path.join(temp_dir, "clipped.tif")

        with WPSDataset(ds_path=None, ds=ds) as wps_ds:
            clipped = wps_ds.clip_to_geometry(cutline_path, output_path=output_path)
            raw = clipped.as_gdal_ds()

            assert (raw.RasterXSize, raw.RasterYSize) == (4, 4)
            assert raw.GetGeoTransform() == (-4.0, 2.0, 0.0, 4.0, 0.0, -2.0)
            assert np.array_equal(raw.GetRasterBand(1).ReadAsArray(), np.full((4, 4), 3))

        assert os.path.exists(output_path)


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

    with (
        WPSDataset(ds_path=None, ds=wgs_84_ds) as wps1_ds,
        WPSDataset(ds_path=None, ds=mercator_ds) as wps2_ds,
    ):
        output_ds: WPSDataset = wps1_ds.warp_to_match(
            wps2_ds, "/vsimem/test.grib2", max_value=100
        )  # test that we can update an output path with any extension
        out_array = output_ds.as_gdal_ds().GetRasterBand(1).ReadAsArray()
        assert out_array.max() == 100

        # Ensure 90 stayed 90 everywhere since we're doing Nearest Neighbour interp. 100*100 array minus the 1 value we changed
        assert np.count_nonzero(out_array == 90) == (100 * 100 - 1), (
            "Expected at least one value to remain 99"
        )

    wgs_84_ds = None
    mercator_ds = None


def test_export_to_geotiff():
    extent1 = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    ds_1 = create_test_dataset(
        "test_dataset_1.tif", 3, 3, extent1, 4326, data_type=gdal.GDT_Byte, fill_value=1
    )
    source_band = ds_1.GetRasterBand(1)
    source_band.SetDescription("surface_fuel_consumption")
    source_band.SetUnitType("kg/m2")

    with WPSDataset(ds_path=None, ds=ds_1) as wps_ds:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "test_export.tif")
            wps_ds.export_to_geotiff(temp_path)

            with WPSDataset(ds_path=temp_path) as exported_ds:
                assert (
                    wps_ds.as_gdal_ds().GetProjection() == exported_ds.as_gdal_ds().GetProjection()
                )
                assert (
                    wps_ds.as_gdal_ds().GetGeoTransform()
                    == exported_ds.as_gdal_ds().GetGeoTransform()
                )
                assert wps_ds.as_gdal_ds().RasterXSize == exported_ds.as_gdal_ds().RasterXSize
                assert wps_ds.as_gdal_ds().RasterYSize == exported_ds.as_gdal_ds().RasterYSize

                original_values = wps_ds.as_gdal_ds().GetRasterBand(1).ReadAsArray()
                exported_band = exported_ds.as_gdal_ds().GetRasterBand(1)
                exported_values = exported_band.ReadAsArray()
                assert np.all(original_values == exported_values) == True
                assert exported_band.GetDescription() == "surface_fuel_consumption"
                assert exported_band.GetUnitType() == "kg/m2"

    ds_1 = None


def test_latitude_array():
    lats_3005_tif = os.path.join(os.path.dirname(__file__), "3005_lats.tif")
    lats_4326_tif = os.path.join(os.path.dirname(__file__), "4326_lats.tif")
    with (
        WPSDataset(ds_path=lats_3005_tif) as lats_3005_ds,
        WPSDataset(ds_path=lats_4326_tif) as lats_4326_ds,
    ):
        output_ds: WPSDataset = lats_3005_ds.warp_to_match(lats_4326_ds, "/vsimem/test_lats.tif")
        original_ds = gdal.Open(lats_4326_tif)
        original_lats = original_ds.GetRasterBand(1).ReadAsArray()
        warped_lats = output_ds.generate_latitude_array()
        assert np.all(original_lats == warped_lats) == True
        output_ds = None


def test_get_nodata_mask():
    set_no_data_value = 0
    driver: gdal.Driver = gdal.GetDriverByName("MEM")
    dataset: gdal.Dataset = driver.Create(
        "test_dataset_no_data_value.tif", 2, 2, 1, eType=gdal.GDT_Int32
    )
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
    original_ds = create_test_dataset(
        "test_dataset_1.tif", 100, 100, extent1, 4326
    )  # float32 datatype
    original_ds.GetRasterBand(1).SetNoDataValue(-99)
    og_band = original_ds.GetRasterBand(1)
    og_array = og_band.ReadAsArray()
    dtype = og_band.DataType
    og_transform = original_ds.GetGeoTransform()
    og_proj = original_ds.GetProjection()

    with WPSDataset.from_array(
        og_array, Georeference(og_transform, og_proj), nodata_value=-99, datatype=dtype
    ) as wps:
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


class TestGetLatLonCoords:
    """Tests for get_lat_lon_coords method."""

    def test_wgs84_coords_returned_correctly(self):
        """Test that WGS84 dataset returns correct lat/lon coordinates."""
        # Create a simple 2x2 WGS84 dataset centered at (0, 0)
        # Extent: lon -1 to 1, lat -1 to 1
        extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
        ds = create_test_dataset("test_wgs84.tif", 2, 2, extent, 4326)

        with WPSDataset(ds_path=None, ds=ds) as wps_ds:
            lats, lons, yi, xi = wps_ds.get_lat_lon_coords()

            # Should have 4 pixels (2x2)
            assert len(lats) == 4
            assert len(lons) == 4
            assert len(yi) == 4
            assert len(xi) == 4

            # Pixel centers should be at -0.5 and 0.5 for both dimensions
            assert np.allclose(np.sort(np.unique(lons)), [-0.5, 0.5], atol=0.01)
            assert np.allclose(np.sort(np.unique(lats)), [-0.5, 0.5], atol=0.01)

    def test_with_valid_mask(self):
        """Test that valid_mask filters pixels correctly."""
        extent = (-1, 1, -1, 1)
        ds = create_test_dataset("test_mask.tif", 2, 2, extent, 4326)

        with WPSDataset(ds_path=None, ds=ds) as wps_ds:
            # Only include top-left pixel
            valid_mask = np.array([[True, False], [False, False]])
            lats, lons, yi, xi = wps_ds.get_lat_lon_coords(valid_mask)

            assert len(lats) == 1
            assert len(lons) == 1
            assert yi[0] == 0
            assert xi[0] == 0

    def test_with_nodata_mask(self):
        """Test that nodata values are automatically masked."""
        driver = gdal.GetDriverByName("MEM")
        ds = driver.Create("test_nodata.tif", 2, 2, 1, gdal.GDT_Float32)

        # Set geotransform and projection for WGS84
        ds.SetGeoTransform((-1, 1, 0, 1, 0, -1))
        from osgeo import osr

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        ds.SetProjection(srs.ExportToWkt())

        # Set nodata and write data with one nodata pixel
        band = ds.GetRasterBand(1)
        band.SetNoDataValue(-9999)
        data = np.array([[1.0, 2.0], [-9999, 4.0]], dtype=np.float32)
        band.WriteArray(data)

        with WPSDataset(ds_path=None, ds=ds) as wps_ds:
            lats, lons, yi, xi = wps_ds.get_lat_lon_coords()

            # Should only have 3 valid pixels (one is nodata)
            assert len(lats) == 3
            assert len(lons) == 3

            # The nodata pixel (1, 0) should not be included
            indices = list(zip(yi, xi))
            assert (1, 0) not in indices

    def test_projected_coords_transformed(self):
        """Test that non-WGS84 coordinates are transformed to WGS84."""
        # Create dataset in Web Mercator (EPSG:3857) near Vancouver
        # Vancouver in 3857: approximately x=-13700000, y=6300000
        extent = (-13750000, -13650000, 6250000, 6350000)
        ds = create_test_dataset("test_3857.tif", 2, 2, extent, 3857)

        with WPSDataset(ds_path=None, ds=ds) as wps_ds:
            lats, lons, _, _ = wps_ds.get_lat_lon_coords()

            # Should have 4 pixels
            assert len(lats) == 4

            # Coordinates should be transformed to WGS84
            # Vancouver is roughly lat 49, lon -123
            assert all(48 < lat < 52 for lat in lats)
            assert all(-125 < lon < -120 for lon in lons)

    def test_indices_match_mask(self):
        """Test that returned indices correctly correspond to mask positions."""
        extent = (-1, 1, -1, 1)
        ds = create_test_dataset("test_indices.tif", 3, 3, extent, 4326)

        with WPSDataset(ds_path=None, ds=ds) as wps_ds:
            # Create checkerboard mask
            valid_mask = np.array(
                [
                    [True, False, True],
                    [False, True, False],
                    [True, False, True],
                ]
            )
            lats, _, yi, xi = wps_ds.get_lat_lon_coords(valid_mask)

            # Should have 5 valid pixels
            assert len(lats) == 5

            # Verify indices match the True positions in mask
            indices = set(zip(yi, xi))
            expected = {(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)}
            assert indices == expected

    def test_empty_mask_returns_empty_arrays(self):
        """Test that all-False mask returns empty arrays."""
        extent = (-1, 1, -1, 1)
        ds = create_test_dataset("test_empty.tif", 2, 2, extent, 4326)

        with WPSDataset(ds_path=None, ds=ds) as wps_ds:
            valid_mask = np.zeros((2, 2), dtype=bool)
            lats, lons, yi, xi = wps_ds.get_lat_lon_coords(valid_mask)

            assert len(lats) == 0
            assert len(lons) == 0
            assert len(yi) == 0
            assert len(xi) == 0


class TestExtractValueAtPoint:
    """Tests for WPSDataset.extract_value_at_point."""

    # 10x10 WGS84 raster covering lon -130..-120, lat 49..59; each pixel is 1 degree
    _EXTENT = (-130, -120, 49, 59)

    def test_returns_value_at_valid_point(self):
        gdal_ds = create_test_dataset("test.tif", 10, 10, self._EXTENT, 4326, fill_value=42.0)
        with WPSDataset(ds_path=None, ds=gdal_ds) as ds:
            assert ds.extract_value_at_point(lat=53.5, lon=-125.5) == pytest.approx(42.0)

    def test_returns_none_when_point_outside_raster(self):
        gdal_ds = create_test_dataset("test.tif", 10, 10, self._EXTENT, 4326, fill_value=1.0)
        with WPSDataset(ds_path=None, ds=gdal_ds) as ds:
            assert ds.extract_value_at_point(lat=0.0, lon=0.0) is None

    def test_returns_none_when_point_fractionally_outside_raster(self):
        """A point just past the raster's edge must not be truncated into bounds.

        Regression test: the pixel coordinate here computes to a small negative
        number (e.g. -0.0005). int() truncation rounds that toward zero into column
        0 (wrongly in-bounds); floor() correctly keeps it negative and out of bounds.
        """
        gdal_ds = create_test_dataset("test.tif", 10, 10, self._EXTENT, 4326, fill_value=99.0)
        with WPSDataset(ds_path=None, ds=gdal_ds) as ds:
            assert ds.extract_value_at_point(lat=53.5, lon=-130.0005) is None

    def test_returns_none_when_pixel_is_nodata(self):
        gdal_ds = create_test_dataset(
            "test.tif", 10, 10, self._EXTENT, 4326, fill_value=1.0, no_data_value=-9999.0
        )
        gdal_ds.GetRasterBand(1).WriteArray(np.array([[-9999.0]], dtype=np.float32), xoff=4, yoff=5)
        with WPSDataset(ds_path=None, ds=gdal_ds) as ds:
            assert ds.extract_value_at_point(lat=53.5, lon=-125.5) is None

    def test_returns_value_at_corner_pixel(self):
        gdal_ds = create_test_dataset("test.tif", 10, 10, self._EXTENT, 4326, fill_value=7.0)
        with WPSDataset(ds_path=None, ds=gdal_ds) as ds:
            assert ds.extract_value_at_point(lat=58.5, lon=-129.5) == pytest.approx(7.0)


class TestApplyMask:
    """Tests for WPSDataset.apply_mask method."""

    def test_basic_mask_application_matching_grids(self):
        """Test mask application when grids match exactly."""
        extent = (-1, 1, -1, 1)

        # Create reference dataset
        ref_gdal_ds = create_test_dataset("ref.tif", 3, 3, extent, 4326)

        # Create mask dataset with same grid - center pixel masked (0)
        mask_gdal_ds = create_test_dataset("mask.tif", 3, 3, extent, 4326)
        mask_data = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.float32)
        mask_gdal_ds.GetRasterBand(1).WriteArray(mask_data)

        with WPSDataset(ds_path=None, ds=ref_gdal_ds) as ref_ds:
            with WPSDataset(ds_path=None, ds=mask_gdal_ds) as mask_ds:
                result = ref_ds.apply_mask(mask_ds)

                assert result.shape == (3, 3)
                assert result[1, 1] == False  # Center pixel masked
                assert np.sum(result) == 8  # 8 valid pixels

    def test_mask_with_nodata_matching_grids(self):
        """Test mask application with nodata values when grids match."""
        extent = (-1, 1, -1, 1)

        ref_gdal_ds = create_test_dataset("ref.tif", 3, 3, extent, 4326)

        mask_gdal_ds = create_test_dataset("mask.tif", 3, 3, extent, 4326)
        mask_data = np.array([[1, 1, -9999], [1, 0, 1], [1, 1, 1]], dtype=np.float32)
        mask_gdal_ds.GetRasterBand(1).WriteArray(mask_data)
        mask_gdal_ds.GetRasterBand(1).SetNoDataValue(-9999)

        with WPSDataset(ds_path=None, ds=ref_gdal_ds) as ref_ds:
            with WPSDataset(ds_path=None, ds=mask_gdal_ds) as mask_ds:
                result = ref_ds.apply_mask(mask_ds)

                assert result[1, 1] == False  # Zero value masked
                assert result[0, 2] == False  # Nodata value masked
                assert np.sum(result) == 7

    def test_all_valid_mask(self):
        """Test when entire mask is valid."""
        extent = (-1, 1, -1, 1)

        ref_gdal_ds = create_test_dataset("ref.tif", 3, 3, extent, 4326)
        mask_gdal_ds = create_test_dataset("mask.tif", 3, 3, extent, 4326, fill_value=1)

        with WPSDataset(ds_path=None, ds=ref_gdal_ds) as ref_ds:
            with WPSDataset(ds_path=None, ds=mask_gdal_ds) as mask_ds:
                result = ref_ds.apply_mask(mask_ds)

                assert np.all(result)
                assert np.sum(result) == 9

    def test_all_masked(self):
        """Test when entire mask is masked (all zeros)."""
        extent = (-1, 1, -1, 1)

        ref_gdal_ds = create_test_dataset("ref.tif", 3, 3, extent, 4326)
        mask_gdal_ds = create_test_dataset("mask.tif", 3, 3, extent, 4326, fill_value=0)

        with WPSDataset(ds_path=None, ds=ref_gdal_ds) as ref_ds:
            with WPSDataset(ds_path=None, ds=mask_gdal_ds) as mask_ds:
                result = ref_ds.apply_mask(mask_ds)

                assert not np.any(result)
                assert np.sum(result) == 0

    def test_raises_when_grids_differ(self):
        """Test that apply_mask raises ValueError when grids don't match."""
        ref_extent = (-1, 1, -1, 1)
        mask_extent = (-2, 2, -2, 2)

        ref_gdal_ds = create_test_dataset("ref.tif", 4, 4, ref_extent, 4326)
        mask_gdal_ds = create_test_dataset("mask.tif", 8, 8, mask_extent, 4326, fill_value=1)

        with WPSDataset(ds_path=None, ds=ref_gdal_ds) as ref_ds:
            with WPSDataset(ds_path=None, ds=mask_gdal_ds) as mask_ds:
                with pytest.raises(ValueError, match="Mask grid does not match reference grid"):
                    ref_ds.apply_mask(mask_ds)
