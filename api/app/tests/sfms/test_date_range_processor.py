from unittest.mock import AsyncMock, call
import uuid
import pytest
from datetime import datetime, timedelta, timezone

from pytest_mock import MockerFixture

from app.geospatial.wps_dataset import WPSDataset, multi_wps_dataset_context
from app.sfms.date_range_processor import BUIDateRangeProcessor
from app.sfms.raster_addresser import FWIParameter, RasterKeyAddresser
from osgeo import gdal

from app.tests.geospatial.test_wps_dataset import create_test_dataset
from app.utils.s3_client import S3Client


TEST_START_DATETIME = datetime(2024, 10, 10, 10, tzinfo=timezone.utc)
TEST_NUM_DAYS = 2


def create_mock_gdal_dataset():
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    return create_test_dataset(f"{str(uuid.uuid4())}.tif", 1, 1, extent, 4326, data_type=gdal.GDT_Byte, fill_value=1)


# Create a mock for the WPSDataset class
def create_mock_wps_dataset():
    mock_ds = create_mock_gdal_dataset()
    return WPSDataset(ds=mock_ds, ds_path=None)


# def test_addresser_called_correctly():
def test_get_previous_fwi_keys_first_day():
    processor = BUIDateRangeProcessor(TEST_START_DATETIME, TEST_NUM_DAYS, RasterKeyAddresser())
    # test the _get_previous_fwi_keys method for the first day
    day = 0

    dc_key, dmc_key = processor._get_previous_fwi_keys(day, TEST_START_DATETIME)

    # Day 0 fwi keys should come from the sfms uploads dir
    assert "uploads" in dc_key
    assert "uploads" in dmc_key


def test_get_previous_fwi_keys_subsequent_day():
    processor = BUIDateRangeProcessor(TEST_START_DATETIME, TEST_NUM_DAYS, RasterKeyAddresser())
    # test the _get_previous_fwi_keys method for the second day

    day = 1

    dc_key, dmc_key = processor._get_previous_fwi_keys(day, TEST_START_DATETIME)

    # Day 1 fwi keys should come from the sfms calculated dir
    assert "calculated" in dc_key
    assert "calculated" in dmc_key


def test_get_calculate_dates():
    processor = BUIDateRangeProcessor(TEST_START_DATETIME, TEST_NUM_DAYS, RasterKeyAddresser())

    # Day 0
    datetime_to_calc, prev_fwi_date, prediction_hour = processor._get_calculate_dates(0)
    assert datetime_to_calc == datetime(2024, 10, 10, 20, tzinfo=timezone.utc)  # start on the 20th hour of the start day
    assert prev_fwi_date == datetime_to_calc - timedelta(days=1)  # the previous fwi date should be 1 day before the date to calculate
    assert prediction_hour == 20  # predicting for UTC hour 20

    # Day 1
    datetime_to_calc, prev_fwi_date, prediction_hour = processor._get_calculate_dates(1)
    assert datetime_to_calc == datetime(2024, 10, 11, 20, tzinfo=timezone.utc)
    assert prev_fwi_date == datetime_to_calc - timedelta(days=1)
    assert prediction_hour == 44  # add 24 hours to our prediction hour

    # Day 2
    datetime_to_calc, prev_fwi_date, prediction_hour = processor._get_calculate_dates(2)
    assert datetime_to_calc == datetime(2024, 10, 12, 20, tzinfo=timezone.utc)
    assert prev_fwi_date == datetime_to_calc - timedelta(days=1)
    assert prediction_hour == 68  # add 24 hours to our prediction hour


@pytest.mark.anyio
async def test_bui_date_range_processor_addresser_calls(mocker: MockerFixture):
    mock_key_addresser = RasterKeyAddresser()
    bui_date_range_processor = BUIDateRangeProcessor(TEST_START_DATETIME, 2, mock_key_addresser)
    # mock out storing of dataset
    mocker.patch.object(bui_date_range_processor, "_create_and_store_dataset", return_value="test_key.tif")

    # mock s3 client
    mock_s3_client = S3Client()
    mock_all_objects_exist = AsyncMock(return_value=True)
    mocker.patch.object(mock_s3_client, "all_objects_exist", new=mock_all_objects_exist)

    # mock gdal open
    mocker.patch("osgeo.gdal.Open", return_value=create_mock_gdal_dataset())

    mock_get_weather_data_keys = mocker.patch.object(mock_key_addresser, "get_weather_data_keys", return_value=("temp_key", "rh_key", "ws_key", "precip_key"))
    mock_get_uploaded_data_keys = mocker.patch.object(mock_key_addresser, "get_uploaded_index_key", return_value=("uploaded_dc_key", "uploaded_dmc_key"))
    mock_get_calc_data_keys = mocker.patch.object(mock_key_addresser, "get_calculated_index_key", return_value=("calculated_dc_key", "calculated_dmc_key"))
    spy = mocker.spy(bui_date_range_processor, "_get_calculate_dates")

    # process bui
    await bui_date_range_processor.process_bui(mock_s3_client, multi_wps_dataset_context, multi_wps_dataset_context)

    # day arguments from the call_args_list
    days_called = [args[0][0] for args in spy.call_args_list]

    # check if days were called as expected
    expected_days = list(range(TEST_NUM_DAYS))
    assert days_called == expected_days

    get_calculate_dates = spy.spy_return_list

    weather_expected_calls = []
    for day in days_called:
        datetime_to_calculate_utc, previous_fwi_datetime, prediction_hour = get_calculate_dates[day]

        get_weather_data_expected_args = (TEST_START_DATETIME, datetime_to_calculate_utc, prediction_hour)
        weather_expected_calls.append(call(*get_weather_data_expected_args))

        fwi_expected_calls = [
            call(previous_fwi_datetime, FWIParameter.DC),
            call(previous_fwi_datetime, FWIParameter.DMC),
        ]
        if day == 0:  # assert day 0 gets previous uploaded fwi
            mock_get_uploaded_data_keys.assert_has_calls(fwi_expected_calls, any_order=False)
        else:  # else assert it gets calculated fwi keys
            mock_get_calc_data_keys.assert_has_calls(fwi_expected_calls, any_order=False)

    mock_get_weather_data_keys.assert_has_calls(weather_expected_calls, any_order=False)
    assert mock_get_weather_data_keys.call_count == len(weather_expected_calls)
