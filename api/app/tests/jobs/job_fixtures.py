""" Fixtures for job tests """
import asyncio
from app.wildfire_one.wfwx_api import WFWXWeatherStation


class MockWFWXHourlyResponse(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def build_mock_wfwx_response(station_id: str) -> MockWFWXHourlyResponse:
    return MockWFWXHourlyResponse(
        stationId=station_id,
        id="ba289776-ef86-04ea-e053-1d09228e8c64",
        station="https://i1bcwsapi.nrs.gov.bc.ca/wfwx-fireweather-api/v1/stations/ba28973a-0a79-04ea-e053-1d09228e8c64",
        createdBy="LEGACY_DATA_LOAD",
        lastModifiedBy="LEGACY_DATA_LOAD",
        lastEntityUpdateTimestamp=1455788589000,
        updateDate="2021-01-31T01:10:34.000+0000",
        archive=False,
        weatherTimestamp=1455771600000,
        temperature=6.7,
        relativeHumidity=100.0,
        windSpeed=1.5,
        recordType=MockWFWXHourlyResponse(
            id="FORECAST",
            displayLabel="Forecast",
            displayOrder=1,
            createdBy="DATA_LOAD",
            lastModifiedBy="DATA_LOAD"
        ),
        windDirection=165.0,
        barometricPressure=None,
        precipitation=0.26,
        observationValidInd=True,
        observationValidComment=None,
        calculate=True,
        businessKey="1455771600000-ba28973a-0a79-04ea-e053-1d09228e8c64",
        fineFuelMoistureCode=5.603,
        initialSpreadIndex=0.0,
        fireWeatherIndex=0.0)


def mock_wfwx_response():
    return [build_mock_wfwx_response('1'), build_mock_wfwx_response('2')]


def mock_wfwx_stations():
    station_1 = WFWXWeatherStation(latitude=1, longitude=1, elevation=1,
                                   wfwx_id='ba28973a-0a79-04ea-e053-1d09228e8c64', code=1,
                                   name='blah', zone_code='T1')
    station_2 = WFWXWeatherStation(latitude=1, longitude=1, elevation=1,
                                   wfwx_id='ba28973a-0a79-04ea-e053-1d09228e8c65', code=2,
                                   name='blah', zone_code='T1')

    future_wfwx_stations = asyncio.Future()
    future_wfwx_stations.set_result([station_1, station_2])
    return future_wfwx_stations
