""" HFI admin logic """

from collections import defaultdict
from itertools import groupby
from operator import attrgetter
from typing import Dict, List, Set, Tuple
from datetime import datetime
from app.db.models.hfi_calc import PlanningWeatherStation
from app.schemas.hfi_calc import HFIAdminAddedStation


def remove_stations(stations_to_remove: List[PlanningWeatherStation],
                    all_planning_area_stations: List[PlanningWeatherStation],
                    timestamp: datetime,
                    username: str):
    """
        Marks stations for removal and update station ordering for planning area
    """
    stations_to_remove = []

    planning_areas_with_removals = defaultdict(set)

    # Mark stations for removal and track their orders for updating other stations in planning area
    for station in stations_to_remove:
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
                            all_planning_area_stations: List[PlanningWeatherStation]) -> List[PlanningWeatherStation]:
    """
        Given a dict of [planning_area_id] -> (station_code, order),
        indicating a station removed from a planning area, and list of all stations
        for the keyed planning areas, update the order of the stations.
    """
    stations_with_order_updates = []

    key = attrgetter('planning_area_id')
    all_stations_by_planning_area = dict((k, list(map(lambda x: x, values)))
                                         for k, values in groupby(sorted(all_planning_area_stations, key=key), key))

    for planning_area_id, orders in planning_areas_with_removals.items():
        all_stations = all_stations_by_planning_area.get(planning_area_id, None)
        if all_stations is not None:
            other_stations = list(
                filter(
                    lambda x: (x.station_code, x.order_of_appearance_in_planning_area_list) not in orders,
                    all_stations))
            sorted_other_stations: List[PlanningWeatherStation] = sorted(
                other_stations, key='order_of_appearance_in_planning_area_list')
            for idx, sorted_station in enumerate(sorted_other_stations):
                sorted_station.order_of_appearance_in_planning_area_list = idx + 1
                stations_with_order_updates.append(sorted_station)

    return stations_with_order_updates


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
        order = next_order_by_planning_area[station.planning_area_id]
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
        next_order_by_planning_area[station.planning_area_id] += 1
    return added_stations


def get_next_order_by_planning_area(stations: List[PlanningWeatherStation]) -> Dict[int, int]:
    """ Return next highest ordering for each planning area """
    next_order_by_planning_area = {}

    for planning_area_id, planning_area_stations in groupby(stations, lambda x: x.planning_area_id):
        orders = [station.order_of_appearance_in_planning_area_list for station in list(planning_area_stations)]
        next_order_by_planning_area[planning_area_id] = max(orders) + 1

    return next_order_by_planning_area
