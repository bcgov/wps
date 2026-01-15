"""
Unit tests for precipitation interpolation module.
"""

import numpy as np
from typing import Optional, cast
from unittest.mock import Mock, patch, MagicMock
from osgeo import gdal
from app.sfms.weather_interpolation import (
    interpolate_to_raster,
)


def create_mock_raster_dataset(
    raster_size=(10, 10),
    nodata: Optional[float] = -9999.0,
    geotransform=(0, 1, 0, 50, 0, -1),
):
    """
    Create a mock WPSDataset for raster interpolation tests.

    :param raster_size: Tuple of (x_size, y_size) for raster dimensions
    :param nodata: NoData value for the raster
    :param geotransform: GDAL geotransform tuple
    :return: Mock context manager for WPSDataset
    """
    x_size, y_size = raster_size

    mock_ds = cast(gdal.Dataset, Mock())
    mock_ds.GetGeoTransform.return_value = geotransform
    mock_ds.GetProjection.return_value = (
        'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]]]'
    )
    mock_ds.RasterXSize = x_size
    mock_ds.RasterYSize = y_size

    # Mock band for nodata
    mock_band = cast(gdal.Band, Mock())
    mock_band.GetNoDataValue.return_value = nodata
    mock_ds.GetRasterBand.return_value = mock_band

    # Mock get_lat_lon_coords to return valid coordinates
    def mock_get_lat_lon_coords(valid_mask=None):
        if valid_mask is None:
            valid_mask = np.ones((y_size, x_size), dtype=bool)
        valid_yi, valid_xi = np.where(valid_mask)
        # Generate mock lat/lon coords based on indices
        lats = 49.0 + valid_yi * 0.01
        lons = -123.0 - valid_xi * 0.01
        return lats, lons, valid_yi, valid_xi

    # Mock get_valid_mask to return valid mask (all pixels valid)
    def mock_get_valid_mask():
        return np.ones((y_size, x_size), dtype=bool)

    mock_wrapper = Mock()
    mock_wrapper.ds = mock_ds
    mock_wrapper.get_lat_lon_coords = Mock(side_effect=mock_get_lat_lon_coords)
    mock_wrapper.get_valid_mask = Mock(side_effect=mock_get_valid_mask)

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = Mock(return_value=mock_wrapper)
    mock_ctx.__exit__ = Mock(return_value=False)

    return mock_ctx


class TestInterpolateToRaster:
    """Tests for interpolate_precipitation_to_raster function."""

    def test_interpolate_basic_success(self):
        """Test successful raster interpolation."""
        station_lats = [49.0, 49.1]
        station_lons = [-123.0, -123.1]
        station_values = [5.0, 10.0]

        mock_ref_ctx = create_mock_raster_dataset()

        with patch("app.sfms.weather_interpolation.WPSDataset") as mock_wps_dataset:
            with patch("app.sfms.weather_interpolation.save_raster_to_geotiff") as mock_save:
                mock_wps_dataset.return_value = mock_ref_ctx

                result = interpolate_to_raster(
                    station_lats,
                    station_lons,
                    station_values,
                    "/path/to/ref.tif",
                    "/path/to/output.tif",
                )

                assert result == "/path/to/output.tif"
                mock_save.assert_called_once()

    def test_interpolate_with_single_station(self):
        """Test interpolation with a single station."""
        station_lats = [49.0]
        station_lons = [-123.0]
        station_values = [7.5]

        mock_ref_ctx = create_mock_raster_dataset(raster_size=(5, 5))

        with patch("app.sfms.weather_interpolation.WPSDataset") as mock_wps_dataset:
            with patch("app.sfms.weather_interpolation.save_raster_to_geotiff"):
                mock_wps_dataset.return_value = mock_ref_ctx

                result = interpolate_to_raster(
                    station_lats,
                    station_lons,
                    station_values,
                    "/path/to/ref.tif",
                    "/path/to/output.tif",
                )

                assert result == "/path/to/output.tif"

    def test_interpolate_captures_output_array(self):
        """Test interpolation verifying output array is properly populated."""
        station_lats = [49.0]
        station_lons = [-123.0]
        station_values = [5.0]

        captured_array = None

        def capture_save(array, *args, **kwargs):
            nonlocal captured_array
            captured_array = array

        mock_ref_ctx = create_mock_raster_dataset(
            raster_size=(3, 3),
            geotransform=(-123.1, 0.05, 0, 49.1, 0, -0.05),
        )

        with patch("app.sfms.weather_interpolation.WPSDataset") as mock_wps_dataset:
            with patch(
                "app.sfms.weather_interpolation.save_raster_to_geotiff",
                side_effect=capture_save,
            ):
                mock_wps_dataset.return_value = mock_ref_ctx

                result = interpolate_to_raster(
                    station_lats,
                    station_lons,
                    station_values,
                    "/path/to/ref.tif",
                    "/path/to/output.tif",
                )

                assert result == "/path/to/output.tif"
                assert captured_array is not None
                assert captured_array.shape == (3, 3)
                # At least some cells should have been interpolated
                non_nodata_count = np.sum(captured_array != -9999.0)
                assert non_nodata_count > 0, "Expected some cells to be interpolated"

    def test_interpolate_with_zero_precipitation(self):
        """Test that zero precipitation values are correctly interpolated."""
        station_lats = [49.0, 49.1]
        station_lons = [-123.0, -123.1]
        station_values = [0.0, 0.0]

        captured_array = None

        def capture_save(array, *args, **kwargs):
            nonlocal captured_array
            captured_array = array

        mock_ref_ctx = create_mock_raster_dataset(raster_size=(3, 3))

        with patch("app.sfms.weather_interpolation.WPSDataset") as mock_wps_dataset:
            with patch(
                "app.sfms.weather_interpolation.save_raster_to_geotiff",
                side_effect=capture_save,
            ):
                mock_wps_dataset.return_value = mock_ref_ctx

                result = interpolate_to_raster(
                    station_lats,
                    station_lons,
                    station_values,
                    "/path/to/ref.tif",
                    "/path/to/output.tif",
                )

                assert result == "/path/to/output.tif"
                # Interpolated values should be 0.0, not nodata
                assert captured_array is not None
                interpolated_values = captured_array[captured_array != -9999.0]
                assert len(interpolated_values) > 0
                assert np.allclose(interpolated_values, 0.0)


class TestGetMaskPath:
    """Tests for get_mask_path function."""

    def test_get_mask_path_returns_correct_format(self):
        """Test that get_mask_path returns correct S3 path format."""
        from app.sfms.sfms_common import get_mask_path

        with patch("app.sfms.sfms_common.config") as mock_config:
            mock_config.get.return_value = "test-bucket"

            result = get_mask_path()

            assert result == "/vsis3/test-bucket/sfms/static/bc_mask.tif"

    def test_get_mask_path_with_different_config(self):
        """Test get_mask_path with different config values."""
        from app.sfms.sfms_common import get_mask_path

        with patch("app.sfms.sfms_common.config") as mock_config:
            mock_config.get.return_value = "production-bucket"

            result = get_mask_path()

            assert result == "/vsis3/production-bucket/sfms/static/bc_mask.tif"
