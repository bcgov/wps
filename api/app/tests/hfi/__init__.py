from app.schemas.shared import FuelType
from app.db.models.hfi_calc import PlanningWeatherStation
import app.hfi.hfi


def mock_station_crud(monkeypatch):
    code1 = 230
    code2 = 239
    all_station_codes = [{'station_code': code1}, {'station_code': code2}]

    def mock_get_all_stations(__):
        """ Returns mocked WFWXWeatherStations codes. """
        return all_station_codes

    def mock_get_fire_centre_stations(_, fire_centre_id: int):
        """ Returns mocked WFWXWeatherStation with fuel types. """
        result = []
        for station_code in [230, 239]:
            planning_station = PlanningWeatherStation(station_code=station_code, planning_area_id=1)
            fuel_type = FuelType(abbrev='C3', fuel_type_code='C3', description='C3',
                                 percentage_conifer=100, percentage_dead_fir=0)
            result.append((planning_station, fuel_type))
        return result

    monkeypatch.setattr(app.utils.hfi_calculator, 'get_all_stations', mock_get_all_stations)
    monkeypatch.setattr(app.routers.hfi_calc, 'get_fire_centre_stations', mock_get_fire_centre_stations)
