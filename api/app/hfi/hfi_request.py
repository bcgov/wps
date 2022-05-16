""" HFI request logic """

from itertools import groupby
import operator
from typing import List
from app.db.models.hfi_calc import PlanningWeatherStation
from app.schemas.hfi_calc import HFIResultRequest, StationInfo


def update_result_request(result_request: HFIResultRequest,
                          currently_persisted_stations: List[PlanningWeatherStation]):
    """ Returns copy of the result request with the latest planning weather stations """
    if len(currently_persisted_stations) == 0:
        return result_request

    updated_result_request = result_request.copy(deep=True)
    key = operator.attrgetter('planning_area_id')
    stations_by_planning_area = dict((k, list(map(lambda x: x, values)))
                                     for k, values in groupby(sorted(currently_persisted_stations, key=key), key))
    for planning_area_id in updated_result_request.planning_area_station_info:
        request_stations = result_request.planning_area_station_info[planning_area_id]
        request_stations_by_code = {
            station.station_code: station for station in request_stations
        }

        planning_area_stations = stations_by_planning_area.get(planning_area_id)
        updated_station_info_list: List[StationInfo] = []

        for station in planning_area_stations:
            request_station = request_stations_by_code.get(station.station_code)
            station_info: StationInfo = StationInfo(
                station_code=station.station_code,
                selected=request_station.selected if request_station is not None else True,
                fuel_type_id=request_station.fuel_type_id if request_station is not None else station.fuel_type_id)  # pylint: disable=line-too-long

            updated_station_info_list.append(station_info)
        updated_result_request.planning_area_station_info[planning_area_id] = updated_station_info_list
    return updated_result_request
