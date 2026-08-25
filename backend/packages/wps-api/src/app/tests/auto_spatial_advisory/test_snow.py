import os
import tempfile

import numpy as np
from osgeo import gdal, osr

from app.auto_spatial_advisory.snow import classify_snow_mask
from wps_shared.geospatial.wps_dataset import WPSDataset


def _make_raster(path: str, values, datatype, geotransform, projection_wkt, np_dtype=np.uint8):
    ds = gdal.GetDriverByName("GTiff").Create(path, 2, 2, 1, datatype)
    ds.SetGeoTransform(geotransform)
    ds.SetProjection(projection_wkt)
    ds.GetRasterBand(1).WriteArray(np.array(values, dtype=np_dtype))
    ds.FlushCache()
    return ds


def test_classify_snow_mask():
    """0 = snow covered (10 < NDSI <= 100), 1 = snow free / QA, preserving georeferencing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "snow.tif")
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        # values: 5 (below threshold), 50 (snow), 100 (snow, inclusive), 101 (above range/QA)
        source_ds = _make_raster(
            source_path,
            [[5, 50], [100, 101]],
            gdal.GDT_Float32,
            (0, 1, 0, 0, 0, -1),
            srs.ExportToWkt(),
            np_dtype=np.float32,
        )
        geotransform = source_ds.GetGeoTransform()
        projection = source_ds.GetProjection()
        source_ds = None

        with WPSDataset(source_path) as source, classify_snow_mask(source) as result:
            raw = result.as_gdal_ds()
            assert raw.GetRasterBand(1).ReadAsArray().tolist() == [[1, 0], [0, 1]]
            assert raw.GetRasterBand(1).DataType == gdal.GDT_Byte
            assert raw.GetGeoTransform() == geotransform
            assert raw.GetProjection() == projection
