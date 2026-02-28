"""
Unit tests for precipitation interpolation module.
"""

import numpy as np
import uuid
import pytest
from osgeo import gdal
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_sfms.interpolation.idw import interpolate_to_raster
from wps_sfms.interpolation.source import StationActualSource
from wps_sfms.tests.conftest import create_test_raster


class TestInterpolateToRaster:
    """Tests for interpolate_to_raster function."""

    def test_interpolation_produces_valid_output(self):
        """Test that interpolation creates an output raster with interpolated values."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 10, 10, extent, epsg=4326)
            create_test_raster(mask_path, 10, 10, extent, epsg=4326)

            station_lats = [49.05, 49.08]
            station_lons = [-123.05, -123.02]
            station_values = [10.0, 20.0]

            dataset = interpolate_to_raster(
                station_lats, station_lons, station_values, ref_path, mask_path
            )

            data = dataset.ds.GetRasterBand(1).ReadAsArray()
            nodata = dataset.ds.GetRasterBand(1).GetNoDataValue()

            assert data.shape == (10, 10)
            valid_count = np.sum(data != nodata)
            assert valid_count > 0, "Expected some interpolated values"

            valid_values = data[data != nodata]
            assert np.all(valid_values >= 10.0 - 0.1)
            assert np.all(valid_values <= 20.0 + 0.1)
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(mask_path)

    def test_zero_values_interpolated_correctly(self):
        """Test that zero precipitation values are interpolated as 0.0, not nodata."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, epsg=4326)
            create_test_raster(mask_path, 5, 5, extent, epsg=4326)

            station_lats = [49.05, 49.08]
            station_lons = [-123.05, -123.02]
            station_values = [0.0, 0.0]

            dataset = interpolate_to_raster(
                station_lats, station_lons, station_values, ref_path, mask_path
            )

            data = dataset.ds.GetRasterBand(1).ReadAsArray()
            nodata = dataset.ds.GetRasterBand(1).GetNoDataValue()

            valid_values = data[data != nodata]
            assert len(valid_values) > 0, "Expected some interpolated values"
            assert np.allclose(valid_values, 0.0), "Zero values should interpolate to 0.0"
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(mask_path)

    def test_single_station_interpolation(self):
        """Test interpolation with a single station."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, epsg=4326)
            create_test_raster(mask_path, 5, 5, extent, epsg=4326)

            dataset = interpolate_to_raster([49.05], [-123.05], [15.0], ref_path, mask_path)

            data = dataset.ds.GetRasterBand(1).ReadAsArray()
            nodata = dataset.ds.GetRasterBand(1).GetNoDataValue()

            valid_values = data[data != nodata]
            assert len(valid_values) > 0
            assert np.allclose(valid_values, 15.0)
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(mask_path)

    def test_output_preserves_reference_properties(self):
        """Test that output raster preserves reference raster properties."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 8, 6, extent, epsg=4326)
            create_test_raster(mask_path, 8, 6, extent, epsg=4326)

            dataset = interpolate_to_raster([49.05], [-123.05], [10.0], ref_path, mask_path)

            ref_ds = gdal.Open(ref_path)
            assert dataset.ds.RasterXSize == ref_ds.RasterXSize
            assert dataset.ds.RasterYSize == ref_ds.RasterYSize
            assert dataset.ds.GetGeoTransform() == ref_ds.GetGeoTransform()
            assert dataset.ds.GetProjection() == ref_ds.GetProjection()
            ref_ds = None
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(mask_path)


class TestStationActualSource:
    """Tests for StationActualSource attribute validation."""

    def test_valid_attribute_constructs_successfully(self):
        """Test that a valid attribute name constructs without error."""
        actuals = [SFMSDailyActual(code=1, lat=49.0, lon=-123.0, precipitation=5.0)]
        source = StationActualSource("precipitation", actuals)
        lats, lons, values = source.get_interpolation_data()
        assert len(lats) == 1
        assert values[0] == pytest.approx(5.0)

    def test_invalid_attribute_raises_value_error(self):
        """Test that an unknown attribute name raises ValueError at construction."""
        actuals = [SFMSDailyActual(code=1, lat=49.0, lon=-123.0)]
        with pytest.raises(ValueError, match="Unknown attribute"):
            StationActualSource("not_a_real_field", actuals)

    def test_none_values_are_excluded(self):
        """Test that stations with None for the target attribute are excluded."""
        actuals = [
            SFMSDailyActual(code=1, lat=49.0, lon=-123.0, precipitation=3.0),
            SFMSDailyActual(code=2, lat=49.1, lon=-123.1, precipitation=None),
        ]
        source = StationActualSource("precipitation", actuals)
        lats, lons, values = source.get_interpolation_data()
        assert len(lats) == 1
        assert values[0] == pytest.approx(3.0)
