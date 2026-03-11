"""
Unit tests for temperature interpolation module.
"""

import numpy as np
import uuid
import pytest
from osgeo import gdal
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_sfms.interpolation.field import build_temperature_field
from wps_sfms.processors.temperature import TemperatureInterpolator
from wps_sfms.tests.conftest import create_test_raster


def create_test_actuals(lats, lons, temps, elevations):
    """Create test SFMSDailyActual objects."""
    actuals = []
    for i, (lat, lon, temp, elev) in enumerate(zip(lats, lons, temps, elevations)):
        actual = SFMSDailyActual(
            code=100 + i,
            lat=lat,
            lon=lon,
            elevation=elev,
            temperature=temp,
            relative_humidity=None,
            precipitation=None,
            wind_speed=None,
        )
        actuals.append(actual)
    return actuals


class TestTemperatureInterpolator:
    """Tests for TemperatureInterpolator."""

    def test_interpolate_basic_success(self):
        """Test successful raster interpolation."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 10, 10, extent, fill_value=1.0)
            create_test_raster(dem_path, 10, 10, extent, fill_value=100.0)
            create_test_raster(mask_path, 10, 10, extent, fill_value=1.0)

            actuals = create_test_actuals(
                lats=[49.05, 49.08],
                lons=[-123.05, -123.02],
                temps=[15.0, 12.0],
                elevations=[100.0, 200.0],
            )
            temperature_field = build_temperature_field(actuals)

            dataset = TemperatureInterpolator(
                mask_path=mask_path, dem_path=dem_path, field=temperature_field
            ).interpolate(ref_path)

            data = dataset.ds.GetRasterBand(1).ReadAsArray()
            nodata = dataset.ds.GetRasterBand(1).GetNoDataValue()

            assert data.shape == (10, 10)
            valid_count = np.sum(data != nodata)
            assert valid_count > 0, "Expected some interpolated values"
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(mask_path)

    def test_interpolate_skips_masked_cells(self):
        """Test that cells masked out by BC mask are skipped."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(dem_path, 5, 5, extent, fill_value=100.0)

            mask_data = np.full((5, 5), 1.0)
            mask_data[2, 2] = 0.0  # Masked cell
            create_test_raster(mask_path, 5, 5, extent, data=mask_data)

            actuals = create_test_actuals(
                lats=[49.05], lons=[-123.05], temps=[15.0], elevations=[100.0]
            )
            temperature_field = build_temperature_field(actuals)

            dataset = TemperatureInterpolator(
                mask_path=mask_path, dem_path=dem_path, field=temperature_field
            ).interpolate(ref_path)

            data = dataset.ds.GetRasterBand(1).ReadAsArray()
            nodata = dataset.ds.GetRasterBand(1).GetNoDataValue()

            assert data[2, 2] == nodata
            valid_count = np.sum(data != nodata)
            assert valid_count == 24, "Expected 24 valid cells (25 - 1 masked)"
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(mask_path)

    def test_interpolate_with_elevation_adjustment(self):
        """Test that temperature is adjusted based on elevation."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(mask_path, 5, 5, extent, fill_value=1.0)

            # DEM with varying elevation
            dem_data = np.full((5, 5), 100.0)
            dem_data[0, 0] = 0.0  # Sea level
            dem_data[4, 4] = 1000.0  # 1000m elevation
            create_test_raster(dem_path, 5, 5, extent, data=dem_data)

            # Single station at 100m with 15C
            # Sea-level adjusted temp = 15 + 100 * 0.0065 = 15.65C
            actuals = create_test_actuals(
                lats=[49.05], lons=[-123.05], temps=[15.0], elevations=[100.0]
            )
            temperature_field = build_temperature_field(actuals)

            dataset = TemperatureInterpolator(
                mask_path=mask_path, dem_path=dem_path, field=temperature_field
            ).interpolate(ref_path)

            data = dataset.ds.GetRasterBand(1).ReadAsArray()

            # At sea level (0m): temp = 15.65 - 0 * 0.0065 = 15.65C
            # At 100m: temp = 15.65 - 100 * 0.0065 = 15.0C
            # At 1000m: temp = 15.65 - 1000 * 0.0065 = 9.15C
            sea_level_temp = data[0, 0]
            mid_elevation_temp = data[2, 2]  # 100m
            high_elevation_temp = data[4, 4]  # 1000m

            assert high_elevation_temp < mid_elevation_temp < sea_level_temp
            assert np.isclose(sea_level_temp, 15.65, atol=0.5)
            assert np.isclose(high_elevation_temp, 9.15, atol=0.5)
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(mask_path)

    def test_output_preserves_reference_properties(self):
        """Test that output raster preserves reference raster properties."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 8, 6, extent, fill_value=1.0)
            create_test_raster(dem_path, 8, 6, extent, fill_value=100.0)
            create_test_raster(mask_path, 8, 6, extent, fill_value=1.0)

            actuals = create_test_actuals(
                lats=[49.05], lons=[-123.05], temps=[15.0], elevations=[100.0]
            )
            temperature_field = build_temperature_field(actuals)

            dataset = TemperatureInterpolator(
                mask_path=mask_path, dem_path=dem_path, field=temperature_field
            ).interpolate(ref_path)

            ref_ds = gdal.Open(ref_path)
            assert dataset.ds.RasterXSize == ref_ds.RasterXSize
            assert dataset.ds.RasterYSize == ref_ds.RasterYSize
            assert dataset.ds.GetGeoTransform() == ref_ds.GetGeoTransform()
            assert dataset.ds.GetProjection() == ref_ds.GetProjection()
            ref_ds = None
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(mask_path)

    def test_interpolate_raises_when_no_valid_stations(self):
        """Test that RuntimeError is raised when no stations have valid temperature values."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(dem_path, 5, 5, extent, fill_value=100.0)
            create_test_raster(mask_path, 5, 5, extent, fill_value=1.0)

            actuals = [
                SFMSDailyActual(code=1, lat=49.05, lon=-123.05, elevation=100.0, temperature=None)
            ]
            temperature_field = build_temperature_field(actuals)

            with pytest.raises(RuntimeError, match="No pixels were successfully interpolated"):
                TemperatureInterpolator(
                    mask_path=mask_path, dem_path=dem_path, field=temperature_field
                ).interpolate(ref_path)
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(mask_path)
