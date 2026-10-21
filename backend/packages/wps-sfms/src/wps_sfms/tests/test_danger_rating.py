from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import numpy as np
import pytest
from osgeo import gdal
from wps_sfms.interpolation.field import ScalarField
from wps_sfms.processors.idw import Interpolator
from wps_sfms.tests.conftest import create_test_raster
from wps_shared.geospatial.wps_dataset import Georeference, WPSDataset


def test_danger_rating_interpolation_keeps_decimal_values_and_mask():
    test_id = uuid4().hex
    reference_path = f"/vsimem/danger_rating_reference_{test_id}.tif"
    mask_path = f"/vsimem/danger_rating_mask_{test_id}.tif"
    extent = (-123.1, -123.0, 49.0, 49.1)
    mask = np.ones((5, 5), dtype=np.float32)
    mask[0, 0] = 0
    field = ScalarField(
        np.array([49.05, 49.05], dtype=np.float32),
        np.array([-123.07, -123.03], dtype=np.float32),
        np.array([2.0, 3.0], dtype=np.float32),
    )

    try:
        create_test_raster(reference_path, 5, 5, extent)
        create_test_raster(mask_path, 5, 5, extent, data=mask)

        with Interpolator(mask_path, field).interpolate(reference_path) as result:
            values = result.read_array()
            nodata = result.require_nodata_value()
            assert values[0, 0] == nodata
            assert values[2, 2] == pytest.approx(2.5, abs=0.001)
            assert np.all((values[values != nodata] >= 2.0) & (values[values != nodata] <= 3.0))
    finally:
        gdal.Unlink(reference_path)
        gdal.Unlink(mask_path)


@pytest.mark.anyio
async def test_interpolator_uses_default_cog_resampling(mocker):
    dataset = WPSDataset.from_array(
        np.array([[2.0]], dtype=np.float32),
        Georeference((0, 1, 0, 0, 0, -1), ""),
        nodata_value=-9999.0,
    )
    field = ScalarField(np.array([49.0]), np.array([-123.0]), np.array([2.0]))
    processor = Interpolator("mask.tif", field)
    mocker.patch.object(processor, "interpolate", return_value=dataset)
    mocker.patch("wps_sfms.processors.idw.set_s3_gdal_config")
    publish = mocker.patch(
        "wps_sfms.processors.idw.publish_dataset",
        new_callable=AsyncMock,
        return_value=SimpleNamespace(output_key="output.tif", cog_key="output_cog.tif"),
    )
    s3_client = MagicMock()

    result = await processor.process(s3_client, "reference.tif", "output.tif")

    assert result == "output.tif"
    publish.assert_awaited_once_with(s3_client, dataset, "output.tif")
