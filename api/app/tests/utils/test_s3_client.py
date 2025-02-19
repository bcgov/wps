from io import BufferedReader
import os
import tempfile
import pytest
from osgeo import gdal
from wps_shared.geospatial.wps_dataset import WPSDataset
from app.tests.dataset_common import create_mock_gdal_dataset
from wps_shared.utils.s3_client import S3Client
from pytest_mock import MockerFixture


@pytest.mark.anyio
async def test_put_object_called(mocker: MockerFixture):
    async with S3Client() as s3_client:
        persist_raster_spy = mocker.patch.object(s3_client, "put_object")
        mock_ds = create_mock_gdal_dataset()
        mock_band: gdal.Band = mock_ds.GetRasterBand(1)
        values = mock_band.ReadAsArray()
        no_data_value = mock_band.GetNoDataValue()

        with tempfile.TemporaryDirectory() as temp_dir:
            with WPSDataset.from_array(values, mock_ds.GetGeoTransform(), mock_ds.GetProjection(), no_data_value) as expected_ds:
                expected_key = "expected_key"
                expected_filename = os.path.join(temp_dir, os.path.basename("expected_key"))
                expected_ds.export_to_geotiff(expected_filename)
                await s3_client.persist_raster_data(temp_dir, expected_key, mock_ds.GetGeoTransform(), mock_ds.GetProjection(), values, no_data_value)

                assert persist_raster_spy.call_args_list == [mocker.call(key=expected_key, body=mocker.ANY)]
                assert isinstance(persist_raster_spy.call_args.kwargs["body"], BufferedReader)
