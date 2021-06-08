""" Routers for HFI Calculator """
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, Response, Depends
from app import wildfire_one
from app.auth import authentication_required, audit
from app.db.models.hfi_calc import FireCentre, FuelType, PlanningArea, PlanningWeatherStation
from app.hfi_calc import fetch_fire_centre_by_id, fetch_fuel_type_by_id, fetch_hfi_station_data, fetch_planning_area_by_id
from app.schemas.hfi_calc import PlanningAreasResponse, WeatherStationProperties, FuelType, FireCentre, PlanningArea, WeatherStation


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hfi-calc",
)


@router.get('/', response_model=PlanningAreasResponse)
async def get_fire_centres(response: Response):
    """ Returns list of fire centres and planning area for each fire centre,
    and weather stations within each planning area. Also returns the assigned fuel type
    for each weather station. """
    try:
        logger.info('/hfi-calc/')
        response.headers["Cache-Control"] = "max-age=0"  # don't let the browser cache this
        station_data = await fetch_hfi_station_data()

        # compile list of station codes from station_data, then send request to WFWX to retrieve
        # station data (station name and elevation)
        station_codes_list = []
        for station in station_data:
            station_codes_list.append(station.station_code)
        wfwx_stations_data = await wildfire_one.get_stations_by_codes(station_codes_list)

        stations_list = []
        for station in station_data:
            fuel = await fetch_fuel_type_by_id(station.fuel_type_id)
            fuel_type = FuelType(abbrev=fuel.abbrev, description=fuel.description)
            wfwx_station = get_wfwx_station(wfwx_stations_data, station.station_code)
            station_properties = WeatherStationProperties(
                name=wfwx_station.name, fuel_type=fuel_type, elevation=wfwx_station.elevation, wfwx_station_uuid=wfwx_station.wfwx_station_uuid)
            zone = await fetch_planning_area_by_id(station.planning_area_id)
            fc = await fetch_fire_centre_by_id(zone.fire_centre_id)
            fire_centre = FireCentre(name=fc.name)
            planning_area = PlanningArea(name=zone.name, fire_centre=fire_centre)
            weather_station = WeatherStation(code=station.station_code,
                                             station_props=station_properties, planning_area=planning_area)
            stations_list.append(weather_station)
        return PlanningAreasResponse(stations=stations_list)

    except Exception as exc:
        logger.critical(exc, exc_info=True)
        raise


def get_wfwx_station(wfwx_stations_data: List[WeatherStation], station_code: int):
    """ Helper function to find station corresponding to station_code from the list of 
    weather stations returned from WFWX. """
    for station in wfwx_stations_data:
        if station.code == station_code:
            return station
    return None
