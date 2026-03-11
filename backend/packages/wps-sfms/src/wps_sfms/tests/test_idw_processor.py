import numpy as np

from wps_sfms.processors.idw import idw_on_valid_pixels


class TestIdwOnValidPixels:
    def test_all_pixels_interpolate_successfully(self, monkeypatch):
        # Verifies the full success path: all returned values are valid and
        # are indexed back to the original valid pixel row/col arrays.
        valid_lats = np.array([49.0, 49.1, 49.2], dtype=np.float32)
        valid_lons = np.array([-123.0, -123.1, -123.2], dtype=np.float32)
        valid_yi = np.array([1, 3, 4], dtype=np.intp)
        valid_xi = np.array([2, 0, 5], dtype=np.intp)
        station_lats = np.array([49.05, 49.15], dtype=np.float32)
        station_lons = np.array([-123.05, -123.15], dtype=np.float32)
        station_values = np.array([10.0, 20.0], dtype=np.float32)

        def fake_idw_interpolation(*args):
            assert len(args) == 5
            return np.array([1.5, 2.5, 3.5], dtype=np.float64)

        monkeypatch.setattr("wps_sfms.processors.idw.idw_interpolation", fake_idw_interpolation)

        result = idw_on_valid_pixels(
            valid_lats=valid_lats,
            valid_lons=valid_lons,
            valid_yi=valid_yi,
            valid_xi=valid_xi,
            station_lats=station_lats,
            station_lons=station_lons,
            station_values=station_values,
            total_pixels=20,
            label="test",
        )

        assert result.interpolated_values.dtype == np.float32
        np.testing.assert_allclose(result.interpolated_values, np.array([1.5, 2.5, 3.5]))
        np.testing.assert_array_equal(result.succeeded_mask, np.array([True, True, True]))
        np.testing.assert_array_equal(result.rows, valid_yi)
        np.testing.assert_array_equal(result.cols, valid_xi)
        np.testing.assert_allclose(result.values, np.array([1.5, 2.5, 3.5]))
        assert result.interpolated_count == 3
        assert result.failed_interpolation_count == 0
        assert result.skipped_nodata_count == 17
        assert result.total_pixels == 20

    def test_nan_interpolated_values_are_marked_failed(self, monkeypatch):
        # Verifies NaN handling: failed pixels are excluded from rows/cols/values,
        # while successful values retain their source indices.
        valid_lats = np.array([49.0, 49.1, 49.2, 49.3], dtype=np.float32)
        valid_lons = np.array([-123.0, -123.1, -123.2, -123.3], dtype=np.float32)
        valid_yi = np.array([0, 1, 2, 3], dtype=np.intp)
        valid_xi = np.array([9, 8, 7, 6], dtype=np.intp)
        station_lats = np.array([49.05, 49.15], dtype=np.float32)
        station_lons = np.array([-123.05, -123.15], dtype=np.float32)
        station_values = np.array([10.0, 20.0], dtype=np.float32)

        monkeypatch.setattr(
            "wps_sfms.processors.idw.idw_interpolation",
            lambda *args: np.array([np.nan, 4.0, np.nan, -1.0], dtype=np.float64),
        )

        result = idw_on_valid_pixels(
            valid_lats=valid_lats,
            valid_lons=valid_lons,
            valid_yi=valid_yi,
            valid_xi=valid_xi,
            station_lats=station_lats,
            station_lons=station_lons,
            station_values=station_values,
            total_pixels=10,
            label="test",
        )

        np.testing.assert_array_equal(result.succeeded_mask, np.array([False, True, False, True]))
        np.testing.assert_array_equal(result.rows, np.array([1, 3], dtype=np.intp))
        np.testing.assert_array_equal(result.cols, np.array([8, 6], dtype=np.intp))
        np.testing.assert_allclose(result.values, np.array([4.0, -1.0], dtype=np.float32))
        assert result.interpolated_count == 2
        assert result.failed_interpolation_count == 2
        assert result.skipped_nodata_count == 6

    def test_empty_valid_pixels_returns_empty_indexed_results(self, monkeypatch):
        # Verifies edge case behavior when no valid raster pixels are provided:
        # all outputs should be empty and skipped_nodata_count == total_pixels.
        valid_lats = np.array([], dtype=np.float32)
        valid_lons = np.array([], dtype=np.float32)
        valid_yi = np.array([], dtype=np.intp)
        valid_xi = np.array([], dtype=np.intp)
        station_lats = np.array([49.05], dtype=np.float32)
        station_lons = np.array([-123.05], dtype=np.float32)
        station_values = np.array([10.0], dtype=np.float32)

        monkeypatch.setattr(
            "wps_sfms.processors.idw.idw_interpolation",
            lambda *args: np.array([], dtype=np.float64),
        )

        result = idw_on_valid_pixels(
            valid_lats=valid_lats,
            valid_lons=valid_lons,
            valid_yi=valid_yi,
            valid_xi=valid_xi,
            station_lats=station_lats,
            station_lons=station_lons,
            station_values=station_values,
            total_pixels=5,
            label="test",
        )

        assert result.interpolated_values.size == 0
        assert result.succeeded_mask.size == 0
        assert result.rows.size == 0
        assert result.cols.size == 0
        assert result.values.size == 0
        assert result.interpolated_count == 0
        assert result.failed_interpolation_count == 0
        assert result.skipped_nodata_count == 5
