"""
Unit tests for precipitation interpolation module.
"""

import pytest
import numpy as np
from datetime import datetime, timezone
from typing import Optional, cast
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from osgeo import gdal
from wps_shared.schemas.sfms import StationPrecipitation
from wps_shared.schemas.stations import WeatherStation
from app.sfms.weather_interpolation import (
    fetch_station_precipitation,
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

    mock_wrapper = Mock()
    mock_wrapper.ds = mock_ds
    mock_wrapper.get_lat_lon_coords = Mock(side_effect=mock_get_lat_lon_coords)

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = Mock(return_value=mock_wrapper)
    mock_ctx.__exit__ = Mock(return_value=False)

    return mock_ctx


class TestStationPrecipitation:
    """Tests for StationPrecipitation class."""

    def test_station_precipitation_initialization(self):
        """Test that StationPrecipitation initializes correctly."""
        station = StationPrecipitation(code=123, lat=49.0, lon=-123.0, precipitation=5.5)
        assert station.code == 123
        assert station.lat == pytest.approx(49.0)
        assert station.lon == pytest.approx(-123.0)
        assert station.precipitation == pytest.approx(5.5)


class TestFetchStationPrecipitation:
    """Tests for fetch_station_precipitation function."""

    @pytest.mark.anyio
    async def test_fetch_basic_success(self):
        """Test successful fetch of station precipitation."""
        mock_session = AsyncMock()
        headers = {"Authorization": "Bearer test_token"}
        time_of_interest = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

        stations = [
            WeatherStation(
                code=123,
                name="Test Station 1",
                lat=49.0,
                long=-123.0,
            ),
            WeatherStation(
                code=456,
                name="Test Station 2",
                lat=50.0,
                long=-124.0,
            ),
        ]

        raw_dailies = [
            {
                "stationData": {
                    "stationCode": 123,
                    "displayLabel": "Test Station 1",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 49.0,
                    "longitude": -123.0,
                },
                "precipitation": 2.5,
                "recordType": {"id": "ACTUAL"},
            },
            {
                "stationData": {
                    "stationCode": 456,
                    "displayLabel": "Test Station 2",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 50.0,
                    "longitude": -124.0,
                },
                "precipitation": 10.0,
                "recordType": {"id": "ACTUAL"},
            },
        ]

        with patch(
            "app.sfms.sfms_common.fetch_raw_dailies_for_all_stations",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_precipitation(
                mock_session, headers, time_of_interest, stations
            )

            assert len(result) == 2
            assert result[0].code == 123
            assert result[0].precipitation == pytest.approx(2.5)
            assert result[1].code == 456
            assert result[1].precipitation == pytest.approx(10.0)

    @pytest.mark.anyio
    async def test_fetch_filters_non_actual_records(self):
        """Test that non-ACTUAL records are filtered out."""
        mock_session = AsyncMock()
        headers = {"Authorization": "Bearer test_token"}
        time_of_interest = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

        stations = [
            WeatherStation(code=123, name="Test Station", lat=49.0, long=-123.0),
        ]

        raw_dailies = [
            {
                "stationData": {
                    "stationCode": 123,
                    "displayLabel": "Test Station",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 49.0,
                    "longitude": -123.0,
                },
                "precipitation": 5.0,
                "recordType": {"id": "FORECAST"},
            },
        ]

        with patch(
            "app.sfms.sfms_common.fetch_raw_dailies_for_all_stations",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_precipitation(
                mock_session, headers, time_of_interest, stations
            )

            assert len(result) == 0

    @pytest.mark.anyio
    async def test_fetch_handles_missing_precipitation(self):
        """Test that stations with missing precipitation are skipped."""
        mock_session = AsyncMock()
        headers = {"Authorization": "Bearer test_token"}
        time_of_interest = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

        stations = [
            WeatherStation(code=123, name="Test Station", lat=49.0, long=-123.0),
        ]

        raw_dailies = [
            {
                "stationData": {
                    "stationCode": 123,
                    "displayLabel": "Test Station",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 49.0,
                    "longitude": -123.0,
                },
                "precipitation": None,
                "recordType": {"id": "ACTUAL"},
            },
        ]

        with patch(
            "app.sfms.sfms_common.fetch_raw_dailies_for_all_stations",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_precipitation(
                mock_session, headers, time_of_interest, stations
            )

            assert len(result) == 0

    @pytest.mark.anyio
    async def test_fetch_handles_unknown_station(self):
        """Test that stations not in lookup are skipped."""
        mock_session = AsyncMock()
        headers = {"Authorization": "Bearer test_token"}
        time_of_interest = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

        stations = [
            WeatherStation(code=123, name="Test Station", lat=49.0, long=-123.0),
        ]

        raw_dailies = [
            {
                "stationData": {
                    "stationCode": 999,  # Not in station list
                    "displayLabel": "Unknown Station",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 49.0,
                    "longitude": -123.0,
                },
                "precipitation": 5.0,
                "recordType": {"id": "ACTUAL"},
            },
        ]

        with patch(
            "app.sfms.sfms_common.fetch_raw_dailies_for_all_stations",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_precipitation(
                mock_session, headers, time_of_interest, stations
            )

            assert len(result) == 0

    @pytest.mark.anyio
    async def test_fetch_handles_zero_precipitation(self):
        """Test that zero precipitation values are included."""
        mock_session = AsyncMock()
        headers = {"Authorization": "Bearer test_token"}
        time_of_interest = datetime(2024, 1, 15, 20, 0, 0, tzinfo=timezone.utc)

        stations = [
            WeatherStation(code=123, name="Test Station", lat=49.0, long=-123.0),
        ]

        raw_dailies = [
            {
                "stationData": {
                    "stationCode": 123,
                    "displayLabel": "Test Station",
                    "stationStatus": {"id": "ACTIVE"},
                    "latitude": 49.0,
                    "longitude": -123.0,
                },
                "precipitation": 0.0,
                "recordType": {"id": "ACTUAL"},
            },
        ]

        with patch(
            "app.sfms.sfms_common.fetch_raw_dailies_for_all_stations",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = raw_dailies

            result = await fetch_station_precipitation(
                mock_session, headers, time_of_interest, stations
            )

            assert len(result) == 1
            assert result[0].precipitation == pytest.approx(0.0)


class TestInterpolatePrecipitationToRaster:
    """Tests for interpolate_precipitation_to_raster function."""

    def test_interpolate_basic_success(self):
        """Test successful raster interpolation."""
        station_lats = [49.0, 49.1]
        station_lons = [-123.0, -123.1]
        station_values = [5.0, 10.0]

        mock_ref_ctx = create_mock_raster_dataset()

        with patch("app.sfms.precipitation_interpolation.WPSDataset") as mock_wps_dataset:
            with patch("app.sfms.precipitation_interpolation.save_raster_to_geotiff") as mock_save:
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

        with patch("app.sfms.precipitation_interpolation.WPSDataset") as mock_wps_dataset:
            with patch("app.sfms.precipitation_interpolation.save_raster_to_geotiff"):
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

        with patch("app.sfms.precipitation_interpolation.WPSDataset") as mock_wps_dataset:
            with patch(
                "app.sfms.precipitation_interpolation.save_raster_to_geotiff",
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

        with patch("app.sfms.precipitation_interpolation.WPSDataset") as mock_wps_dataset:
            with patch(
                "app.sfms.precipitation_interpolation.save_raster_to_geotiff",
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
