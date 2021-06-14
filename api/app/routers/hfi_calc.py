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
            # Fetch all fire weather stations from the database.
            station_query = get_fire_weather_stations(session)
            # Prepare a dictionary for storing station info in.
            station_info_dict = {}
            # Iterate through all the database records, collecting all the data we need.
            for (station_record, fuel_type_record, planning_area_record, fire_centre_record) in station_query:
                station_info_dict[station_record.station_code] = {
                    'fuel_type': FuelType(
                        abbrev=fuel_type_record.abbrev,
                        description=fuel_type_record.description),
                    'planning_area': PlanningArea(
                        name=planning_area_record.name,
                        fire_centre=FireCentre(name=fire_centre_record.name)
                    )

                }

            # We're still missing some data that we need from wfwx, so give it the list of stations
            wfwx_stations_data = await wildfire_one.get_stations_by_codes(list(station_info_dict.keys()))
            # Prepare a list to store our final station objects in.
            stations_list: List[WeatherStation] = []
            # Iterate through all the stations from wildfire one.
            for wfwx_station in wfwx_stations_data:
                station_info = station_info_dict[wfwx_station.code]
                # Combine everything.
                station_properties = WeatherStationProperties(
                    name=wfwx_station.name,
                    fuel_type=station_info['fuel_type'],
                    elevation=wfwx_station.elevation,
                    wfwx_station_uuid=wfwx_station.wfwx_station_uuid)

                weather_station = WeatherStation(code=wfwx_station.code,
                                                 station_props=station_properties,
                                                 planning_area=station_info['planning_area'])

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
