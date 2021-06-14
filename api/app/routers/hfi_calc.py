""" Routers for HFI Calculator """
import logging
from typing import List
from fastapi import APIRouter, Response, Depends
import app
from app import wildfire_one
from app.auth import authentication_required, audit
from app.schemas.hfi_calc import HFIWeatherStationsResponse, WeatherStationProperties,\
    FuelType, FireCentre, PlanningArea, WeatherStation
from app.db.crud.hfi_calc import get_fire_centre_by_id, get_fuel_type_by_id,\
    get_planning_area_by_id, get_planning_weather_stations


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hfi-calc",
    dependencies=[Depends(authentication_required), Depends(audit)]
)


@router.get('/', response_model=HFIWeatherStationsResponse)
# pylint: disable=too-many-locals
async def get_fire_centres(response: Response):
    """ Returns list of fire centres and planning area for each fire centre,
    and weather stations within each planning area. Also returns the assigned fuel type
    for each weather station. """
    try:
        logger.info('/hfi-calc/')
        response.headers["Cache-Control"] = "max-age=0"  # don't let the browser cache this

        with app.db.database.get_read_session_scope() as session:
            station_data = get_planning_weather_stations(session)

            # compile list of station codes from station_data, then send request to WFWX to retrieve
            # station data (station name and elevation)
            station_codes_list = []
            for station in station_data:
                station_codes_list.append(station.station_code)
            wfwx_stations_data = await wildfire_one.get_stations_by_codes(station_codes_list)

            stations_list = []
            for station in station_data:
                fuel = get_fuel_type_by_id(session, station.fuel_type_id)
                fuel_type = FuelType(abbrev=fuel.abbrev, description=fuel.description)
                wfwx_station = get_wfwx_station(wfwx_stations_data, station.station_code)
                station_properties = WeatherStationProperties(
                    name=wfwx_station.name, fuel_type=fuel_type, elevation=wfwx_station.elevation,
                    wfwx_station_uuid=wfwx_station.wfwx_station_uuid)
                zone = get_planning_area_by_id(session, station.planning_area_id)
                fire_centre_from_db = get_fire_centre_by_id(session, zone.fire_centre_id)
                fire_centre = FireCentre(name=fire_centre_from_db.name, id=zone.fire_centre_id)
                planning_area = PlanningArea(
                    name=zone.name, fire_centre=fire_centre, id=station.planning_area_id)
                weather_station = WeatherStation(code=station.station_code,
                                                 station_props=station_properties,
                                                 planning_area=planning_area)
                stations_list.append(weather_station)
            return HFIWeatherStationsResponse(stations=stations_list)

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
