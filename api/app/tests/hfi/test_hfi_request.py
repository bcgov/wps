""" Unit testing for hfi logic """
import pytest
import os
import json
from app.db.models.hfi_calc import PlanningWeatherStation
from app.hfi.hfi_request import update_result_request
from app.schemas.hfi_calc import HFIResultRequest


@pytest.fixture
def result_request() -> HFIResultRequest:
    dirname = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dirname, 'result_request.json')
    with open(filename, 'r') as f:
        stored_request = json.loads(f.read())
        return HFIResultRequest.parse_obj(stored_request)


def test_no_new_stations(result_request):
    """ No new stations means no update """
    result = update_result_request(result_request, [])
    assert len(result.planning_area_station_info[1]) == 1
    assert result.planning_area_station_info[1][0].station_code == 230
    assert result.planning_area_station_info[1][0].selected is False
    assert result.planning_area_station_info[1][0].fuel_type_id == 1


def test_new_stations(result_request):
    """ New stations should overwrite existing """
    latest_stations = [PlanningWeatherStation(station_code=1, fuel_type_id=1, planning_area_id=1),
                       PlanningWeatherStation(station_code=2, fuel_type_id=1, planning_area_id=1)]
    result = update_result_request(result_request, latest_stations)
    assert len(result.planning_area_station_info[1]) == 2
    assert result.planning_area_station_info[1][0].station_code == 1
    assert result.planning_area_station_info[1][1].station_code == 2


def test_existing_station_state(result_request):
    """ Existing station state should remain """
    latest_stations = [PlanningWeatherStation(station_code=230, fuel_type_id=2, planning_area_id=1)]
    result = update_result_request(result_request, latest_stations)
    assert len(result.planning_area_station_info[1]) == 1
    assert result.planning_area_station_info[1][0].station_code == 230
    assert result.planning_area_station_info[1][0].selected is False
    assert result.planning_area_station_info[1][0].fuel_type_id == 1


def test_existing_stations(result_request):
    """ Existing stations should be included when new station exists """
    latest_stations = [
        PlanningWeatherStation(station_code=230, fuel_type_id=1, planning_area_id=1),
        PlanningWeatherStation(station_code=1, fuel_type_id=1, planning_area_id=1)]
    result = update_result_request(result_request, latest_stations)
    assert len(result.planning_area_station_info[1]) == 2
    assert result.planning_area_station_info[1][0].station_code == 230
    assert result.planning_area_station_info[1][1].station_code == 1
