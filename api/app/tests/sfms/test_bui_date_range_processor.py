from contextlib import ExitStack, contextmanager
from typing import List
from unittest.mock import AsyncMock
import pytest
from datetime import datetime, timezone
from osgeo import gdal
from pytest_mock import MockerFixture

from app.geospatial.wps_dataset import WPSDataset, multi_wps_dataset_context
from app.sfms.date_range_processor import BUIDateRangeProcessor
from app.sfms.raster_addresser import RasterKeyAddresser
from app.tests.geospatial.test_wps_dataset import create_test_dataset
from app.utils.s3_client import S3Client
import uuid

TEST_DATETIME = datetime(2024, 10, 10, 10, tzinfo=timezone.utc)


def create_mock_gdal_dataset():
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    return create_test_dataset(f"{str(uuid.uuid4())}.tif", 1, 1, extent, 4326, data_type=gdal.GDT_Byte, fill_value=1)


# Create a mock for the WPSDataset class
def create_mock_wps_dataset():
    mock_ds = create_mock_gdal_dataset()
    return WPSDataset(ds=mock_ds, ds_path=None)


@pytest.mark.anyio
async def test_bui_date_range_processor(mocker: MockerFixture):
    mock_key_addresser = RasterKeyAddresser()
    bui_date_range_processor = BUIDateRangeProcessor(TEST_DATETIME, 2, mock_key_addresser)
    # mock out storing of dataset
    mocker.patch.object(bui_date_range_processor, "_create_and_store_dataset", return_value="test_key.tif")

    # mock weather index, param datasets used for calculations
    mock_dc_ds = create_mock_wps_dataset()
    mock_dmc_ds = create_mock_wps_dataset()
    mock_temp_ds = create_mock_wps_dataset()
    mock_rh_ds = create_mock_wps_dataset()
    mock_precip_ds = create_mock_wps_dataset()

    @contextmanager
    def mock_input_dataset_context(_: List[str]):
        mock_input_datasets = [mock_temp_ds, mock_rh_ds, mock_precip_ds, mock_dc_ds, mock_dmc_ds]
        try:
            # Enter each dataset's context and yield the list of instances
            with ExitStack() as stack:
                yield [stack.enter_context(ds) for ds in mock_input_datasets]
        finally:
            # Close all datasets to ensure cleanup
            for ds in mock_input_datasets:
                ds.close()

    # mock new dmc and dc datasets
    mock_new_dmc_ds = create_mock_wps_dataset()
    mock_new_dc_ds = create_mock_wps_dataset()

    @contextmanager
    def mock_new_dmc_dc_datasets_context(_: List[str]):
        mock_input_datasets = [mock_new_dmc_ds, mock_new_dc_ds]
        try:
            # Enter each dataset's context and yield the list of instances
            with ExitStack() as stack:
                yield [stack.enter_context(ds) for ds in mock_input_datasets]
        finally:
            # Close all datasets to ensure cleanup
            for ds in mock_input_datasets:
                ds.close()

    # mock s3 client
    mock_s3_client = S3Client()
    mock_all_objects_exist = AsyncMock(return_value=True)
    mocker.patch.object(mock_s3_client, "all_objects_exist", new=mock_all_objects_exist)

    # mock gdal open
    mocker.patch("osgeo.gdal.Open", return_value=create_mock_gdal_dataset())

    await bui_date_range_processor.process_bui(mock_s3_client, mock_input_dataset_context, mock_new_dmc_dc_datasets_context)
    mock_all_objects_exist.assert_called()
