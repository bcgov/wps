""" HFI request logic """

from itertools import groupby
import operator
from typing import List
from app.db.models.hfi_calc import PlanningWeatherStation
from app.schemas.hfi_calc import HFIResultRequest, StationInfo


def update_result_request(result_request: HFIResultRequest,
                          latest_stations: List[PlanningWeatherStation]):
    """ Immutable copy of the result request with the latest planning weather stations """
    if len(latest_stations) == 0:
        return result_request

    updated_result_request = result_request.copy(deep=True)
    get_attr = operator.attrgetter('planning_area_id')
    stations_by_planning_area = dict((k, list(map(lambda x: x, values)))
                                     for k, values in groupby(latest_stations, get_attr))
    for planning_area_id in updated_result_request.planning_area_station_info:
        existing_stations = result_request.planning_area_station_info[planning_area_id]
        existing_stations_by_code = {
            station.station_code: station for station in existing_stations
        }

        planning_area_stations = stations_by_planning_area.get(planning_area_id)
        updated_station_info_list: List[StationInfo] = []

        for station in planning_area_stations:
            existing_station = existing_stations_by_code.get(station.station_code)
            station_info: StationInfo = StationInfo(
                station_code=station.station_code,
                selected=existing_station.selected if existing_station is not None else True,
                fuel_type_id=station.fuel_type_id)
            updated_station_info_list.append(station_info)
        updated_result_request.planning_area_station_info[planning_area_id] = updated_station_info_list
    return updated_result_request
