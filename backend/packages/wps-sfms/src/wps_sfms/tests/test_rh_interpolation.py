"""
Unit tests for relative humidity interpolation module.
"""

import numpy as np
import uuid
import pytest
from osgeo import gdal
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_sfms.interpolation.field import build_dewpoint_field, compute_rh
from wps_sfms.processors.relative_humidity import RHInterpolator
from wps_sfms.tests.conftest import create_test_raster


def create_test_actuals(lats, lons, dewpoints, elevations):
    """Create test SFMSDailyActual objects with dewpoint values."""
    actuals = []
    for i, (lat, lon, td, elev) in enumerate(zip(lats, lons, dewpoints, elevations)):
        actual = SFMSDailyActual(
            code=100 + i,
            lat=lat,
            lon=lon,
            elevation=elev,
            dewpoint=td,
        )
        actuals.append(actual)
    return actuals


class TestComputeRHFromTempAndDewpoint:
    """Tests for the simple approximation RH computation."""

    def test_dewpoint_equals_temp_gives_100_percent(self):
        """When dew point equals temperature, RH should be 100%."""
        temp = np.array([20.0, 10.0, 0.0], dtype=np.float32)
        dewpoint = np.array([20.0, 10.0, 0.0], dtype=np.float32)
        rh = compute_rh(temp, dewpoint)
        np.testing.assert_allclose(rh, 100.0, atol=0.01)

    def test_lower_dewpoint_gives_lower_rh(self):
        """Lower dew point relative to temperature should give lower RH."""
        temp = np.array([20.0, 20.0, 20.0], dtype=np.float32)
        dewpoint = np.array([20.0, 15.0, 10.0], dtype=np.float32)
        rh = compute_rh(temp, dewpoint)
        assert rh[0] > rh[1] > rh[2]

    def test_rh_clamped_to_0_100(self):
        """RH should be clamped between 0 and 100."""
        temp = np.array([20.0], dtype=np.float32)
        dewpoint = np.array([-50.0], dtype=np.float32)
        rh = compute_rh(temp, dewpoint)
        assert np.all(rh >= 0.0)
        assert np.all(rh <= 100.0)

    def test_known_values(self):
        """Test against known Arden Buck values."""
        # At 20°C with dewpoint of 10°C: e_s(10)/e_s(20) ≈ 0.5258 → ~52.58%
        temp = np.array([20.0], dtype=np.float32)
        dewpoint = np.array([10.0], dtype=np.float32)
        rh = compute_rh(temp, dewpoint)
        np.testing.assert_allclose(rh, 52.58, atol=0.1)

    def test_output_dtype_is_float32(self):
        """Output should be float32."""
        temp = np.array([20.0], dtype=np.float32)
        dewpoint = np.array([15.0], dtype=np.float32)
        rh = compute_rh(temp, dewpoint)
        assert rh.dtype == np.float32


class TestRHInterpolator:
    """Tests for RHInterpolator."""

    def test_interpolate_basic_success(self):
        """Test successful RH raster interpolation."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        temp_raster_path = f"/vsimem/temp_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 10, 10, extent, fill_value=1.0)
            create_test_raster(dem_path, 10, 10, extent, fill_value=100.0)
            create_test_raster(mask_path, 10, 10, extent, fill_value=1.0)
            create_test_raster(temp_raster_path, 10, 10, extent, fill_value=15.0)

            actuals = create_test_actuals(
                lats=[49.05, 49.08],
                lons=[-123.05, -123.02],
                dewpoints=[12.0, 11.0],
                elevations=[100.0, 200.0],
            )
            dewpoint_field = build_dewpoint_field(actuals)

            dataset = RHInterpolator(
                mask_path=mask_path,
                dem_path=dem_path,
                temp_raster_path=temp_raster_path,
                field=dewpoint_field,
            ).interpolate(ref_path)

            data = dataset.ds.GetRasterBand(1).ReadAsArray()
            nodata = dataset.ds.GetRasterBand(1).GetNoDataValue()

            assert data.shape == (10, 10)
            valid_count = np.sum(data != nodata)
            assert valid_count > 0, "Expected some interpolated RH values"

            valid_values = data[data != nodata]
            assert np.all(valid_values >= 0.0)
            assert np.all(valid_values <= 100.0)
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(temp_raster_path)
            gdal.Unlink(mask_path)

    def test_interpolate_skips_masked_cells(self):
        """Test that cells masked out by BC mask are skipped."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        temp_raster_path = f"/vsimem/temp_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(dem_path, 5, 5, extent, fill_value=100.0)
            create_test_raster(temp_raster_path, 5, 5, extent, fill_value=15.0)

            mask_data = np.full((5, 5), 1.0)
            mask_data[2, 2] = 0.0  # Masked cell
            create_test_raster(mask_path, 5, 5, extent, data=mask_data)

            actuals = create_test_actuals(
                lats=[49.05], lons=[-123.05], dewpoints=[12.0], elevations=[100.0]
            )
            dewpoint_field = build_dewpoint_field(actuals)

            dataset = RHInterpolator(
                mask_path=mask_path,
                dem_path=dem_path,
                temp_raster_path=temp_raster_path,
                field=dewpoint_field,
            ).interpolate(ref_path)

            data = dataset.ds.GetRasterBand(1).ReadAsArray()
            nodata = dataset.ds.GetRasterBand(1).GetNoDataValue()

            assert data[2, 2] == nodata
            valid_count = np.sum(data != nodata)
            assert valid_count == 24, "Expected 24 valid cells (25 - 1 masked)"
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(temp_raster_path)
            gdal.Unlink(mask_path)

    def test_output_preserves_reference_properties(self):
        """Test that output raster preserves reference raster properties."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        temp_raster_path = f"/vsimem/temp_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 8, 6, extent, fill_value=1.0)
            create_test_raster(dem_path, 8, 6, extent, fill_value=100.0)
            create_test_raster(temp_raster_path, 8, 6, extent, fill_value=15.0)
            create_test_raster(mask_path, 8, 6, extent, fill_value=1.0)

            actuals = create_test_actuals(
                lats=[49.05], lons=[-123.05], dewpoints=[12.0], elevations=[100.0]
            )
            dewpoint_field = build_dewpoint_field(actuals)

            dataset = RHInterpolator(
                mask_path=mask_path,
                dem_path=dem_path,
                temp_raster_path=temp_raster_path,
                field=dewpoint_field,
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
            gdal.Unlink(temp_raster_path)
            gdal.Unlink(mask_path)

    def test_rh_values_respond_to_elevation(self):
        """Test that RH varies with elevation since dew point is elevation-adjusted."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        temp_raster_path = f"/vsimem/temp_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(mask_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(temp_raster_path, 5, 5, extent, fill_value=15.0)

            dem_data = np.full((5, 5), 100.0)
            dem_data[0, 0] = 0.0  # Sea level
            dem_data[4, 4] = 1000.0  # 1000m elevation
            create_test_raster(dem_path, 5, 5, extent, data=dem_data)

            actuals = create_test_actuals(
                lats=[49.05], lons=[-123.05], dewpoints=[12.0], elevations=[100.0]
            )
            dewpoint_field = build_dewpoint_field(actuals)

            dataset = RHInterpolator(
                mask_path=mask_path,
                dem_path=dem_path,
                temp_raster_path=temp_raster_path,
                field=dewpoint_field,
            ).interpolate(ref_path)

            data = dataset.ds.GetRasterBand(1).ReadAsArray()
            nodata = dataset.ds.GetRasterBand(1).GetNoDataValue()

            rh_sea_level = data[0, 0]
            rh_high_elevation = data[4, 4]

            assert rh_sea_level != nodata
            assert rh_high_elevation != nodata
            # With a constant temp raster but elevation-adjusted dew point,
            # higher elevation = lower dew point = lower RH
            assert rh_high_elevation < rh_sea_level
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(temp_raster_path)
            gdal.Unlink(mask_path)

    def test_interpolate_raises_when_no_valid_stations(self):
        """Test that RuntimeError is raised when no stations have valid dew point values."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        temp_raster_path = f"/vsimem/temp_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(dem_path, 5, 5, extent, fill_value=100.0)
            create_test_raster(temp_raster_path, 5, 5, extent, fill_value=15.0)
            create_test_raster(mask_path, 5, 5, extent, fill_value=1.0)

            actuals = [
                SFMSDailyActual(code=1, lat=49.05, lon=-123.05, elevation=100.0, dewpoint=None)
            ]
            dewpoint_field = build_dewpoint_field(actuals)

            with pytest.raises(RuntimeError, match="No pixels were successfully interpolated"):
                RHInterpolator(
                    mask_path=mask_path,
                    dem_path=dem_path,
                    temp_raster_path=temp_raster_path,
                    field=dewpoint_field,
                ).interpolate(ref_path)
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(temp_raster_path)
            gdal.Unlink(mask_path)
