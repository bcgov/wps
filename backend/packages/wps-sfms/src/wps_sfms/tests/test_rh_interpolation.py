"""
Unit tests for relative humidity interpolation module.
"""

import numpy as np
import uuid
from typing import Optional
from osgeo import gdal, osr
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_sfms.interpolation.source import StationDewPointSource
from wps_sfms.interpolation.relative_humidity import interpolate_rh_to_raster


def create_test_raster(
    path: str,
    width: int,
    height: int,
    extent: tuple,
    data: Optional[np.ndarray] = None,
    epsg: int = 4326,
    fill_value: float = 1.0,
    nodata: float = -9999.0,
):
    """
    Create a test GeoTIFF raster in memory using GDAL's /vsimem/ filesystem.
    """
    driver: gdal.Driver = gdal.GetDriverByName("GTiff")
    ds: gdal.Dataset = driver.Create(path, width, height, 1, gdal.GDT_Float32)

    xmin, xmax, ymin, ymax = extent
    xres = (xmax - xmin) / width
    yres = (ymax - ymin) / height
    ds.SetGeoTransform((xmin, xres, 0, ymax, 0, -yres))

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    ds.SetProjection(srs.ExportToWkt())

    band: gdal.Band = ds.GetRasterBand(1)
    band.SetNoDataValue(nodata)

    if data is not None:
        band.WriteArray(data.astype(np.float32))
    else:
        band.WriteArray(np.full((height, width), fill_value, dtype=np.float32))
    band.FlushCache()

    ds = None


def create_test_actuals(lats, lons, temps, rhs, elevations):
    """Create test SFMSDailyActual objects with temperature and relative humidity."""
    actuals = []
    for i, (lat, lon, temp, rh, elev) in enumerate(zip(lats, lons, temps, rhs, elevations)):
        actual = SFMSDailyActual(
            code=100 + i,
            lat=lat,
            lon=lon,
            elevation=elev,
            temperature=temp,
            relative_humidity=rh,
            precipitation=None,
            wind_speed=None,
        )
        actuals.append(actual)
    return actuals


class TestComputeRHFromTempAndDewpoint:
    """Tests for the Magnus formula RH computation."""

    def test_dewpoint_equals_temp_gives_100_percent(self):
        """When dew point equals temperature, RH should be 100%."""
        temp = np.array([20.0, 10.0, 0.0], dtype=np.float32)
        dewpoint = np.array([20.0, 10.0, 0.0], dtype=np.float32)
        rh = StationDewPointSource.compute_rh(temp, dewpoint)
        np.testing.assert_allclose(rh, 100.0, atol=0.01)

    def test_lower_dewpoint_gives_lower_rh(self):
        """Lower dew point relative to temperature should give lower RH."""
        temp = np.array([20.0, 20.0, 20.0], dtype=np.float32)
        dewpoint = np.array([20.0, 15.0, 10.0], dtype=np.float32)
        rh = StationDewPointSource.compute_rh(temp, dewpoint)
        assert rh[0] > rh[1] > rh[2]

    def test_rh_clamped_to_0_100(self):
        """RH should be clamped between 0 and 100."""
        temp = np.array([20.0], dtype=np.float32)
        dewpoint = np.array([-50.0], dtype=np.float32)
        rh = StationDewPointSource.compute_rh(temp, dewpoint)
        assert np.all(rh >= 0.0)
        assert np.all(rh <= 100.0)

    def test_known_values(self):
        """Test against known meteorological values."""
        # At 20°C with dewpoint of 10°C, RH should be approximately 52%
        temp = np.array([20.0], dtype=np.float32)
        dewpoint = np.array([10.0], dtype=np.float32)
        rh = StationDewPointSource.compute_rh(temp, dewpoint)
        assert 50.0 < rh[0] < 55.0

    def test_output_dtype_is_float32(self):
        """Output should be float32."""
        temp = np.array([20.0], dtype=np.float32)
        dewpoint = np.array([15.0], dtype=np.float32)
        rh = StationDewPointSource.compute_rh(temp, dewpoint)
        assert rh.dtype == np.float32


class TestInterpolateRHToRaster:
    """Tests for interpolate_rh_to_raster function."""

    def test_interpolate_basic_success(self):
        """Test successful RH raster interpolation."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        temp_raster_path = f"/vsimem/temp_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"
        output_path = f"/vsimem/output_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 10, 10, extent, fill_value=1.0)
            create_test_raster(dem_path, 10, 10, extent, fill_value=100.0)
            create_test_raster(mask_path, 10, 10, extent, fill_value=1.0)
            # Create a temperature raster with uniform 15°C
            create_test_raster(temp_raster_path, 10, 10, extent, fill_value=15.0)

            # Create stations within extent with temp=20°C and RH=60%
            actuals = create_test_actuals(
                lats=[49.05, 49.08],
                lons=[-123.05, -123.02],
                temps=[20.0, 18.0],
                rhs=[60.0, 65.0],
                elevations=[100.0, 200.0],
            )
            dewpoint_source = StationDewPointSource(actuals)

            result = interpolate_rh_to_raster(
                dewpoint_source,
                temp_raster_path,
                ref_path,
                dem_path,
                output_path,
                mask_path=mask_path,
            )

            assert result == output_path

            ds = gdal.Open(output_path)
            assert ds is not None
            data = ds.GetRasterBand(1).ReadAsArray()
            nodata = ds.GetRasterBand(1).GetNoDataValue()

            assert data.shape == (10, 10)
            valid_count = np.sum(data != nodata)
            assert valid_count > 0, "Expected some interpolated RH values"

            # RH values should be in valid range
            valid_values = data[data != nodata]
            assert np.all(valid_values >= 0.0)
            assert np.all(valid_values <= 100.0)

            ds = None
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(temp_raster_path)
            gdal.Unlink(mask_path)
            gdal.Unlink(output_path)

    def test_interpolate_skips_masked_cells(self):
        """Test that cells masked out by BC mask are skipped."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        temp_raster_path = f"/vsimem/temp_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"
        output_path = f"/vsimem/output_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(dem_path, 5, 5, extent, fill_value=100.0)
            create_test_raster(temp_raster_path, 5, 5, extent, fill_value=15.0)

            mask_data = np.full((5, 5), 1.0)
            mask_data[2, 2] = 0.0  # Masked cell
            create_test_raster(mask_path, 5, 5, extent, data=mask_data)

            actuals = create_test_actuals(
                lats=[49.05],
                lons=[-123.05],
                temps=[20.0],
                rhs=[60.0],
                elevations=[100.0],
            )
            dewpoint_source = StationDewPointSource(actuals)

            result = interpolate_rh_to_raster(
                dewpoint_source,
                temp_raster_path,
                ref_path,
                dem_path,
                output_path,
                mask_path=mask_path,
            )

            assert result == output_path

            ds = gdal.Open(output_path)
            data = ds.GetRasterBand(1).ReadAsArray()
            nodata = ds.GetRasterBand(1).GetNoDataValue()

            # The cell at (2,2) should be nodata in output
            assert data[2, 2] == nodata
            valid_count = np.sum(data != nodata)
            assert valid_count == 24, "Expected 24 valid cells (25 - 1 masked)"

            ds = None
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(temp_raster_path)
            gdal.Unlink(mask_path)
            gdal.Unlink(output_path)

    def test_output_preserves_reference_properties(self):
        """Test that output raster preserves reference raster properties."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        temp_raster_path = f"/vsimem/temp_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"
        output_path = f"/vsimem/output_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 8, 6, extent, fill_value=1.0)
            create_test_raster(dem_path, 8, 6, extent, fill_value=100.0)
            create_test_raster(temp_raster_path, 8, 6, extent, fill_value=15.0)
            create_test_raster(mask_path, 8, 6, extent, fill_value=1.0)

            actuals = create_test_actuals(
                lats=[49.05],
                lons=[-123.05],
                temps=[20.0],
                rhs=[60.0],
                elevations=[100.0],
            )
            dewpoint_source = StationDewPointSource(actuals)

            interpolate_rh_to_raster(
                dewpoint_source,
                temp_raster_path,
                ref_path,
                dem_path,
                output_path,
                mask_path=mask_path,
            )

            ref_ds = gdal.Open(ref_path)
            out_ds = gdal.Open(output_path)

            assert out_ds.RasterXSize == ref_ds.RasterXSize
            assert out_ds.RasterYSize == ref_ds.RasterYSize
            assert out_ds.GetGeoTransform() == ref_ds.GetGeoTransform()
            assert out_ds.GetProjection() == ref_ds.GetProjection()

            ref_ds = None
            out_ds = None
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(temp_raster_path)
            gdal.Unlink(mask_path)
            gdal.Unlink(output_path)

    def test_rh_values_respond_to_elevation(self):
        """Test that RH varies with elevation since dew point is elevation-adjusted."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        temp_raster_path = f"/vsimem/temp_{test_id}.tif"
        mask_path = f"/vsimem/mask_{test_id}.tif"
        output_path = f"/vsimem/output_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)
            create_test_raster(mask_path, 5, 5, extent, fill_value=1.0)

            # DEM with varying elevation
            dem_data = np.full((5, 5), 100.0)
            dem_data[0, 0] = 0.0  # Sea level
            dem_data[4, 4] = 1000.0  # 1000m elevation
            create_test_raster(dem_path, 5, 5, extent, data=dem_data)

            # Temperature raster with uniform value
            create_test_raster(temp_raster_path, 5, 5, extent, fill_value=15.0)

            actuals = create_test_actuals(
                lats=[49.05],
                lons=[-123.05],
                temps=[20.0],
                rhs=[60.0],
                elevations=[100.0],
            )
            dewpoint_source = StationDewPointSource(actuals)

            interpolate_rh_to_raster(
                dewpoint_source,
                temp_raster_path,
                ref_path,
                dem_path,
                output_path,
                mask_path=mask_path,
            )

            ds = gdal.Open(output_path)
            data = ds.GetRasterBand(1).ReadAsArray()
            nodata = ds.GetRasterBand(1).GetNoDataValue()

            # RH at different elevations should differ since dew point is elevation-adjusted
            rh_sea_level = data[0, 0]
            rh_high_elevation = data[4, 4]

            assert rh_sea_level != nodata
            assert rh_high_elevation != nodata
            # With a constant temp raster but elevation-adjusted dew point,
            # higher elevation = lower dew point = lower RH
            assert rh_high_elevation < rh_sea_level

            ds = None
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(temp_raster_path)
            gdal.Unlink(mask_path)
            gdal.Unlink(output_path)
