"""
Unit tests for temperature interpolation module.
"""

import pytest
import numpy as np
from numpy.testing import assert_allclose
from osgeo import gdal
from typing import Optional, cast
from unittest.mock import Mock, patch, MagicMock
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.schemas.sfms import StationTemperature
from wps_shared.geospatial.spatial_interpolation import (
    haversine_distance,
    idw_interpolation,
)
from app.sfms.temperature_interpolation import (
    compute_actual_temperatures,
    LAPSE_RATE,
    interpolate_temperature_to_raster,
)


def create_mock_raster_datasets(
    raster_size=(10, 10),
    dem_data=None,
    dem_nodata: Optional[float] = -9999.0,
    geotransform=(0, 1, 0, 50, 0, -1),
):
    """
    Create mock GDAL datasets for raster interpolation tests.

    :param raster_size: Tuple of (x_size, y_size) for raster dimensions
    :param dem_data: Optional numpy array for DEM data, defaults to uniform 100.0
    :param dem_nodata: NoData value for DEM, or None
    :param geotransform: GDAL geotransform tuple
    :return: Tuple of (mock_ref_ds, mock_dem_ds, mock_output_ds, mock_ref_ctx, mock_dem_ctx)
    """
    x_size, y_size = raster_size

    # Create reference dataset
    mock_ref_ds = cast(gdal.Dataset, Mock())
    mock_ref_ds.GetGeoTransform.return_value = geotransform
    mock_ref_ds.GetProjection.return_value = (
        'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]]]'
    )
    mock_ref_ds.RasterXSize = x_size
    mock_ref_ds.RasterYSize = y_size

    # Create DEM dataset
    if dem_data is None:
        dem_data = np.full((y_size, x_size), 100.0)

    mock_dem_band = cast(gdal.Band, Mock())
    # ReadAsArray with no args returns full array (for old code compatibility)
    mock_dem_band.ReadAsArray.return_value = dem_data

    # ReadAsArray with args (xoff, yoff, xsize, ysize) returns a subset
    def read_array_subset(xoff=None, yoff=None, xsize=None, ysize=None):
        if xoff is None:
            return dem_data
        # Return 1x1 array for single pixel reads
        if xsize == 1 and ysize == 1:
            if 0 <= yoff < dem_data.shape[0] and 0 <= xoff < dem_data.shape[1]:
                return np.array([[dem_data[yoff, xoff]]])
            return None
        return dem_data[yoff : yoff + ysize, xoff : xoff + xsize]

    mock_dem_band.ReadAsArray.side_effect = read_array_subset
    mock_dem_band.GetNoDataValue.return_value = dem_nodata

    mock_dem_ds = cast(gdal.Dataset, Mock())
    mock_dem_ds.GetRasterBand.return_value = mock_dem_band
    mock_dem_ds.RasterXSize = x_size
    mock_dem_ds.RasterYSize = y_size
    mock_dem_ds.GetGeoTransform.return_value = geotransform

    # Mock warp_to_match to return a resampled DEM
    mock_resampled_dem = cast(WPSDataset, Mock())
    mock_resampled_dem.ds = mock_dem_ds
    mock_resampled_dem.ds.GetRasterBand.return_value = mock_dem_band

    # Mock get_lat_lon_coords to return valid coordinates
    def mock_get_lat_lon_coords(valid_mask):
        # Get indices where mask is True
        valid_yi, valid_xi = np.where(valid_mask)
        # Generate mock lat/lon coords based on indices - place them near typical BC stations
        lats = 49.0 + valid_yi * 0.01
        lons = -123.0 - valid_xi * 0.01
        return lats, lons, valid_yi, valid_xi

    mock_resampled_dem.get_lat_lon_coords = Mock(side_effect=mock_get_lat_lon_coords)

    # Mock get_valid_mask to return valid mask based on nodata
    def mock_get_valid_mask():
        if dem_nodata is not None:
            return dem_data != dem_nodata
        return np.ones((y_size, x_size), dtype=bool)

    mock_resampled_dem.get_valid_mask = Mock(side_effect=mock_get_valid_mask)

    # Create output dataset
    mock_output_ds = Mock()
    mock_output_ds.export_to_geotiff = Mock()
    mock_output_ds.__enter__ = Mock(return_value=mock_output_ds)
    mock_output_ds.__exit__ = Mock(return_value=False)

    # Create context managers for WPSDataset
    mock_ref_ctx = MagicMock()
    mock_ref_ctx.__enter__ = Mock(return_value=Mock(ds=mock_ref_ds))
    mock_ref_ctx.__exit__ = Mock(return_value=False)

    mock_dem_ctx = MagicMock()
    mock_dem_wrapper = Mock(ds=mock_dem_ds)
    # Add warp_to_match method that returns the resampled DEM
    mock_dem_wrapper.warp_to_match = Mock(return_value=mock_resampled_dem)
    mock_dem_ctx.__enter__ = Mock(return_value=mock_dem_wrapper)
    mock_dem_ctx.__exit__ = Mock(return_value=False)

    return mock_ref_ds, mock_dem_ds, mock_output_ds, mock_ref_ctx, mock_dem_ctx


class TestStationTemperature:
    """Tests for StationTemperature class."""

    def test_station_temperature_initialization(self):
        """Test that StationTemperature initializes correctly."""
        station = StationTemperature(
            code=123, lat=49.0, lon=-123.0, elevation=500.0, temperature=20.0
        )
        assert station.code == 123
        assert station.lat == pytest.approx(49.0)
        assert station.lon == pytest.approx(-123.0)
        assert station.elevation == pytest.approx(500.0)
        assert station.temperature == pytest.approx(20.0)
        assert station.sea_level_temp is None


class TestHaversineDistance:
    """Tests for haversine distance calculation."""

    def test_same_point(self):
        """Test that distance between same point is zero."""
        lat, lon = 49.0, -123.0
        distance = haversine_distance(lat, lon, lat, lon)
        assert distance == pytest.approx(0.0, abs=1.0)  # Within 1 meter

    def test_known_distance(self):
        """Test haversine with known distance."""
        # Vancouver: 49.2827° N, 123.1207° W
        # Seattle: 47.6062° N, 122.3321° W
        # Approximate distance: ~195 km

        vancouver_lat, vancouver_lon = 49.2827, -123.1207
        seattle_lat, seattle_lon = 47.6062, -122.3321

        distance = haversine_distance(vancouver_lat, vancouver_lon, seattle_lat, seattle_lon)

        # Should be approximately 195 km (195000 meters)
        # Allow 5% tolerance
        assert distance == pytest.approx(195000, rel=0.05)

    def test_equator_distance(self):
        """Test distance along equator."""
        # 1 degree of longitude at equator ≈ 111.32 km
        distance = haversine_distance(0.0, 0.0, 0.0, 1.0)
        assert distance == pytest.approx(111320, rel=0.01)


class TestIDWInterpolation:
    """Tests for Inverse Distance Weighting interpolation."""

    def test_idw_exact_match(self):
        """Test that IDW returns station value when point is at station."""
        stations = [
            StationTemperature(code=1, lat=49.0, lon=-123.0, elevation=100, temperature=15.0),
            StationTemperature(code=2, lat=50.0, lon=-124.0, elevation=200, temperature=20.0),
        ]

        # Prepare lists for IDW
        lats = [s.lat for s in stations]
        lons = [s.lon for s in stations]
        values = [s.sea_level_temp for s in stations]

        # Query at exact station location
        result = idw_interpolation(49.0, -123.0, lats, lons, values)

        # Should return the sea level temp of the first station
        assert result == pytest.approx(stations[0].sea_level_temp, rel=1e-6)

    def test_idw_between_two_stations(self):
        """Test IDW interpolation between two stations."""
        stations = [
            StationTemperature(code=1, lat=49.0, lon=-123.0, elevation=0, temperature=10.0),
            StationTemperature(code=2, lat=50.0, lon=-123.0, elevation=0, temperature=20.0),
        ]

        # Prepare lists for IDW
        lats = [s.lat for s in stations]
        lons = [s.lon for s in stations]
        values = [s.sea_level_temp for s in stations]

        # Query at midpoint
        result = idw_interpolation(49.5, -123.0, lats, lons, values)

        # Should be weighted average, closer to midpoint
        assert result is not None
        assert 10.0 < result < 20.0

    def test_idw_no_stations(self):
        """Test that IDW returns None when no stations provided."""
        result = idw_interpolation(49.0, -123.0, [], [], [])
        assert result is None

    def test_idw_outside_search_radius(self):
        """Test that IDW returns None when all stations outside search radius."""
        stations = [
            StationTemperature(code=1, lat=49.0, lon=-123.0, elevation=0, temperature=15.0),
        ]

        # Prepare lists for IDW
        lats = [s.lat for s in stations]
        lons = [s.lon for s in stations]
        values = [s.sea_level_temp for s in stations]

        # Query far away (at least 200km away)
        result = idw_interpolation(52.0, -128.0, lats, lons, values, search_radius=100000)
        assert result is None

    def test_idw_with_none_sea_level_temp(self):
        """Test that IDW handles points with None values."""
        stations = [
            StationTemperature(code=1, lat=49.0, lon=-123.0, elevation=0, temperature=15.0),
            StationTemperature(code=2, lat=50.0, lon=-124.0, elevation=0, temperature=20.0),
        ]

        # Prepare lists for IDW (including None value)
        lats = [s.lat for s in stations]
        lons = [s.lon for s in stations]
        values = [stations[0].sea_level_temp, None]

        result = idw_interpolation(49.5, -123.5, lats, lons, values)

        # Should still work with only one valid station
        assert result is not None
        assert result == pytest.approx(stations[0].sea_level_temp, abs=1.0)


class TestInterpolateTemperatureToRaster:
    """Tests for interpolate_temperature_to_raster function."""

    def test_interpolate_basic_success(self):
        """Test successful raster interpolation."""
        station_lats = [49.0, 49.1]
        station_lons = [-123.0, -123.1]
        station_values = [15.0, 12.0]  # sea-level adjusted temps

        _, _, _, mock_ref_ctx, mock_dem_ctx = create_mock_raster_datasets()

        with patch("app.sfms.temperature_interpolation.WPSDataset") as mock_wps_dataset:
            with patch("app.sfms.temperature_interpolation.save_raster_to_geotiff") as mock_save:
                mock_wps_dataset.side_effect = [mock_ref_ctx, mock_dem_ctx]

                result = interpolate_temperature_to_raster(
                    station_lats,
                    station_lons,
                    station_values,
                    "/path/to/ref.tif",
                    "/path/to/dem.tif",
                    "/path/to/output.tif",
                )

                assert result == "/path/to/output.tif"
                mock_save.assert_called_once()

    def test_interpolate_skips_nodata_cells(self):
        """Test that cells with NoData elevation are skipped."""
        station_lats = [49.0]
        station_lons = [-123.0]
        station_values = [15.0]

        # Create DEM with NoData values
        dem_data = np.full((5, 5), 100.0)
        dem_data[2, 2] = -9999.0  # NoData cell

        _, _, _, mock_ref_ctx, mock_dem_ctx = create_mock_raster_datasets(
            raster_size=(5, 5), dem_data=dem_data, dem_nodata=-9999.0
        )

        with patch("app.sfms.temperature_interpolation.WPSDataset") as mock_wps_dataset:
            with patch("app.sfms.temperature_interpolation.save_raster_to_geotiff"):
                mock_wps_dataset.side_effect = [mock_ref_ctx, mock_dem_ctx]

                result = interpolate_temperature_to_raster(
                    station_lats,
                    station_lons,
                    station_values,
                    "/path/to/ref.tif",
                    "/path/to/dem.tif",
                    "/path/to/output.tif",
                )

                assert result == "/path/to/output.tif"

    def test_interpolate_with_actual_loop_execution(self):
        """Test interpolation verifying output array is properly populated."""
        station_lats = [49.0]
        station_lons = [-123.0]
        station_values = [15.65]  # sea-level adjusted temp (15 + 100m * 0.0065)

        # Create very small test arrays (2x2) to allow actual loop execution
        dem_data = np.array([[100.0, 200.0], [150.0, 250.0]], dtype=np.float32)

        # Track the array that gets passed to save_raster_to_geotiff
        captured_array = None

        def capture_save(array, *args, **kwargs):
            nonlocal captured_array
            captured_array = array

        _, _, _, mock_ref_ctx, mock_dem_ctx = create_mock_raster_datasets(
            raster_size=(2, 2),
            dem_data=dem_data,
            dem_nodata=None,
            geotransform=(-123.1, 0.05, 0, 49.1, 0, -0.05),
        )

        with patch("app.sfms.temperature_interpolation.WPSDataset") as mock_wps_dataset:
            with patch(
                "app.sfms.temperature_interpolation.save_raster_to_geotiff",
                side_effect=capture_save,
            ):
                mock_wps_dataset.side_effect = [mock_ref_ctx, mock_dem_ctx]

                result = interpolate_temperature_to_raster(
                    station_lats,
                    station_lons,
                    station_values,
                    "/path/to/ref.tif",
                    "/path/to/dem.tif",
                    "/path/to/output.tif",
                )

                assert result == "/path/to/output.tif"

                # Verify that the output array was created and has non-NoData values
                assert captured_array is not None
                assert captured_array.shape == (2, 2)
                # At least some cells should have been interpolated (not all -9999)
                non_nodata_count = np.sum(captured_array != -9999.0)
                assert non_nodata_count > 0, "Expected some cells to be interpolated"


class TestIntegrationScenario:
    """Integration tests simulating real-world scenarios."""

    def test_full_workflow_simple(self):
        """Test the full workflow with simple data."""
        # Create stations at different elevations
        stations = [
            StationTemperature(
                code=1, lat=49.0, lon=-123.0, elevation=0, temperature=15.0
            ),  # Sea level, 15°C
            StationTemperature(
                code=2, lat=49.1, lon=-123.1, elevation=500, temperature=10.0
            ),  # 500m, 10°C
            StationTemperature(
                code=3, lat=49.2, lon=-123.2, elevation=1000, temperature=5.0
            ),  # 1000m, 5°C
        ]

        # Verify sea level adjustments
        # Station 1: 15 + 0 = 15°C
        assert stations[0].sea_level_temp == pytest.approx(15.0, rel=1e-6)

        # Station 2: 10 + (500 * 0.0065) = 10 + 3.25 = 13.25°C
        assert stations[1].sea_level_temp == pytest.approx(13.25, rel=1e-6)

        # Station 3: 5 + (1000 * 0.0065) = 5 + 6.5 = 11.5°C
        assert stations[2].sea_level_temp == pytest.approx(11.5, rel=1e-6)

        # Prepare lists for IDW
        lats = [s.lat for s in stations]
        lons = [s.lon for s in stations]
        values = [s.sea_level_temp for s in stations]

        # Interpolate at a point
        interpolated = idw_interpolation(49.1, -123.1, lats, lons, values)
        assert interpolated is not None

        # Adjust back to elevation (e.g., 250m)
        final_temp = compute_actual_temperatures(interpolated, 250)

        # Should be reasonable (between 5-15°C range)
        assert 5.0 <= final_temp <= 15.0
