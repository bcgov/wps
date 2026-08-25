import os
import tempfile

import numpy as np
from osgeo import gdal, osr

from app.auto_spatial_advisory.classify_hfi import classify_hfi
from wps_shared.geospatial.wps_dataset import Georeference, WPSDataset


def test_classify_hfi():
    """0 = <4000, 1 = 4000-10000, 2 = >=10000, preserving the source's geotransform/projection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "source.tif")
        target_path = os.path.join(temp_dir, "classified.tif")

        source = WPSDataset.from_array(
            np.array([[1000, 5000], [11000, 0]], dtype=np.float32),
            Georeference((0, 100, 0, 0, 0, -100), osr.GetUserInputAsWKT("EPSG:3005")),
            output_path=source_path,
        )

        classify_hfi(source_path, target_path)

        with WPSDataset(target_path) as result:
            assert result.ds.GetRasterBand(1).ReadAsArray().tolist() == [[0, 1], [2, 0]]
            assert result.ds.GetRasterBand(1).DataType == gdal.GDT_Byte
            assert result.ds.GetRasterBand(1).GetNoDataValue() == 0
            assert result.georeference == source.georeference

        source.close()
