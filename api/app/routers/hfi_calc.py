""" Routers for HFI Calculator """
import logging
from typing import List
from fastapi import APIRouter, Response, Depends
import app
from app import wildfire_one
from app.auth import authentication_required, audit
from app.schemas.hfi_calc import HFIWeatherStationsResponse, WeatherStationProperties,\
    FuelType, FireCentre, PlanningArea, WeatherStation
from app.db.crud.hfi_calc import get_fire_weather_stations
from pydantic import ValidationError


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hfi-calc",
)


@router.get('/fire-centres', response_model=HFIWeatherStationsResponse)
# pylint: disable=too-many-locals
async def get_fire_centres(response: Response):
    """ Returns list of fire centres and planning area for each fire centre,
    and weather stations within each planning area. Also returns the assigned fuel type
    for each weather station. """
    try:
        logger.info('/hfi-calc/fire-centres')
        response.headers["Cache-Control"] = "max-age=0"  # don't let the browser cache this

        with app.db.database.get_read_session_scope() as session:
            # Fetch all fire weather stations from the database.
            station_query = get_fire_weather_stations(session)
            # Prepare empty data structures to be used in HFIWeatherStationsResponse
            fire_centres_list = []
            planning_areas_by_fire_center = {}
            partial_stations_by_planning_area = {}
            station_info_dict = {}
            station_codes = []
            # Iterate through all the database records, collecting all the data we need.
            for (station_record, fuel_type_record, planning_area_record, fire_centre_record) in station_query:
                fire_centre = FireCentre(name=fire_centre_record.name)
                planning_area = PlanningArea(name=planning_area_record.name, fire_centre=fire_centre)
                station_info = {
                    'code': station_record.station_code,
                    'fuel_type': FuelType(
                        abbrev=fuel_type_record.abbrev,
                        description=fuel_type_record.description),
                    'planning_area': planning_area
                }
                # Bookkeeping
                fire_centres_list.append(fire_centre)
                add_planning_center_to_fire_center(planning_areas_by_fire_center, planning_area)
                add_partial_station_to_planning_area(partial_stations_by_planning_area, station_info)
                add_partial_station_info(station_info_dict,
                                         station_record.station_code, station_info)
                station_codes.append(station_record.station_code)

            # We're still missing some data that we need from wfwx, so give it the list of stations
            wfwx_stations_data = await wildfire_one.get_stations_by_codes(station_codes)

            full_stations_by_planning_area = {}
            # Iterate through all the stations from wildfire one.
            for wfwx_station in wfwx_stations_data:
                # Combine everything.
                weather_station = build_full_station(station_info_dict,
                                                     wfwx_station.name,
                                                     wfwx_station.elevation,
                                                     wfwx_station.code,
                                                     wfwx_station.wfwx_station_uuid)

                add_station_to_planning_area(full_stations_by_planning_area, weather_station)

            try:
                return HFIWeatherStationsResponse(fire_centres=fire_centres_list,
                                                  planning_areas_by_fire_center=planning_areas_by_fire_center,
                                                  stations_by_planning_area=full_stations_by_planning_area)
            except ValidationError as v_e:
                print(v_e)

    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise


def build_full_station(planning_area_to_stations: dict,
                       wfwx_station_name: str,
                       wfwx_elevation: int,
                       wfwx_station_code: int,
                       wfwx_station_uuid: str) -> WeatherStation:
    """ Builds out full station from existing partial data and retrieved WFWX data"""
    partial_station_info = planning_area_to_stations[wfwx_station_code]
    station_properties = WeatherStationProperties(
        name=wfwx_station_name,
        fuel_type=partial_station_info['fuel_type'],
        elevation=wfwx_elevation,
        wfwx_station_uuid=wfwx_station_uuid)

    weather_station = WeatherStation(code=wfwx_station_code,
                                     station_props=station_properties,
                                     planning_area=partial_station_info['planning_area'])
    return weather_station


def add_partial_station_info(station_info_dict: dict, station_code: int, station_info):
    """ Add planning centre info to station code dict.
        Assumes 1:1 planning centre to station mapping.
        Mutates the referenced dict through destructive writes."""
    station_info_dict[station_code] = station_info


def add_partial_station_to_planning_area(planning_area_to_stations: dict, station_info):
    """ Add partial station info to planning area dict.
        Mutates the referenced dict through destructive writes. """
    stations = planning_area_to_stations.get(station_info['planning_area'].name)
    if stations is not None:
        stations.append(station_info)
        planning_area_to_stations[station_info['planning_area'].name] = stations
    else:
        planning_area_to_stations[station_info['planning_area'].name] = [station_info]


def add_station_to_planning_area(planning_area_to_stations: dict, station_info):
    """ Add partial station info to planning area dict.
        Mutates the referenced dict through destructive writes. """
    stations = planning_area_to_stations.get(station_info.planning_area.name)
    if stations is not None:
        stations.append(station_info)
        planning_area_to_stations[station_info.planning_area.name] = stations
    else:
        planning_area_to_stations[station_info.planning_area.name] = [station_info]


def add_planning_center_to_fire_center(fire_center_to_planning_centres: dict, planning_area: PlanningArea):
    """ Add planning area to existing fire center 2 planning area dict, or instantiate a list.
        Mutates the referenced dict. 
    """
    existing_planning_areas = fire_center_to_planning_centres.get(planning_area.fire_centre.name)
    if existing_planning_areas is not None:
        existing_planning_areas.append(planning_area)
        fire_center_to_planning_centres[planning_area.fire_centre.name] = existing_planning_areas
    else:
        fire_center_to_planning_centres[planning_area.fire_centre.name] = [planning_area]


def get_wfwx_station(wfwx_stations_data: List[WeatherStation], station_code: int):
    """ Helper function to find station corresponding to station_code from the list of
    weather stations returned from WFWX. """
    for station in wfwx_stations_data:
        if station.code == station_code:
            return station
    return None
