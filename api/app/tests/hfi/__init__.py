from app.db.models.hfi_calc import PlanningWeatherStation, FireStartRange, FireStartLookup, FuelType
import app.hfi.hfi_calc


def mock_station_crud(monkeypatch):
    code1 = 230
    code2 = 239
    all_station_codes = [{'station_code': code1}, {'station_code': code2}]

    def mock_get_all_stations(__):
        """ Returns mocked WFWXWeatherStations codes. """
        return all_station_codes

    def mock_get_fire_centre_stations(_, fire_centre_id: int):
        """ Returns mocked WFWXWeatherStation with fuel types. """
        def get_fuel_type_code_by_station_code(code: int):
            if code == 230:
                return 'C3'
            return 'C7B'
        result = []
        for station_code, planning_area_id in [(230, 1), (239, 1), (230, 2)]:
            planning_station = PlanningWeatherStation(
                station_code=station_code, planning_area_id=planning_area_id)
            fuel_type_code = get_fuel_type_code_by_station_code(station_code)
            fuel_type = FuelType(id=1, abbrev=fuel_type_code, fuel_type_code=fuel_type_code,
                                 description=fuel_type_code,
                                 percentage_conifer=100, percentage_dead_fir=0)
            result.append((planning_station, fuel_type))
        return result

    def mock_get_fire_centre_fire_start_ranges(_, __: int):
        """ Returns mocked FireStartRange """
        data = ((1, '0-1'), (2, '1-2'), (3, '2-3'), (4, '3-6'), (5, '6+'))
        return [FireStartRange(id=id, label=range) for id, range in data]

    def mock_get_fire_start_lookup(_):
        """ Returns mocked FireStartLookup """
        data = ((1, 1, 1, 1),
                (2, 1, 2, 1),
                (3, 1, 3, 2),
                (4, 1, 4, 3),
                (5, 1, 5, 4),
                (6, 2, 1, 1),
                (7, 2, 2, 1),
                (8, 2, 3, 2),
                (9, 2, 4, 4),
                (10, 2, 5, 5),
                (11, 3, 1, 2),
                (12, 3, 2, 3),
                (13, 3, 3, 4),
                (14, 3, 4, 5),
                (15, 3, 5, 6),
                (16, 4, 1, 3),
                (17, 4, 2, 4),
                (18, 4, 3, 4),
                (19, 4, 4, 5),
                (20, 4, 5, 6),
                (21, 5, 1, 4),
                (22, 5, 2, 5),
                (23, 5, 3, 6),
                (24, 5, 4, 6),
                (25, 5, 5, 6))
        return [FireStartLookup(id=id,
                                fire_start_range_id=fire_start_range_id,
                                mean_intensity_group=mean_intensity_group,
                                prep_level=prep_level) for
                id, fire_start_range_id, mean_intensity_group, prep_level in data]

    monkeypatch.setattr(app.utils.hfi_calculator, 'get_all_stations', mock_get_all_stations)
    monkeypatch.setattr(app.hfi.hfi_calc, 'get_fire_centre_stations', mock_get_fire_centre_stations)
    monkeypatch.setattr(app.routers.hfi_calc, 'get_fire_centre_stations', mock_get_fire_centre_stations)
    monkeypatch.setattr(app.hfi.hfi_calc, 'get_fire_centre_fire_start_ranges',
                        mock_get_fire_centre_fire_start_ranges)
    monkeypatch.setattr(app.hfi.hfi_calc, 'get_fire_start_lookup', mock_get_fire_start_lookup)
