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
        planning_area_stations = stations_by_planning_area.get(planning_area_id)
        station_info: List[StationInfo] = [StationInfo(
            station_code=station.station_code,
            selected=True,
            fuel_type_id=station.fuel_type_id) for station in planning_area_stations]
        updated_result_request.planning_area_station_info[planning_area_id] = station_info
    return updated_result_request
