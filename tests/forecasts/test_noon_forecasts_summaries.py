""" Functional testing for /noon_forecasts/summaries/ endpoint.
"""
from datetime import timedelta, datetime
import json
import logging
from typing import List
from pytest_bdd import scenario, given, then, parsers
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
import app.main
from app.db.models.forecasts import NoonForecast
import app.utils.time as time_utils
from app.schemas.stations import StationCodeList


logger = logging.getLogger(__name__)

noon = time_utils.get_utc_now().replace(
    hour=20, minute=0, second=0, microsecond=0)
weather_date = noon - timedelta(days=2)

# they should have the same length
mock_tmps = [20, 21, 22]
mock_rhs = [50, 51, 52]


def mock_query_noon_forecast_records(session: Session,
                                     station_codes: StationCodeList,
                                     start_date: datetime,
                                     end_date: datetime
                                     ):
    """ Mock some noon forecasts """
    forecasts = []
    weather_values = []
    for index, tmp in enumerate(mock_tmps):
        weather_values.append({
            'tmp': tmp,
            'rh': mock_rhs[index]
        })

    for code in [209, 322]:
        for value in weather_values:
            forecasts.append(
                NoonForecast(
                    station_code=code,
                    weather_date=weather_date,
                    created_at=time_utils.get_utc_now(),
                    temperature=value['tmp'],
                    relative_humidity=value['rh']
                )
            )
    return forecasts


@pytest.mark.usefixtures('mock_jwt_decode')
@scenario('test_noon_forecasts_summaries.feature', 'Get noon forecasts summaries(historic)')
def test_noon_forecasts():
    """ BDD Scenario. """


@given(parsers.parse('I request noon forecasts for stations: {codes}'),
       target_fixture='response',
       converters={'codes': json.loads})
def given_request(monkeypatch, codes: List):
    """ Stub forecasts into the database and make a request """

    monkeypatch.setattr(app.forecasts.noon_forecasts_summaries,
                        'query_noon_forecast_records', mock_query_noon_forecast_records)

    client = TestClient(app.main.app)
    endpoint = '/api/forecasts/noon/summaries/'
    return client.post(
        endpoint, headers={'Authorization': 'Bearer token'}, json={'stations': codes})


@then(parsers.parse('the status code of the response is {status}'), converters={'status': int})
def assert_status_code(response, status: int):
    """ Check if we receive the expected status code """
    assert response.status_code == status


@then(parsers.parse('the response should have {num_summaries} summaries of forecasts'),
      converters={'num_summaries': int})
def assert_number_of_summaries(response, num_summaries: int):
    """ Check if we receive the expected number of summaries"""
    assert len(response.json()['summaries']) == num_summaries


@then(parsers.parse('and contain calculated percentiles for available stations {codes}'),
      converters={'codes': json.loads})
def assert_response(response, codes: List):
    """ Check if we calculate correct percentiles based on its noon forecasts """
    result = response.json()
    tmp_min = min(mock_tmps)
    tmp_max = max(mock_tmps)
    rh_min = min(mock_rhs)
    rh_max = max(mock_rhs)

    if len(result['summaries']) == 0:
        assert result['summaries'] == []

    if len(result['summaries']) == 1:
        summary = result['summaries'][0]
        assert summary['station']['code'] == codes[0]
        assert summary['values'] == [{'datetime': weather_date.isoformat(), 'tmp_min': tmp_min,
                                      'tmp_max': tmp_max, 'rh_min': rh_min, 'rh_max': rh_max}]
