"""
Unit tests for temperature interpolation module.
"""

import numpy as np
import uuid
from typing import Optional
from osgeo import gdal, osr
from wps_shared.schemas.sfms import SFMSDailyActual
from wps_sfms.interpolation.source import StationTemperatureSource
from wps_sfms.interpolation.temperature import interpolate_temperature_to_raster


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

    :param path: Output path (should use /vsimem/ prefix)
    :param width: Raster width in pixels
    :param height: Raster height in pixels
    :param extent: (xmin, xmax, ymin, ymax)
    :param data: Optional numpy array for raster data, defaults to fill_value
    :param epsg: EPSG code for projection
    :param fill_value: Value to fill raster with if data not provided
    :param nodata: NoData value
    :return: None
    """
    driver = gdal.GetDriverByName("GTiff")
    ds = driver.Create(path, width, height, 1, gdal.GDT_Float32)

    xmin, xmax, ymin, ymax = extent
    xres = (xmax - xmin) / width
    yres = (ymax - ymin) / height
    ds.SetGeoTransform((xmin, xres, 0, ymax, 0, -yres))

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    ds.SetProjection(srs.ExportToWkt())

    band = ds.GetRasterBand(1)
    band.SetNoDataValue(nodata)

    if data is not None:
        band.WriteArray(data.astype(np.float32))
    else:
        band.WriteArray(np.full((height, width), fill_value, dtype=np.float32))
    band.FlushCache()

    ds = None  # Close dataset


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


class TestInterpolateTemperatureToRaster:
    """Tests for interpolate_temperature_to_raster function."""

    def test_interpolate_basic_success(self):
        """Test successful raster interpolation."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        output_path = f"/vsimem/output_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            # Create reference and DEM rasters
            create_test_raster(ref_path, 10, 10, extent, fill_value=1.0)
            # DEM with uniform 100m elevation
            create_test_raster(dem_path, 10, 10, extent, fill_value=100.0)

            # Create stations within extent
            actuals = create_test_actuals(
                lats=[49.05, 49.08],
                lons=[-123.05, -123.02],
                temps=[15.0, 12.0],
                elevations=[100.0, 200.0],
            )
            temperature_source = StationTemperatureSource(actuals)

            result = interpolate_temperature_to_raster(
                temperature_source,
                ref_path,
                dem_path,
                output_path,
            )

            assert result == output_path

            # Verify output raster
            ds = gdal.Open(output_path)
            assert ds is not None
            data = ds.GetRasterBand(1).ReadAsArray()
            nodata = ds.GetRasterBand(1).GetNoDataValue()

            assert data.shape == (10, 10)
            valid_count = np.sum(data != nodata)
            assert valid_count > 0, "Expected some interpolated values"

            ds = None
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(output_path)

    def test_interpolate_skips_nodata_cells(self):
        """Test that cells with NoData elevation are skipped."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        output_path = f"/vsimem/output_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)

            # DEM with one NoData cell
            dem_data = np.full((5, 5), 100.0)
            dem_data[2, 2] = -9999.0  # NoData cell
            create_test_raster(dem_path, 5, 5, extent, data=dem_data)

            actuals = create_test_actuals(
                lats=[49.05],
                lons=[-123.05],
                temps=[15.0],
                elevations=[100.0],
            )
            temperature_source = StationTemperatureSource(actuals)

            result = interpolate_temperature_to_raster(
                temperature_source,
                ref_path,
                dem_path,
                output_path,
            )

            assert result == output_path

            # Verify the NoData cell in DEM results in NoData in output
            ds = gdal.Open(output_path)
            data = ds.GetRasterBand(1).ReadAsArray()
            nodata = ds.GetRasterBand(1).GetNoDataValue()

            # The cell at (2,2) should be nodata in output
            assert data[2, 2] == nodata
            # Other cells should have values
            valid_count = np.sum(data != nodata)
            assert valid_count == 24, "Expected 24 valid cells (25 - 1 nodata)"

            ds = None
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(output_path)

    def test_interpolate_with_elevation_adjustment(self):
        """Test that temperature is adjusted based on elevation."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        output_path = f"/vsimem/output_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 5, 5, extent, fill_value=1.0)

            # DEM with varying elevation
            dem_data = np.full((5, 5), 100.0)
            dem_data[0, 0] = 0.0  # Sea level
            dem_data[4, 4] = 1000.0  # 1000m elevation
            create_test_raster(dem_path, 5, 5, extent, data=dem_data)

            # Single station at 100m with 15C
            # Sea-level adjusted temp = 15 + 100 * 0.0065 = 15.65C
            actuals = create_test_actuals(
                lats=[49.05],
                lons=[-123.05],
                temps=[15.0],
                elevations=[100.0],
            )
            temperature_source = StationTemperatureSource(actuals)

            result = interpolate_temperature_to_raster(
                temperature_source,
                ref_path,
                dem_path,
                output_path,
            )

            assert result == output_path

            ds = gdal.Open(output_path)
            data = ds.GetRasterBand(1).ReadAsArray()

            # At sea level (0m): temp = 15.65 - 0 * 0.0065 = 15.65C
            # At 100m: temp = 15.65 - 100 * 0.0065 = 15.0C
            # At 1000m: temp = 15.65 - 1000 * 0.0065 = 9.15C
            sea_level_temp = data[0, 0]
            mid_elevation_temp = data[2, 2]  # 100m
            high_elevation_temp = data[4, 4]  # 1000m

            # Higher elevation should have lower temperature
            assert high_elevation_temp < mid_elevation_temp < sea_level_temp
            # Check approximate values (lapse rate = 6.5C per 1000m)
            assert np.isclose(sea_level_temp, 15.65, atol=0.5)
            assert np.isclose(high_elevation_temp, 9.15, atol=0.5)

            ds = None
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(output_path)

    def test_output_preserves_reference_properties(self):
        """Test that output raster preserves reference raster properties."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        dem_path = f"/vsimem/dem_{test_id}.tif"
        output_path = f"/vsimem/output_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 8, 6, extent, fill_value=1.0)
            create_test_raster(dem_path, 8, 6, extent, fill_value=100.0)

            actuals = create_test_actuals(
                lats=[49.05],
                lons=[-123.05],
                temps=[15.0],
                elevations=[100.0],
            )
            temperature_source = StationTemperatureSource(actuals)

            interpolate_temperature_to_raster(
                temperature_source,
                ref_path,
                dem_path,
                output_path,
            )

            ref_ds = gdal.Open(ref_path)
            out_ds = gdal.Open(output_path)

            # Same dimensions
            assert out_ds.RasterXSize == ref_ds.RasterXSize
            assert out_ds.RasterYSize == ref_ds.RasterYSize

            # Same geotransform
            assert out_ds.GetGeoTransform() == ref_ds.GetGeoTransform()

            # Same projection
            assert out_ds.GetProjection() == ref_ds.GetProjection()

            ref_ds = None
            out_ds = None
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(dem_path)
            gdal.Unlink(output_path)
