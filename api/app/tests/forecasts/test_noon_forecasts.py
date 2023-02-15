""" BDD tests for API /noon_forecasts.
NOTE: This test currently only handles one station.
"""

import json
import os
import logging
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
import pytest
from pytest_bdd import scenario, given, then, parsers
from starlette.testclient import TestClient
from aiohttp import ClientSession
from app.schemas.stations import StationCodeList
import app.main
from app.tests.common import default_mock_client_get
import app.wildfire_one
import app.db.database
from app.db.models.forecasts import NoonForecast

logger = logging.getLogger(__name__)


def mock_query_noon_forecast_records(session: Session,
                                     station_codes: StationCodeList,
                                     start_date: datetime,
                                     end_date: datetime
                                     ):
    """ Mock some noon forecasts """
    forecasts = []
    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, 'test_noon_forecasts.json')
    with open(filename) as data:
        json_data = json.load(data)
        for forecast in json_data:
            forecast['weather_date'] = datetime.fromisoformat(forecast['weather_date'])
            forecast['created_at'] = datetime.fromisoformat(forecast['created_at'])
            forecasts.append(NoonForecast(**forecast))
    return forecasts


@pytest.mark.usefixtures('mock_env_with_use_wfwx', 'mock_jwt_decode')
@scenario('test_noon_forecasts.feature', 'Get noon_forecasts')
def test_noon_forecasts():
    """ BDD Scenario. """


@given(parsers.parse('I request noon_forecasts for stations: {codes}'),
       target_fixture='response', converters={'codes': json.loads})
def given_request(monkeypatch, codes: List):
    """ Make /api/forecasts/noon/ request using mocked out ClientSession.
    """
    monkeypatch.setattr(ClientSession, 'get', default_mock_client_get)
    monkeypatch.setattr(app.forecasts.noon_forecasts, 'query_noon_forecast_records', mock_query_noon_forecast_records)

    # Create API client and get the reppnse.
    client = TestClient(app.main.app)
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer token'}
    return dict(response=client.post('/api/forecasts/noon/', headers=headers, json={"stations": codes}))


@then(parsers.parse('there are {num_groups} groups of forecasts'), converters={'num_groups': int})
def assert_number_of_forecasts_groups(response, num_groups):
    """ Assert that we receive the expected number of forecast groups """
    assert len(response['response'].json()['noon_forecasts']) == num_groups
