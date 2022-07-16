""" HFI admin logic """

from collections import defaultdict
from itertools import groupby
from operator import attrgetter
from typing import Dict, List, Set, Tuple
from datetime import datetime
from app.db.models.hfi_calc import PlanningWeatherStation
from app.schemas.hfi_calc import HFIAdminAddedStation


def update_stations(stations_to_remove: List[PlanningWeatherStation],
                    all_planning_area_stations: List[PlanningWeatherStation],
                    to_add: List[HFIAdminAddedStation],
                    timestamp: datetime,
                    username: str) -> List[PlanningWeatherStation]:
    """
        Orchestrates removal and addition of stations
    """
    stations_marked_for_removal, stations_with_order_updates = remove_stations(
        stations_to_remove, all_planning_area_stations, timestamp, username)

    next_order_by_planning_area = get_next_order_by_planning_area(
        stations_with_order_updates, all_planning_area_stations)

    stations_to_add = add_stations(to_add, next_order_by_planning_area, timestamp, username)

    return stations_marked_for_removal + stations_with_order_updates + stations_to_add


def remove_stations(remove_station_list: List[PlanningWeatherStation],
                    all_planning_area_stations: List[PlanningWeatherStation],
                    timestamp: datetime,
                    username: str):
    """
        Marks stations for removal and update station ordering for planning area
    """
    stations_to_remove = []

    planning_areas_with_removals = defaultdict(set)

    # Mark stations for removal and track their orders for updating other stations in planning area
    for station in remove_station_list:
        station.update_timestamp = timestamp
        station.update_user = username
        station.is_deleted = True
        planning_areas_with_removals[station.planning_area_id].add(
            station.order_of_appearance_in_planning_area_list)
        station.order_of_appearance_in_planning_area_list = None
        stations_to_remove.append(station)

    # Handle order updates
    stations_with_order_updates = update_station_ordering(planning_areas_with_removals, all_planning_area_stations)

    return stations_to_remove, stations_with_order_updates


def update_station_ordering(planning_areas_with_removals: Dict[int, Set[Tuple[int, int]]],
                            all_planning_area_stations: List[PlanningWeatherStation]):
    """
        Given a dict of [planning_area_id] -> (station_code, order),
        indicating a station removed from a planning area, and list of all stations
        for the keyed planning areas, update the order of the stations.
    """
    stations_with_order_updates = []

    key = attrgetter('planning_area_id')
    all_stations_by_planning_area = dict((k, list(map(lambda x: x, values)))
                                         for k, values in groupby(sorted(all_planning_area_stations, key=key), key))

    for planning_area_id, removed_stations in planning_areas_with_removals.items():
        all_stations = all_stations_by_planning_area.get(planning_area_id, None)
        if all_stations is not None:
            other_stations = get_stations_with_order(get_other_stations(removed_stations, all_stations))
            sorted_other_stations: List[PlanningWeatherStation] = sorted(
                other_stations, key=attrgetter('order_of_appearance_in_planning_area_list'))
            for idx, sorted_station in enumerate(sorted_other_stations):
                sorted_station.order_of_appearance_in_planning_area_list = idx + 1
                stations_with_order_updates.append(sorted_station)

    return stations_with_order_updates


def get_other_stations(stations_removed: Set[Tuple[int, int]], all_stations: List[PlanningWeatherStation]):
    """
        Given a set of removed stations, {(station_code, order), ...},
        and list of all stations, return a list of stations not in set
    """
    return list(filter(
        lambda x: (x.station_code, x.order_of_appearance_in_planning_area_list) not in stations_removed,
        all_stations))


def get_stations_with_order(stations: List[PlanningWeatherStation]):
    """
        Returns list of stations that have an order
    """
    return list(filter(lambda x: x.order_of_appearance_in_planning_area_list is not None, stations))


def add_stations(stations_to_add: List[HFIAdminAddedStation],
                 next_order_by_planning_area: Dict[int, int],
                 timestamp: datetime,
                 username: str) -> List[PlanningWeatherStation]:
    """
        Given a list of station data to add, and the next order for a station for each planning area,
        return the station data and order as planning weather stations.
    """
    added_stations: List[PlanningWeatherStation] = []
    for station_to_add in stations_to_add:
        order = next_order_by_planning_area.get(station_to_add.planning_area_id, 1)
        station = PlanningWeatherStation(
            planning_area_id=station_to_add.planning_area_id,
            station_code=station_to_add.station_code,
            order_of_appearance_in_planning_area_list=order,
            fuel_type_id=station_to_add.fuel_type_id,
            create_user=username,
            update_user=username,
            create_timestamp=timestamp,
            update_timestamp=timestamp,
            is_deleted=False
        )
        added_stations.append(station)
        next_order_by_planning_area[station.planning_area_id] = order + 1
    return added_stations


def get_next_order_by_planning_area(station_with_order_updates: List[PlanningWeatherStation],
                                    all_planning_area_stations: List[PlanningWeatherStation]) -> Dict[int, int]:
    """ Return next highest ordering for each planning area """
    next_order_by_planning_area = {}

    key = attrgetter('planning_area_id')
    updated_stations_by_planning_area = dict((k, list(map(lambda x: x, values)))
                                             for k, values in groupby(sorted(station_with_order_updates, key=key), key))
    all_stations_by_planning_area = dict((k, list(map(lambda x: x, values)))
                                         for k, values in groupby(sorted(all_planning_area_stations, key=key), key))

    for planning_area_id, planning_area_stations in all_stations_by_planning_area.items():
        updated_stations = updated_stations_by_planning_area.get(planning_area_id, [])
        next_order_by_planning_area[planning_area_id] = get_next_order(updated_stations, planning_area_stations)

    return next_order_by_planning_area


def get_next_order(updated_stations: List[PlanningWeatherStation], other_stations: List[PlanningWeatherStation]):
    """
        Returns the next order for a list of planning stations based on updated and existing stations.
        Updated stations will include and removals, so that list may have a smaller max order.
    """
    updated_orders = [station.order_of_appearance_in_planning_area_list for station in updated_stations]

    # An existing could be removed and hence have no order
    existing_orders = [
        station.order_of_appearance_in_planning_area_list for station in other_stations
        if station.order_of_appearance_in_planning_area_list is not None]

    if len(updated_orders) == 0:
        return max(existing_orders) + 1
    if len(existing_orders) == 0:
        return max(updated_orders) + 1

    return min(max(updated_orders) + 1, max(existing_orders) + 1)


def get_unique_planning_area_ids(stations: List[PlanningWeatherStation]):
    return list(set([station.planning_area_id for station in stations]))
