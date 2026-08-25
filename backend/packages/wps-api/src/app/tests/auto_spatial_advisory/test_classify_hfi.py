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


def test_classify_hfi_closes_every_dataset_it_opens(mocker):
    """Regression test: the WPSDataset.from_array() output is discarded immediately after
    writing to target_path, so it must be closed explicitly - nothing else references it to
    close it later, and a bare, unclosed call would leak its GDAL write handle."""
    close_spy = mocker.patch.object(WPSDataset, "close", wraps=WPSDataset.close, autospec=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "source.tif")
        target_path = os.path.join(temp_dir, "classified.tif")

        source = WPSDataset.from_array(
            np.array([[1000, 5000], [11000, 0]], dtype=np.float32),
            Georeference((0, 100, 0, 0, 0, -100), osr.GetUserInputAsWKT("EPSG:3005")),
            output_path=source_path,
        )
        source.close()
        close_spy.reset_mock()  # only interested in what classify_hfi() itself closes

        classify_hfi(source_path, target_path)

        # once for the `source_path` dataset classify_hfi opens for reading, once for the
        # from_array() dataset it writes target_path with.
        assert close_spy.call_count == 2
