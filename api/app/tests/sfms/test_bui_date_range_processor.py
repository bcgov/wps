import pytest
from datetime import datetime, timezone

from pytest_mock import MockerFixture

from app.sfms.date_range_processor import BUIDateRangeProcessor
from app.sfms.raster_addresser import RasterKeyAddresser

TEST_DATETIME = datetime(2024, 10, 10, 10, tzinfo=timezone.utc)


@pytest.mark.anyio
async def test_bui_drp(mocker: MockerFixture):
    mock_key_addresser = RasterKeyAddresser()
    mocker.patch.object(mock_key_addresser, "get_weather_data_keys", return_value=("temp_key", "rh_key", "wind_speed_key", "precip_key"))
    bui_date_range_processor = BUIDateRangeProcessor(TEST_DATETIME, 2, mock_key_addresser)
    await bui_date_range_processor.process_bui()
    # TODO mock s3 client, bucket
