import os
import tempfile

import numpy as np
from osgeo import gdal, osr

from app.auto_spatial_advisory.snow import classify_snow_mask


def test_classify_snow_mask():
    """0 = snow covered (10 < NDSI <= 100), 1 = snow free / QA, preserving georeferencing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "snow.tif")

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        source_ds = gdal.GetDriverByName("GTiff").Create(source_path, 2, 2, 1, gdal.GDT_Float32)
        source_ds.SetGeoTransform((0, 1, 0, 0, 0, -1))
        source_ds.SetProjection(srs.ExportToWkt())
        # values: 5 (below threshold), 50 (snow), 100 (snow, inclusive), 101 (above range/QA)
        source_ds.GetRasterBand(1).WriteArray(
            np.array([[5, 50], [100, 101]], dtype=np.float32)
        )
        source_ds.FlushCache()
        geotransform = source_ds.GetGeoTransform()
        projection = source_ds.GetProjection()
        source_ds = None

        result_path = classify_snow_mask(source_path, temp_dir)

        result_ds = gdal.Open(result_path, gdal.GA_ReadOnly)
        result_band = result_ds.GetRasterBand(1)

        assert result_band.ReadAsArray().tolist() == [[1, 0], [0, 1]]
        assert result_band.DataType == gdal.GDT_Byte
        assert result_ds.GetGeoTransform() == geotransform
        assert result_ds.GetProjection() == projection
        result_ds = None
