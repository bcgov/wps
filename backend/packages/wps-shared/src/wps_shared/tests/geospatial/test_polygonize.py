import os
import tempfile

import numpy as np
import pytest
from osgeo import gdal, osr

from wps_shared.geospatial.polygonize import polygonize_in_memory


def test_polygonize_in_memory():
    """Polygonizes a raster's valid (non-nodata) region into vector features."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "source.tif")

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3005)
        ds = gdal.GetDriverByName("GTiff").Create(path, 4, 4, 1, gdal.GDT_Byte)
        ds.SetGeoTransform((0, 1, 0, 4, 0, -1))  # 1x1 unit pixels
        ds.SetProjection(srs.ExportToWkt())
        # A 2x2 block of valid data (value 5) surrounded by nodata (0).
        data = np.array(
            [
                [0, 0, 0, 0],
                [0, 5, 5, 0],
                [0, 5, 5, 0],
                [0, 0, 0, 0],
            ],
            dtype=np.uint8,
        )
        band = ds.GetRasterBand(1)
        band.SetNoDataValue(0)
        band.WriteArray(data)
        ds.FlushCache()
        ds = None

        with polygonize_in_memory(path, "test_layer", "value") as layer:
            feature_count = layer.GetFeatureCount()
            assert feature_count >= 1

            total_area = 0.0
            for i in range(feature_count):
                feature = layer.GetFeature(i)
                geometry = feature.GetGeometryRef()
                total_area += geometry.GetArea()
            # 4 valid (non-nodata) pixels at 1x1 unit each -> 4 square units of polygonized area.
            assert total_area == pytest.approx(4.0)
