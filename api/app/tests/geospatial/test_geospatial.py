import os
from wps_shared.geospatial.geospatial import rasters_match
from osgeo import gdal

raster1 = os.path.join(os.path.dirname(__file__), "3005_lats.tif")
raster2 = os.path.join(os.path.dirname(__file__), "4326_lats.tif")


def test_rasters_match():
    with gdal.Open(raster1) as r1, gdal.Open(raster1) as r2:
        match = rasters_match(r1, r2)
        assert match


def test_rasters_no_match_projection():
    with gdal.Open(raster1) as r1, gdal.Open(raster2) as r2:
        match = rasters_match(r1, r2)
        assert not match


def test_rasters_no_match_pixel_size():
    with gdal.Open(raster1) as r1:
        diff_r1 = gdal.Warp("/vsimem/mod.tif", r1, xRes=400, yRes=400, resampleAlg=gdal.GRA_NearestNeighbour)

        match = rasters_match(r1, diff_r1)
        assert not match


def test_rasters_no_match_extent():
    with gdal.Open(raster1) as r1:
        # Get the current geotransform
        geotransform = r1.GetGeoTransform()
        pixel_width = geotransform[1]
        pixel_height = geotransform[5]  # Typically negative

        # Slightly modify the extent (shift by one pixel)
        new_extent = (
            geotransform[0] + pixel_width,  # Shift left by 1 pixel
            geotransform[3] - pixel_height,  # Shift down by 1 pixel
            geotransform[0] + (r1.RasterXSize + 1) * pixel_width,  # Expand right
            geotransform[3] + (r1.RasterYSize + 1) * pixel_height,  # Expand bottom
        )

        diff_r1 = gdal.Translate("/vsimem/mod_extent.tif", r1, projWin=new_extent)

        match = rasters_match(r1, diff_r1)
        assert not match
