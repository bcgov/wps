import json
from typing import List
from pytest_bdd import then
from app.schemas.shared import FuelType
from app.db.models.hfi_calc import PlanningWeatherStation, PlanningArea
import app.hfi.hfi


def mock_planning_area_crud(monkeypatch):

    def mock_get_planning_areas(session, fire_centre_id):
        """ Returns mocked PlanningAreas. """
        return [PlanningArea(id=1, fire_centre_id=1, name='Area 1', order_of_appearance_in_list=1),
                PlanningArea(id=2, fire_centre_id=1, name='Area 2', order_of_appearance_in_list=2)]

    def mock_get_fire_centre_stations(session, fire_centre_id):
        """ Returns mocked stations per PlanningAreas """
        return [PlanningWeatherStation(id=1, planning_area_id=1, station_code=230),
                PlanningWeatherStation(id=2, planning_area_id=2, station_code=239)]

    monkeypatch.setattr(app.hfi.hfi, 'get_planning_areas', mock_get_planning_areas)
    monkeypatch.setattr(app.hfi.hfi, 'get_fire_centre_stations',
                        mock_get_fire_centre_stations)


def mock_station_crud(monkeypatch):
    code1 = 230
    code2 = 239
    all_station_codes = [{'station_code': code1}, {'station_code': code2}]

    def mock_get_all_stations(__):
        """ Returns mocked WFWXWeatherStations codes. """
        return all_station_codes

    def mock_get_station_with_fuel_types(_, station_codes: List[int]):
        """ Returns mocked WFWXWeatherStation with fuel types. """
        result = []
        for station_code in station_codes:
            planning_station = PlanningWeatherStation(station_code=station_code)
            fuel_type = FuelType(abbrev='C3', fuel_type_code='C3', description='C3', percentage_conifer=100, percentage_dead_fir=0)
            result.append((planning_station, fuel_type))
        return result

    monkeypatch.setattr(app.utils.hfi_calculator, 'get_all_stations', mock_get_all_stations)
    monkeypatch.setattr(app.wildfire_one.wfwx_api, 'get_stations_with_fuel_types',
                        mock_get_station_with_fuel_types)
