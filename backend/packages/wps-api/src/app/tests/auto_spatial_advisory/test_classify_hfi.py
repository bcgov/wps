import os
import tempfile

import numpy as np
from osgeo import gdal, osr

from app.auto_spatial_advisory.classify_hfi import classify_hfi


def test_classify_hfi():
    """0 = <4000, 1 = 4000-10000, 2 = >=10000, preserving the source's geotransform/projection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "source.tif")
        target_path = os.path.join(temp_dir, "classified.tif")

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3005)
        source_ds = gdal.GetDriverByName("GTiff").Create(source_path, 2, 2, 1, gdal.GDT_Float32)
        source_ds.SetGeoTransform((0, 100, 0, 0, 0, -100))
        source_ds.SetProjection(srs.ExportToWkt())
        source_ds.GetRasterBand(1).WriteArray(
            np.array([[1000, 5000], [11000, 0]], dtype=np.float32)
        )
        source_ds.FlushCache()
        geotransform = source_ds.GetGeoTransform()
        projection = source_ds.GetProjection()
        source_ds = None

        classify_hfi(source_path, target_path)

        result_ds = gdal.Open(target_path, gdal.GA_ReadOnly)
        result_band = result_ds.GetRasterBand(1)

        assert result_band.ReadAsArray().tolist() == [[0, 1], [2, 0]]
        assert result_band.DataType == gdal.GDT_Byte
        assert result_band.GetNoDataValue() == 0
        assert result_ds.GetGeoTransform() == geotransform
        assert result_ds.GetProjection() == projection
        result_ds = None
