from typing import Final
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.auto_spatial_advisory.sfms import get_prefix
from app.routers.sfms import get_target_filename
from app import config

from app.main import app


URL = '/api/sfms/upload'

yesterday: Final = 'hfi20220822.tif'
today: Final = 'hfi20220823.tif'
tomorrow: Final = 'hfi20220824.tif'


def get_pdt_8am():
    """ Morning SFMS runs some time in the morning
    Just to make everything extra confusing, use a PDT (-7) timestamp.
    """
    return datetime.fromisoformat('2022-08-23T08:17:50.947039-07:00')


def get_pdt_noon():
    """ NOT solar noon. Solar noon is at 12h00 PST / 13h00 PDT.
    Just to make everything extra confusing, use a PDT (-7) timestamp.
    """
    return datetime.fromisoformat('2022-08-23T12:17:50.947039-07:00')


def get_pdt_17():
    """ 17h00 PDT is 12h00 UTC the NEXT day.
    """
    return datetime.fromisoformat('2022-08-23T17:17:50.947039-07:00')


def get_pdt_1pm():
    """ Solar noon is at 12h00 PST / 13h00 PDT.
    Just to make everything extra confusing, use a PDT (-7) timestamp.
    """
    return datetime.fromisoformat('2022-08-23T13:17:50.947039-07:00')


def get_time_in_utc(date: datetime):
    """ Given some datetime, return the datetime in UTC """
    return date.astimezone(timezone.utc)


@patch('app.auto_spatial_advisory.sfms.get_vancouver_now', return_value=get_pdt_8am())
def test_is_actual_before_noon(_):
    """ Test is_actual function """
    # If it's for yesterday, we assume it's an actual.
    assert get_prefix(yesterday) == 'actual'
    # If it's for today, we assume it's a forecast (actual only comes after SOLAR noon).
    assert get_prefix(today) == 'forecast'
    # If it's for tomorrow, we assume it's a forecast.
    assert get_prefix(tomorrow) == 'forecast'


def test_tiff_does_not_break():
    """ If someone decided to add an extra f on tiff, it should keep working!"""
    # Slightly silly way to check that no exception is thrown:
    assert get_prefix('hfi20220824.tiff') in ('actual', 'forecast')


@patch('app.auto_spatial_advisory.sfms.get_vancouver_now', return_value=get_pdt_noon())
def test_is_actual_after_noon(_):
    """ Test is_actual function """
    # If it's for yesterday, we assume it's an actual.
    assert get_prefix(yesterday) == 'actual'
    # If it's for today, we assume it's an forecast, since it's BEFORE solar noon.
    assert get_prefix(today) == 'forecast'
    # If it's for tomorrow, we assume it's a forecast.
    assert get_prefix(tomorrow) == 'forecast'


@patch('app.auto_spatial_advisory.sfms.get_vancouver_now', return_value=get_pdt_1pm())
def test_is_actual_after_solar_noon(_):
    """ Test is_actual function """
    # If it's for yesterday, we assume it's an actual.
    assert get_prefix(yesterday) == 'actual'
    # If it's for today, we assume it's an actual, since it's after SOLAR noon.
    assert get_prefix(today) == 'actual'
    # If it's for tomorrow, we assume it's a forecast.
    assert get_prefix(tomorrow) == 'forecast'


@patch('app.auto_spatial_advisory.sfms.get_vancouver_now', return_value=get_pdt_1pm())
def test_get_target_filename(_):
    """ Test get_target_filename function """
    # If it's for yesterday, we assume it's an actual.
    assert get_target_filename(yesterday) == 'sfms/uploads/actual/2022-08-23/hfi20220822.tif'
    # If it's for today, after solar noon, we assume it's an actual.
    assert get_target_filename(today) == 'sfms/uploads/actual/2022-08-23/hfi20220823.tif'
    # If it's for tomorrow, we assume it's a forecast.
    assert get_target_filename(tomorrow) == 'sfms/uploads/forecast/2022-08-23/hfi20220824.tif'


@patch('app.auto_spatial_advisory.sfms.get_vancouver_now', return_value=get_pdt_17())
def test_get_target_filename_day_difference(_):
    """ Test get_target_filename function, when UTC day is different from PST day """
    # If the issue date is today in Canada, we want the filename to reflect that.
    # We want to make sure that the fact that 5pm local on the 23rd, doesn't get construed as
    # the 24th. Yes. It's already the 24th in UTC - but we're only concerned with respect to
    # PDT.
    # Now sure. We could store the entire timestamp in the filename, and then we know exactly
    # what we're dealing with - but that seems excessive.
    assert get_target_filename(yesterday) == 'sfms/uploads/actual/2022-08-23/hfi20220822.tif'
    # It's 5 pm, so anything for today, is an actual.
    assert get_target_filename(today) == 'sfms/uploads/actual/2022-08-23/hfi20220823.tif'
    # It's 5 pm, so anything for tomorrow, is a forecast.
    assert get_target_filename(tomorrow) == 'sfms/uploads/forecast/2022-08-23/hfi20220824.tif'


@patch('app.routers.sfms.get_client')
@patch('app.routers.sfms.publish')
def test_endpoint(mock_publish: AsyncMock, mock_get_client: AsyncMock):
    """ Test that if all is well - the endpoint returns 200, the file is uploaded to S3, and
    a message is published to the queue. """
    mock_s3_client = AsyncMock()

    @asynccontextmanager
    async def _mock_get_client_for_router():
        yield mock_s3_client, 'some_bucket'

    mock_get_client.return_value = _mock_get_client_for_router()
    client = TestClient(app)
    response = client.post(URL,
                           files={'file': ('hfi20220904.tiff', b'')},
                           headers={
                               'Secret': config.get('SFMS_SECRET'),
                               'Last-modified': datetime.now().isoformat(),
                               'Create-time': datetime.now().isoformat()})
    # We should get a 200 response if the file is uploaded successfully.
    assert response.status_code == 200
    # We should have called put_object once.
    assert mock_s3_client.put_object.called
    # We should have called publish once.
    assert mock_publish.called


@patch('app.routers.sfms.get_client')
@patch('app.routers.sfms.publish')
def test_endpoint_no_secret(mock_publish: AsyncMock, mock_get_client: AsyncMock):
    """ Test that if no secret is provided, we get a 401, no file is uploaded, and no message is
    placed on the queue. """
    mock_s3_client = AsyncMock()

    @asynccontextmanager
    async def _mock_get_client_for_router():
        yield mock_s3_client, 'some_bucket'

    mock_get_client.return_value = _mock_get_client_for_router()
    client = TestClient(app)
    response = client.post(URL,
                           files={'file': ('test_sfms_upload.py', b'')})
    # If you didn't give a secret = we should get a 401.
    assert response.status_code == 401
    # We should not have called put_object.
    assert mock_s3_client.put_object.called is False
    # Publish should not have been called.
    assert mock_publish.called is False


@patch('app.routers.sfms.get_client')
@patch('app.routers.sfms.publish')
def test_endpoint_wrong_secret(mock_publish: AsyncMock, mock_get_client: AsyncMock):
    """ Test that if the wrong secret is provided, we get a 401, no file is uploaded, and no
    message is placed on the queue. """
    mock_s3_client = AsyncMock()

    @asynccontextmanager
    async def _mock_get_client_for_router():
        yield mock_s3_client, 'some_bucket'

    mock_get_client.return_value = _mock_get_client_for_router()

    client = TestClient(app)
    response = client.post(URL,
                           files={'file': ('test_sfms_upload.py', b'')},
                           headers={'Secret': 'fudge'})
    # If your secret is wrong = we should get a 401.
    assert response.status_code == 401
    # We should not have called put_object.
    assert mock_s3_client.put_object.called is False
    # Publish should not have been called.
    assert mock_publish.called is False
