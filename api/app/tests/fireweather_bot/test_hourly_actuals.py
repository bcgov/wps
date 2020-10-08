""" Unit testing for hourly actuals bot (Marvin) """
import logging
import pytest
from pytest_mock import MockerFixture
from app.fireweather_bot import hourly_actuals


logger = logging.getLogger(__name__)


def test_hourly_actuals_bot(mocker: MockerFixture, mock_requests_session):  # pylint: disable=unused-argument
    """ Very simple test that checks that:
    - the bot exits with a success code
    - the expected number of records are saved.
    """
    save_hourly_actuals_spy = mocker.spy(hourly_actuals, 'save_hourly_actual')
    with pytest.raises(SystemExit) as excinfo:
        hourly_actuals.main()
    # Assert that we exited without errors.
    assert excinfo.value.code == 0
    # Assert that we got called the expected number of times.
    # There are 535 records in the csv fixture, one of which doesn't have a valid station name,
    # so we expect 534 records.
    assert save_hourly_actuals_spy.call_count == 534
