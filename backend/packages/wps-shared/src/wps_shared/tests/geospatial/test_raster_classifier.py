"""Tests for windowed raster classification."""

import numpy as np
import pytest
from osgeo import gdal

from wps_shared.geospatial.raster_classifier import (
    NODATA_LABEL,
    ClassRule,
    TileConfig,
    WindowedRasterClassifier,
    hfi_classify_rules,
    snow_classify_rules,
)


def write_geotiff(path: str, array: np.ndarray, nodata: float | None = None) -> None:
    """Write a small single-band GeoTIFF for use as classifier input."""
    height, width = array.shape
    driver = gdal.GetDriverByName("GTiff")
    ds = driver.Create(path, width, height, 1, gdal.GDT_Float32)
    ds.SetGeoTransform((-120.0, 1.0, 0, 55.0, 0, -1.0))
    ds.SetProjection(
        'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
    )
    band = ds.GetRasterBand(1)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    band.WriteArray(array.astype(np.float32))
    band.FlushCache()
    ds = None


@pytest.fixture
def classifier(tmp_path):
    input_path = str(tmp_path / "input.tif")
    output_path = str(tmp_path / "output.tif")
    return WindowedRasterClassifier(input_path, output_path, hfi_classify_rules())


class TestClassifyRuleFactories:
    def test_hfi_rules_cover_full_range_with_no_gaps_or_overlaps(self):
        rules = hfi_classify_rules()
        rules_sorted = sorted(rules, key=lambda r: r.min_val)
        assert rules_sorted[0].min_val == float("-inf")
        assert rules_sorted[-1].max_val == float("inf")
        for prev, nxt in zip(rules_sorted, rules_sorted[1:]):
            assert prev.max_val == nxt.min_val

    def test_snow_rules_labels_and_bounds(self):
        rules = {r.name: r for r in snow_classify_rules()}
        assert rules["snow_covered"].min_val == 10
        assert rules["snow_covered"].max_val == 100
        assert rules["snow_free"].max_val == 10


class TestClassifyArray:
    def test_basic_classification_into_bins(self, classifier):
        data = np.array([[100.0, 5000.0], [15000.0, 3999.0]])
        out = classifier.classify_array(data, hfi_classify_rules())
        assert out.dtype == np.uint8
        np.testing.assert_array_equal(out, np.array([[0, 1], [2, 0]]))

    def test_min_val_is_inclusive(self, classifier):
        data = np.array([[4000.0, 10000.0]])
        out = classifier.classify_array(data, hfi_classify_rules())
        # 4000 belongs to "above_4000" (min inclusive), 10000 belongs to "above_10000"
        np.testing.assert_array_equal(out, np.array([[1, 2]]))

    def test_max_val_is_exclusive(self, classifier):
        data = np.array([[3999.999, 9999.999]])
        out = classifier.classify_array(data, hfi_classify_rules())
        np.testing.assert_array_equal(out, np.array([[0, 1]]))

    def test_explicit_nodata_value_masked_to_sentinel(self, classifier):
        data = np.array([[-9999.0, 5000.0]])
        out = classifier.classify_array(data, hfi_classify_rules(), nodata=-9999.0)
        np.testing.assert_array_equal(out, np.array([[NODATA_LABEL, 1]]))

    def test_nan_masked_even_without_explicit_nodata(self, classifier):
        data = np.array([[np.nan, 5000.0]])
        out = classifier.classify_array(data, hfi_classify_rules(), nodata=None)
        np.testing.assert_array_equal(out, np.array([[NODATA_LABEL, 1]]))

    def test_nan_masked_alongside_explicit_nodata(self, classifier):
        data = np.array([[np.nan, -9999.0, 5000.0]])
        out = classifier.classify_array(data, hfi_classify_rules(), nodata=-9999.0)
        np.testing.assert_array_equal(out, np.array([[NODATA_LABEL, NODATA_LABEL, 1]]))

    def test_nodata_sentinel_distinct_from_label_zero_class(self, classifier):
        """A real label-0 class pixel (below_4000) and a nodata pixel must not collide."""
        data = np.array([[100.0, -9999.0]])  # 100 -> below_4000 (label 0), -9999 -> nodata
        out = classifier.classify_array(data, hfi_classify_rules(), nodata=-9999.0)
        np.testing.assert_array_equal(out, np.array([[0, NODATA_LABEL]]))

    def test_rejects_rule_label_colliding_with_nodata_sentinel(self, classifier):
        rules = [ClassRule(NODATA_LABEL, "bad", 0, 10)]
        with pytest.raises(AssertionError):
            classifier.classify_array(np.array([[5.0]]), rules)

    def test_value_matching_no_rule_stays_default_zero(self, classifier):
        # rules only cover [0, 10); 20 falls outside every rule's range
        rules = [ClassRule(1, "low", 0, 10)]
        data = np.array([[5.0, 20.0]])
        out = classifier.classify_array(data, rules)
        np.testing.assert_array_equal(out, np.array([[1, 0]]))

    def test_overlapping_rules_last_match_wins(self, classifier):
        rules = [ClassRule(1, "first", 0, 100), ClassRule(2, "second", 50, 100)]
        data = np.array([[75.0]])
        out = classifier.classify_array(data, rules)
        assert out[0, 0] == 2

    def test_empty_rules_yields_all_zero(self, classifier):
        data = np.array([[1.0, 2.0], [3.0, 4.0]])
        out = classifier.classify_array(data, [])
        assert np.all(out == 0)

    def test_output_shape_matches_input(self, classifier):
        data = np.zeros((3, 7))
        out = classifier.classify_array(data, hfi_classify_rules())
        assert out.shape == (3, 7)


class TestClassifyRasterSingleTile:
    def test_writes_output_matching_classified_values(self, tmp_path):
        data = np.array(
            [
                [100.0, 5000.0, 15000.0],
                [3999.0, 4000.0, 9999.0],
            ]
        )
        input_path = str(tmp_path / "input.tif")
        output_path = str(tmp_path / "output.tif")
        write_geotiff(input_path, data)

        clf = WindowedRasterClassifier(input_path, output_path, hfi_classify_rules())
        clf.classify_raster(hfi_classify_rules())

        out_ds = gdal.Open(output_path)
        out_arr = out_ds.GetRasterBand(1).ReadAsArray()
        out_ds = None

        expected = np.array([[0, 1, 2], [0, 1, 1]], dtype=np.uint8)
        np.testing.assert_array_equal(out_arr, expected)

    def test_summary_counts_and_percentages(self, tmp_path):
        data = np.array([[5000.0, 5000.0, 15000.0, 15000.0]])  # 2 above_4000, 2 above_10000
        input_path = str(tmp_path / "input.tif")
        output_path = str(tmp_path / "output.tif")
        write_geotiff(input_path, data)

        clf = WindowedRasterClassifier(input_path, output_path, hfi_classify_rules())
        summary = clf.classify_raster(hfi_classify_rules())

        by_name = summary.set_index("class_name")
        assert by_name.loc["nodata", "pixel_count"] == 0
        assert by_name.loc["below_4000", "pixel_count"] == 0
        assert by_name.loc["above_4000", "pixel_count"] == 2
        assert by_name.loc["above_10000", "pixel_count"] == 2
        assert pytest.approx(summary["pct"].sum(), abs=0.02) == 100.0

    def test_label_zero_class_distinguished_from_nodata_in_summary(self, tmp_path):
        """A real "below_4000" (label 0) pixel must not be counted as nodata, and
        vice versa - the summary's "nodata" row must only reflect true nodata pixels."""
        data = np.array([[-9999.0, 100.0, 100.0]])  # 1 nodata pixel, 2 real "below_4000" pixels
        input_path = str(tmp_path / "input.tif")
        output_path = str(tmp_path / "output.tif")
        write_geotiff(input_path, data, nodata=-9999.0)

        clf = WindowedRasterClassifier(input_path, output_path, hfi_classify_rules())
        summary = clf.classify_raster(hfi_classify_rules())

        by_name = summary.set_index("class_name")
        assert by_name.loc["nodata", "pixel_count"] == 1
        assert by_name.loc["below_4000", "pixel_count"] == 2

    def test_nodata_pixels_labeled_sentinel_and_counted(self, tmp_path):
        data = np.array([[-9999.0, -9999.0, 5000.0]])
        input_path = str(tmp_path / "input.tif")
        output_path = str(tmp_path / "output.tif")
        write_geotiff(input_path, data, nodata=-9999.0)

        clf = WindowedRasterClassifier(input_path, output_path, hfi_classify_rules())
        summary = clf.classify_raster(hfi_classify_rules())

        by_name = summary.set_index("class_name")
        assert by_name.loc["nodata", "pixel_count"] == 2
        assert by_name.loc["above_4000", "pixel_count"] == 1

        out_ds = gdal.Open(output_path)
        band = out_ds.GetRasterBand(1)
        assert band.GetNoDataValue() == NODATA_LABEL
        out_arr = band.ReadAsArray()
        out_ds = None
        assert (out_arr == NODATA_LABEL).sum() == 2

    def test_missing_input_raises(self, tmp_path):
        # With gdal.UseExceptions() active, gdal.Open() raises RuntimeError itself
        # for a missing file - see test_open_returning_none_raises_file_not_found
        # for the `if src_ds is None: raise FileNotFoundError` branch below it.
        clf = WindowedRasterClassifier(
            str(tmp_path / "does_not_exist.tif"), str(tmp_path / "output.tif"), hfi_classify_rules()
        )
        with pytest.raises(RuntimeError):
            clf.classify_raster(hfi_classify_rules())

    def test_open_returning_none_raises_file_not_found(self, tmp_path, mocker):
        # gdal.Open() returning None (rather than raising) is possible in principle
        # even with UseExceptions() active - e.g. an unreadable/unsupported format
        # that GDAL declines without erroring. Force that path directly.
        input_path = str(tmp_path / "input.tif")
        clf = WindowedRasterClassifier(input_path, str(tmp_path / "output.tif"), hfi_classify_rules())
        mocker.patch("wps_shared.geospatial.raster_classifier.gdal.Open", return_value=None)

        with pytest.raises(FileNotFoundError) as exc_info:
            clf.classify_raster(hfi_classify_rules())
        assert input_path in str(exc_info.value)

    def test_output_georeference_matches_input(self, tmp_path):
        data = np.zeros((4, 4))
        input_path = str(tmp_path / "input.tif")
        output_path = str(tmp_path / "output.tif")
        write_geotiff(input_path, data)

        clf = WindowedRasterClassifier(input_path, output_path, hfi_classify_rules())
        clf.classify_raster(hfi_classify_rules())

        src_ds = gdal.Open(input_path)
        out_ds = gdal.Open(output_path)
        assert out_ds.GetGeoTransform() == src_ds.GetGeoTransform()
        assert out_ds.GetProjection() == src_ds.GetProjection()
        assert out_ds.RasterXSize == src_ds.RasterXSize
        assert out_ds.RasterYSize == src_ds.RasterYSize
        src_ds = None
        out_ds = None

    def test_output_is_tiled_geotiff(self, tmp_path):
        data = np.zeros((4, 4))
        input_path = str(tmp_path / "input.tif")
        output_path = str(tmp_path / "output.tif")
        write_geotiff(input_path, data)

        clf = WindowedRasterClassifier(input_path, output_path, hfi_classify_rules())
        clf.classify_raster(hfi_classify_rules())

        out_ds = gdal.Open(output_path)
        assert out_ds.GetDriver().ShortName == "GTiff"
        assert out_ds.GetRasterBand(1).DataType == gdal.GDT_Byte
        metadata = out_ds.GetMetadata("IMAGE_STRUCTURE")
        assert metadata.get("COMPRESSION") == "LZW"
        out_ds = None


class TestClassifyRasterMultipleTiles:
    def test_tiling_matches_single_tile_result(self, tmp_path):
        """Classifying with small tiles should give the same result as one big tile."""
        rng = np.random.default_rng(seed=7)
        data = rng.uniform(0, 20000, size=(10, 10))

        input_path = str(tmp_path / "input.tif")
        write_geotiff(input_path, data)

        whole_output = str(tmp_path / "whole.tif")
        clf_whole = WindowedRasterClassifier(
            input_path,
            whole_output,
            hfi_classify_rules(),
            config=TileConfig(tile_width=100, tile_height=100),
        )
        summary_whole = clf_whole.classify_raster(
            hfi_classify_rules(), config=TileConfig(tile_width=100, tile_height=100)
        )

        tiled_output = str(tmp_path / "tiled.tif")
        clf_tiled = WindowedRasterClassifier(input_path, tiled_output, hfi_classify_rules())
        summary_tiled = clf_tiled.classify_raster(
            hfi_classify_rules(), config=TileConfig(tile_width=3, tile_height=4)
        )

        whole_ds = gdal.Open(whole_output)
        tiled_ds = gdal.Open(tiled_output)
        whole_arr = whole_ds.GetRasterBand(1).ReadAsArray()
        tiled_arr = tiled_ds.GetRasterBand(1).ReadAsArray()
        np.testing.assert_array_equal(whole_arr, tiled_arr)
        whole_ds = None
        tiled_ds = None

        pandas_summary_whole = summary_whole.set_index("class_name")["pixel_count"]
        pandas_summary_tiled = summary_tiled.set_index("class_name")["pixel_count"]
        assert pandas_summary_whole.equals(pandas_summary_tiled)

    def test_pixel_counts_sum_to_raster_size_for_uneven_tiles(self, tmp_path):
        """Raster dims not evenly divisible by tile size must still classify every pixel exactly once."""
        data = np.full((7, 5), 5000.0)  # all "above_4000"
        input_path = str(tmp_path / "input.tif")
        output_path = str(tmp_path / "output.tif")
        write_geotiff(input_path, data)

        clf = WindowedRasterClassifier(input_path, output_path, hfi_classify_rules())
        summary = clf.classify_raster(
            hfi_classify_rules(), config=TileConfig(tile_width=3, tile_height=3)
        )

        assert summary["pixel_count"].sum() == 7 * 5
        by_name = summary.set_index("class_name")
        assert by_name.loc["above_4000", "pixel_count"] == 7 * 5

        out_ds = gdal.Open(output_path)
        assert out_ds.GetRasterBand(1).ReadAsArray().size == 7 * 5
        out_ds = None
