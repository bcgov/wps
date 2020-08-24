""" Functional testing for /noon_forecasts/summaries/ endpoint.
"""

from datetime import datetime, timedelta
import logging
import json
from pytest_bdd import scenario, given, then, when
from numpy import percentile
from fastapi.testclient import TestClient
import pytest
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from alchemy_mock.compat import mock
import app.main
from app.db.models import NoonForecasts

LOGGER = logging.getLogger(__name__)

noon = datetime.now().replace(hour=20, minute=0, second=0, microsecond=0)
weather_date = noon - timedelta(days=2)

# they should have the same length
mock_tmps = [20, 21, 22]
mock_rhs = [50, 51, 52]


def get_session_with_data():
    session = UnifiedAlchemyMagicMock()
    station_codes = [209, 322]
    weather_values = []
    for index, tmp in enumerate(mock_tmps):
        weather_values.append({
            'tmp': tmp,
            'rh': mock_rhs[index]
        })

    for code in station_codes:
        for value in weather_values:
            session.add(
                NoonForecasts(
                    station_code=code,
                    weather_date=weather_date,
                    created_at=datetime.now(),
                    temperature=value['tmp'],
                    relative_humidity=value['rh']
                )
            )
    return session


@scenario('test_noon_forecasts_summaries.feature', 'Get noon forecasts summaries(historic)',
          example_converters=dict(codes=str, status=int, num_summaries=int))
def test_noon_forecasts():
    """ BDD Scenario. """


@given('I request noon forecasts for stations: <codes>')
def response(monkeypatch, mock_jwt_decode, codes):
    """ Stub forecasts into the database and make a request """
    stations = eval(codes)

    def mock_get_session(*args):
        return get_session_with_data()
    monkeypatch.setattr(app.db.database, 'get_session', mock_get_session)

    client = TestClient(app.main.app)
    endpoint = '/noon_forecasts/summaries/'
    response = client.post(
        endpoint, headers={'Authorization': 'Bearer token'}, json={'stations': stations})

    return response


@then('the status code of the response is <status>')
def assert_status_code(response, status):
    """ Check if we receive the expected status code """
    assert response.status_code == status


@then('the response should have <num_summaries> summaries of forecasts')
def assert_number_of_summaries(response, num_summaries):
    """ Check if we receive the expected number of summaries"""
    assert len(response.json()['summaries']) == num_summaries


@then('and contain calculated percentiles for available stations <codes>')
def assert_response(response, codes):
    """ Check if we receive correct percentiles of noon forecasts """
    stations = eval(codes)
    result = response.json()
    tmp_5th = percentile(mock_tmps, 5)
    tmp_median = percentile(mock_tmps, 50)
    tmp_90th = percentile(mock_tmps, 90)
    rh_5th = percentile(mock_rhs, 5)
    rh_median = percentile(mock_rhs, 50)
    rh_90th = percentile(mock_rhs, 90)

    if len(result['summaries']) == 0:
        assert result['summaries'] == []

    if len(result['summaries']) == 1:
        summary = result['summaries'][0]
        assert summary['station']['code'] == stations[0]
        assert summary['values'] == [{'datetime': weather_date.isoformat(), 'tmp_5th': tmp_5th,
                                      'tmp_median': tmp_median, 'tmp_90th': tmp_90th, 'rh_5th': rh_5th, 'rh_median': rh_median, 'rh_90th': rh_90th}]
