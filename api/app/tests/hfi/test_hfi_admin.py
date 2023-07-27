from datetime import datetime
from app.db.models.hfi_calc import PlanningWeatherStation
from app.hfi.hfi_admin import add_stations, get_next_order, get_next_order_by_planning_area, get_unique_planning_area_ids, remove_stations, update_station_ordering
from app.schemas.hfi_calc import HFIAdminAddedStation

timestamp = datetime.fromisoformat("2019-06-10T18:42:49")


def test_get_unique_planning_areas_dups():
    stations = [PlanningWeatherStation(planning_area_id=1,
                                       station_code=4,
                                       order_of_appearance_in_planning_area_list=1),
                PlanningWeatherStation(planning_area_id=1,
                                       station_code=5,
                                       order_of_appearance_in_planning_area_list=2)]
    res = get_unique_planning_area_ids(stations)
    assert res == [1]


def test_get_unique_planning_areas_uniques():
    stations = [PlanningWeatherStation(planning_area_id=1,
                                       station_code=4,
                                       order_of_appearance_in_planning_area_list=1),
                PlanningWeatherStation(planning_area_id=2,
                                       station_code=5,
                                       order_of_appearance_in_planning_area_list=2)]
    res = get_unique_planning_area_ids(stations)
    assert res == [1, 2]


def test_get_next_order_by_planning_area_no_stations():
    """ No updated stations or existing stations means no ordering"""
    res = get_next_order_by_planning_area([], [])
    assert res == {}


def test_get_next_order_by_planning_area_with_updates():
    """ Updated station list is the current list so its ordering takes precedence over existing stations
        In this case the last existing station was removed so the next added station has order 2
    """
    updated_stations = [PlanningWeatherStation(planning_area_id=1,
                                               station_code=4,
                                               order_of_appearance_in_planning_area_list=1)]
    existing_stations = [PlanningWeatherStation(planning_area_id=1,
                                                station_code=4,
                                                order_of_appearance_in_planning_area_list=1),
                         PlanningWeatherStation(planning_area_id=1,
                                                station_code=5,
                                                order_of_appearance_in_planning_area_list=2)]
    res = get_next_order_by_planning_area(updated_stations, existing_stations)
    assert res == {1: 2}


def test_get_next_order_by_planning_area_no_updates():
    """ No updated stations mean next order is max(existing_orders) + 1"""
    updated_stations = []
    existing_stations = [PlanningWeatherStation(planning_area_id=1,
                                                station_code=4,
                                                order_of_appearance_in_planning_area_list=1),
                         PlanningWeatherStation(planning_area_id=1,
                                                station_code=5,
                                                order_of_appearance_in_planning_area_list=2)]
    res = get_next_order_by_planning_area(updated_stations, existing_stations)
    assert res == {1: 3}


def test_get_next_order_by_planning_area():
    """ Next order is computed based on stations in each planning area """
    planning_area_1 = 1
    pa1_station1 = PlanningWeatherStation(planning_area_id=planning_area_1,
                                          station_code=1,
                                          order_of_appearance_in_planning_area_list=1)
    pa1_station2 = PlanningWeatherStation(planning_area_id=planning_area_1,
                                          station_code=2,
                                          order_of_appearance_in_planning_area_list=2)
    planning_area_2 = 2
    pa2_station1 = PlanningWeatherStation(planning_area_id=planning_area_2,
                                          station_code=3,
                                          order_of_appearance_in_planning_area_list=1)

    res = get_next_order_by_planning_area([], [pa1_station1, pa1_station2, pa2_station1])
    assert res[planning_area_1] == 3  # order 1 and 2 for pa1 are taken
    assert res[planning_area_2] == 2  # order 2 for pa2 taken


def test_add_station():
    """ Adding a station to a planning area with correct order """
    pa_order_dict = {1: 1}
    station_to_add = HFIAdminAddedStation(planning_area_id=1, station_code=1, fuel_type_id=1)
    username = "test_user"
    res = add_stations([station_to_add], pa_order_dict, timestamp, username)
    assert res[0].planning_area_id == station_to_add.planning_area_id
    assert res[0].order_of_appearance_in_planning_area_list == 1


def test_add_stations():
    """ Adding stations to a planning area with correct orders """
    pa_order_dict = {1: 1}
    station_to_add_1 = HFIAdminAddedStation(planning_area_id=1, station_code=1, fuel_type_id=1)
    station_to_add_2 = HFIAdminAddedStation(planning_area_id=1, station_code=2, fuel_type_id=1)
    username = "test_user"
    res = add_stations([station_to_add_1, station_to_add_2], pa_order_dict, timestamp, username)

    assert res[0].planning_area_id == station_to_add_1.planning_area_id
    assert res[0].station_code == station_to_add_1.station_code
    assert res[0].order_of_appearance_in_planning_area_list == 1

    assert res[1].planning_area_id == station_to_add_2.planning_area_id
    assert res[1].station_code == station_to_add_2.station_code
    assert res[1].order_of_appearance_in_planning_area_list == 2


def test_add_stations_different_planning_areas():
    """ Adding stations to a planning area with correct orders """
    pa_order_dict = {1: 2, 2: 3}
    station_to_add_1 = HFIAdminAddedStation(planning_area_id=1, station_code=1, fuel_type_id=1)
    station_to_add_2 = HFIAdminAddedStation(planning_area_id=2, station_code=2, fuel_type_id=1)
    username = "test_user"
    res = add_stations([station_to_add_1, station_to_add_2], pa_order_dict, timestamp, username)

    assert res[0].planning_area_id == station_to_add_1.planning_area_id
    assert res[0].station_code == station_to_add_1.station_code
    assert res[0].order_of_appearance_in_planning_area_list == 2

    assert res[1].planning_area_id == station_to_add_2.planning_area_id
    assert res[1].station_code == station_to_add_2.station_code
    assert res[1].order_of_appearance_in_planning_area_list == 3


def test_update_order_all_stations_removed():
    """ Correct station order for planning area when all stations are removed """

    # [planning_area_id] -> {(station_code, order)...}
    # planning area 1 has stations 1 and 2 removed
    planning_area_removed_stations = {1: {(1, 1), (2, 2)}}
    all_planning_area_stations = [PlanningWeatherStation(planning_area_id=1,
                                                         station_code=1,
                                                         order_of_appearance_in_planning_area_list=1),
                                  PlanningWeatherStation(planning_area_id=1,
                                                         station_code=2,
                                                         order_of_appearance_in_planning_area_list=2)]
    res = update_station_ordering(planning_area_removed_stations, all_planning_area_stations)
    assert len(res) == 0  # no order updates since all stations are removed


def test_update_order_last_station_removed():
    """ Correct station order for planning area when all stations are removed """

    # [planning_area_id] -> {(station_code, order)...}
    # planning area 1 has stations 1 and 2 removed
    planning_area_removed_stations = {1: {(2, 2)}}
    all_planning_area_stations = [PlanningWeatherStation(planning_area_id=1,
                                                         station_code=1,
                                                         order_of_appearance_in_planning_area_list=1),
                                  PlanningWeatherStation(planning_area_id=1,
                                                         station_code=2,
                                                         order_of_appearance_in_planning_area_list=2)]
    res = update_station_ordering(planning_area_removed_stations, all_planning_area_stations)
    assert res[0].planning_area_id == 1
    assert res[0].station_code == 1
    assert res[0].order_of_appearance_in_planning_area_list == 1  # first station still has same order


def test_update_order_first_station_removed():
    """ Correct station order for planning area when all stations are removed """

    # [planning_area_id] -> {(station_code, order)...}
    # planning area 1 has stations 1 and 2 removed
    planning_area_removed_stations = {1: {(1, 1)}}
    all_planning_area_stations = [PlanningWeatherStation(planning_area_id=1,
                                                         station_code=1,
                                                         order_of_appearance_in_planning_area_list=1),
                                  PlanningWeatherStation(planning_area_id=1,
                                                         station_code=2,
                                                         order_of_appearance_in_planning_area_list=2)]
    res = update_station_ordering(planning_area_removed_stations, all_planning_area_stations)
    assert res[0].planning_area_id == 1
    assert res[0].station_code == 2
    assert res[0].order_of_appearance_in_planning_area_list == 1  # remaining station now has order 1


def test_update_order_middle_station_removed():
    """ Correct station order for planning area when all stations are removed """

    # [planning_area_id] -> {(station_code, order)...}
    # planning area 1 has stations 1 and 2 removed
    planning_area_removed_stations = {1: {(2, 2)}}
    all_planning_area_stations = [PlanningWeatherStation(planning_area_id=1,
                                                         station_code=1,
                                                         order_of_appearance_in_planning_area_list=1),
                                  PlanningWeatherStation(planning_area_id=1,
                                                         station_code=2,
                                                         order_of_appearance_in_planning_area_list=2),
                                  PlanningWeatherStation(planning_area_id=1,
                                                         station_code=3,
                                                         order_of_appearance_in_planning_area_list=3)]
    res = update_station_ordering(planning_area_removed_stations, all_planning_area_stations)

    assert len(res) == 2

    assert res[0].planning_area_id == 1
    assert res[0].station_code == 1
    assert res[0].order_of_appearance_in_planning_area_list == 1  # first station still has order 1

    assert res[1].planning_area_id == 1
    assert res[1].station_code == 3
    assert res[1].order_of_appearance_in_planning_area_list == 2  # last station now has order 2


def test_remove_station():
    """ Removing a station marks it as deleted an updates remaining orders """
    removals = [PlanningWeatherStation(planning_area_id=1,
                                       station_code=1,
                                       order_of_appearance_in_planning_area_list=1)]
    all_planning_area_stations = [removals[0],
                                  PlanningWeatherStation(planning_area_id=1,
                                                         station_code=2,
                                                         order_of_appearance_in_planning_area_list=2),
                                  PlanningWeatherStation(planning_area_id=1,
                                                         station_code=3,
                                                         order_of_appearance_in_planning_area_list=3)]
    timestamp = datetime.fromisoformat('2019-06-10T18:42:49')
    username = 'test'
    stations_to_remove, stations_with_order_updates = remove_stations(
        removals, all_planning_area_stations, timestamp, username)

    assert stations_to_remove[0].planning_area_id == removals[0].planning_area_id
    assert stations_to_remove[0].station_code == removals[0].station_code
    assert stations_to_remove[0].order_of_appearance_in_planning_area_list is None

    assert len(stations_with_order_updates) == 2
    assert stations_with_order_updates[0].planning_area_id == all_planning_area_stations[1].planning_area_id
    assert stations_with_order_updates[0].station_code == all_planning_area_stations[1].station_code
    assert stations_with_order_updates[0].order_of_appearance_in_planning_area_list == 1  # 2nd is 1st now

    assert stations_with_order_updates[1].planning_area_id == all_planning_area_stations[2].planning_area_id
    assert stations_with_order_updates[1].station_code == all_planning_area_stations[2].station_code
    assert stations_with_order_updates[1].order_of_appearance_in_planning_area_list == 2  # 3rd is 2nd now


def test_remove_stations():
    """ Removing stations marks them as deleted and updates remaining orders"""
    removals = [PlanningWeatherStation(planning_area_id=1,
                                       station_code=1,
                                       order_of_appearance_in_planning_area_list=1),
                PlanningWeatherStation(planning_area_id=1,
                                       station_code=2,
                                       order_of_appearance_in_planning_area_list=2)]
    all_planning_area_stations = [removals[0],
                                  removals[1],
                                  PlanningWeatherStation(planning_area_id=1,
                                                         station_code=3,
                                                         order_of_appearance_in_planning_area_list=3)]
    timestamp = datetime.fromisoformat('2019-06-10T18:42:49')
    username = 'test'
    stations_to_remove, stations_with_order_updates = remove_stations(
        removals, all_planning_area_stations, timestamp, username)

    assert len(stations_to_remove) == 2
    assert stations_to_remove[0].planning_area_id == removals[0].planning_area_id
    assert stations_to_remove[0].station_code == removals[0].station_code
    assert stations_to_remove[0].order_of_appearance_in_planning_area_list is None

    assert stations_to_remove[1].planning_area_id == removals[1].planning_area_id
    assert stations_to_remove[1].station_code == removals[1].station_code
    assert stations_to_remove[1].order_of_appearance_in_planning_area_list is None

    assert len(stations_with_order_updates) == 1
    assert stations_with_order_updates[0].planning_area_id == all_planning_area_stations[2].planning_area_id
    assert stations_with_order_updates[0].station_code == all_planning_area_stations[2].station_code
    assert stations_with_order_updates[0].order_of_appearance_in_planning_area_list == 1  # last one left


def test_get_next_order_no_updated_or_existing():
    """ If there are no updated or existing stations, the next order should be 1 """
    assert get_next_order([], []) == 1


def test_get_next_order_no_updated():
    """ If there are no updated or existing stations, the next order should be 1 """
    assert get_next_order([], [PlanningWeatherStation(planning_area_id=1,
                                                      station_code=3,
                                                      order_of_appearance_in_planning_area_list=1)]) == 2


def test_get_next_order_no_existing():
    """ If there are no updated or existing stations, the next order should be 1 """
    assert get_next_order([], [PlanningWeatherStation(planning_area_id=1,
                                                      station_code=3,
                                                      order_of_appearance_in_planning_area_list=1)]) == 2
