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


def test_classify_hfi_closes_the_from_array_output(mocker):
    """Regression test: the WPSDataset.from_array() output is discarded immediately after
    writing to target_path - nothing else references it to close it later - so a bare,
    unclosed call would leak its GDAL write handle."""
    from_array_spy = mocker.spy(WPSDataset, "from_array")

    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "source.tif")
        target_path = os.path.join(temp_dir, "classified.tif")

        source = WPSDataset.from_array(
            np.array([[1000, 5000], [11000, 0]], dtype=np.float32),
            Georeference((0, 100, 0, 0, 0, -100), osr.GetUserInputAsWKT("EPSG:3005")),
            output_path=source_path,
        )
        source.close()

        classify_hfi(source_path, target_path)

        # from_array_spy.spy_return is the WPSDataset classify_hfi wrote target_path with -
        # closed sets .ds to None, so a non-None .ds here means it leaked.
        output_ds = from_array_spy.spy_return
        assert output_ds.ds is None
