from app.sfms.raster_addresser import RasterKeyAddresser, FWIParameter
import pytest
from datetime import datetime, timezone

TEST_DATETIME_1 = datetime(2024, 10, 10, 23, tzinfo=timezone.utc)
TEST_DATE_1_ISO = TEST_DATETIME_1.date().isoformat()

TEST_DATETIME_TO_CALC = TEST_DATETIME_1.replace(hour=20)


@pytest.fixture
def raster_key_addresser():
    return RasterKeyAddresser()


def test_get_uploaded_index_key(raster_key_addresser):
    result = raster_key_addresser.get_uploaded_index_key(TEST_DATETIME_1, FWIParameter.DMC)
    assert result == f"sfms/uploads/actual/{TEST_DATE_1_ISO}/dmc{TEST_DATE_1_ISO.replace('-','')}.tif"


def test_get_calculated_index_key(raster_key_addresser):
    result = raster_key_addresser.get_calculated_index_key(TEST_DATETIME_1, FWIParameter.DC)
    assert result == f"sfms/calculated/forecast/{TEST_DATE_1_ISO}/dc{TEST_DATE_1_ISO.replace('-', '')}.tif"


def test_get_weather_data_keys(raster_key_addresser):
    result = raster_key_addresser.get_weather_data_keys(TEST_DATETIME_1, TEST_DATETIME_TO_CALC, 20)

    assert len(result) == 4
