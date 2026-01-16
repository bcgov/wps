"""
Unit tests for precipitation interpolation module.
"""

import numpy as np
import uuid
from osgeo import gdal, osr
from wps_sfms.interpolation.precipitation import interpolate_to_raster


def create_test_raster(path: str, width: int, height: int, extent: tuple, epsg: int = 4326, fill_value: float = 1.0, nodata: float = -9999.0):
    """
    Create a test GeoTIFF raster in memory using GDAL's /vsimem/ filesystem.

    :param path: Output path (should use /vsimem/ prefix)
    :param width: Raster width in pixels
    :param height: Raster height in pixels
    :param extent: (xmin, xmax, ymin, ymax)
    :param epsg: EPSG code for projection
    :param fill_value: Value to fill raster with
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
    band.WriteArray(np.full((height, width), fill_value, dtype=np.float32))
    band.FlushCache()

    ds = None  # Close dataset


class TestInterpolateToRaster:
    """Tests for interpolate_to_raster function."""

    def test_interpolation_produces_valid_output(self):
        """Test that interpolation creates an output raster with interpolated values."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        output_path = f"/vsimem/output_{test_id}.tif"

        try:
            # Create a small reference raster centered near Vancouver
            # Extent covers roughly 49.0-49.1 lat, -123.1 to -123.0 lon
            create_test_raster(ref_path, 10, 10, (-123.1, -123.0, 49.0, 49.1), epsg=4326)

            # Station data within the raster extent
            station_lats = [49.05, 49.08]
            station_lons = [-123.05, -123.02]
            station_values = [10.0, 20.0]

            result = interpolate_to_raster(
                station_lats,
                station_lons,
                station_values,
                ref_path,
                output_path,
            )

            assert result == output_path

            # Read output and verify
            ds = gdal.Open(output_path)
            assert ds is not None

            data = ds.GetRasterBand(1).ReadAsArray()
            nodata = ds.GetRasterBand(1).GetNoDataValue()

            # Should have same dimensions as reference
            assert data.shape == (10, 10)

            # Should have some interpolated values (not all nodata)
            valid_count = np.sum(data != nodata)
            assert valid_count > 0, "Expected some interpolated values"

            # Interpolated values should be in range of station values
            valid_values = data[data != nodata]
            assert np.all(valid_values >= 10.0 - 0.1)
            assert np.all(valid_values <= 20.0 + 0.1)

            ds = None
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(output_path)

    def test_zero_values_interpolated_correctly(self):
        """Test that zero precipitation values are interpolated as 0.0, not nodata."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        output_path = f"/vsimem/output_{test_id}.tif"

        try:
            create_test_raster(ref_path, 5, 5, (-123.1, -123.0, 49.0, 49.1), epsg=4326)

            # All stations have zero precipitation
            station_lats = [49.05, 49.08]
            station_lons = [-123.05, -123.02]
            station_values = [0.0, 0.0]

            result = interpolate_to_raster(
                station_lats,
                station_lons,
                station_values,
                ref_path,
                output_path,
            )

            assert result == output_path

            ds = gdal.Open(output_path)
            data = ds.GetRasterBand(1).ReadAsArray()
            nodata = ds.GetRasterBand(1).GetNoDataValue()

            # Interpolated values should be 0.0, not nodata
            valid_values = data[data != nodata]
            assert len(valid_values) > 0, "Expected some interpolated values"
            assert np.allclose(valid_values, 0.0), "Zero values should interpolate to 0.0"

            ds = None
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(output_path)

    def test_single_station_interpolation(self):
        """Test interpolation with a single station."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        output_path = f"/vsimem/output_{test_id}.tif"

        try:
            create_test_raster(ref_path, 5, 5, (-123.1, -123.0, 49.0, 49.1), epsg=4326)

            # Single station
            station_lats = [49.05]
            station_lons = [-123.05]
            station_values = [15.0]

            result = interpolate_to_raster(
                station_lats,
                station_lons,
                station_values,
                ref_path,
                output_path,
            )

            assert result == output_path

            ds = gdal.Open(output_path)
            data = ds.GetRasterBand(1).ReadAsArray()
            nodata = ds.GetRasterBand(1).GetNoDataValue()

            # With single station, all interpolated values should equal station value
            valid_values = data[data != nodata]
            assert len(valid_values) > 0
            assert np.allclose(valid_values, 15.0)

            ds = None
        finally:
            gdal.Unlink(ref_path)
            gdal.Unlink(output_path)

    def test_output_preserves_reference_properties(self):
        """Test that output raster preserves reference raster properties."""
        test_id = uuid.uuid4().hex
        ref_path = f"/vsimem/reference_{test_id}.tif"
        output_path = f"/vsimem/output_{test_id}.tif"

        try:
            extent = (-123.1, -123.0, 49.0, 49.1)
            create_test_raster(ref_path, 8, 6, extent, epsg=4326)

            station_lats = [49.05]
            station_lons = [-123.05]
            station_values = [10.0]

            interpolate_to_raster(
                station_lats,
                station_lons,
                station_values,
                ref_path,
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
            gdal.Unlink(output_path)
