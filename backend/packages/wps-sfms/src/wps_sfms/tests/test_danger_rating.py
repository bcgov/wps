from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import numpy as np
import pytest
from osgeo import gdal
from wps_sfms.interpolation.common import SFMS_NO_DATA
from wps_sfms.interpolation.field import ScalarField
from wps_sfms.processors.danger_rating import DangerRatingInterpolator
from wps_sfms.processors.idw import Interpolator
from wps_sfms.tests.conftest import create_test_raster
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.geospatial.wps_dataset import Georeference, WPSDataset


def test_danger_rating_interpolator_rounds_caps_and_preserves_nodata(mocker):
    nodata = SFMS_NO_DATA
    georeference = Georeference((0, 1, 0, 0, 0, -1), "")
    source = WPSDataset.from_array(
        np.array([[-1.0, 0.0, 0.49, 0.5, 1.5, 4.49, 4.5, 5.5, 9.0, nodata]], dtype=np.float32),
        georeference,
        nodata_value=nodata,
    )
    source.chunk_size = 3
    mocker.patch("wps_sfms.processors.idw.Interpolator.interpolate", return_value=source)
    field = ScalarField(np.array([49.0]), np.array([-123.0]), np.array([1.0]))

    with DangerRatingInterpolator("mask.tif", field).interpolate("reference.tif") as result:
        band = result.ds.GetRasterBand(1)
        assert band.DataType == gdal.GDT_Float32
        np.testing.assert_array_equal(
            result.read_array(),
            np.array([[0, 0, 0, 1, 2, 4, 5, 5, 5, nodata]], dtype=np.float32),
        )
        assert result.require_nodata_value() == pytest.approx(SFMS_NO_DATA)
        assert result.georeference == georeference


def test_danger_rating_interpolator_uses_idw_and_mask():
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

        with DangerRatingInterpolator(mask_path, field).interpolate(reference_path) as result:
            values = result.read_array()
            nodata = result.require_nodata_value()
            assert result.ds.GetRasterBand(1).DataType == gdal.GDT_Float32
            assert values[0, 0] == nodata
            assert nodata == pytest.approx(SFMS_NO_DATA)
            assert values[2, 2] == 3
            assert set(np.unique(values[values != nodata])) <= {2, 3}
    finally:
        gdal.Unlink(reference_path)
        gdal.Unlink(mask_path)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "processor_type,process_kwargs,resample_alg",
    [
        (
            DangerRatingInterpolator,
            {"cog_resample_alg": GDALResamplingMethod.NEAREST_NEIGHBOUR},
            GDALResamplingMethod.NEAREST_NEIGHBOUR,
        ),
        (Interpolator, {}, GDALResamplingMethod.BILINEAR),
    ],
)
async def test_interpolator_publishes_with_expected_cog_resampling(
    mocker, processor_type, process_kwargs, resample_alg
):
    dataset = WPSDataset.from_array(
        np.array([[2.0]], dtype=np.float32),
        Georeference((0, 1, 0, 0, 0, -1), ""),
        nodata_value=-9999.0,
    )
    field = ScalarField(np.array([49.0]), np.array([-123.0]), np.array([2.0]))
    processor = processor_type("mask.tif", field)
    mocker.patch.object(processor, "interpolate", return_value=dataset)
    mocker.patch("wps_sfms.processors.idw.set_s3_gdal_config")
    publish = mocker.patch(
        "wps_sfms.processors.idw.publish_dataset",
        new_callable=AsyncMock,
        return_value=SimpleNamespace(output_key="output.tif", cog_key="output_cog.tif"),
    )
    s3_client = MagicMock()

    result = await processor.process(s3_client, "reference.tif", "output.tif", **process_kwargs)

    assert result == "output.tif"
    publish.assert_awaited_once_with(
        s3_client, dataset, "output.tif", cog_resample_alg=resample_alg
    )
