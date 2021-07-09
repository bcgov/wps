""" Routers for Fire Behaviour Advisory Calculator """

import logging
from aiohttp.client import ClientSession
from fastapi import APIRouter, Depends
from app.auth import authentication_required, audit
from app.schemas.fba_calc import StationListRequest, StationsListResponse
from app.utils.time import get_hour_20_from_date
from app.wildfire_one.wfwx_api import (get_auth_header,
                                       get_dailies,
                                       get_wfwx_stations_from_station_codes)
# TODO: move FBACalculatorWeatherStation and generate_station_response somewhere else!
from app.wildfire_one.schema_parsers import FBACalculatorWeatherStation, generate_station_response


router = APIRouter(
    prefix="/fba-calc",
    dependencies=[Depends(authentication_required), Depends(audit)]
)

logger = logging.getLogger(__name__)


@router.post('/stations', response_model=StationsListResponse)
async def get_stations_data(
        request: StationListRequest,
        _=Depends(authentication_required)
):
    """ Returns per-station data for a list of requested stations """
    logger.info('/fba-calc/stations')

    try:

        # build a list of station codes
        station_codes = [station.station_code for station in request.stations]
        # remove any duplicate station codes
        unique_station_codes = list(dict.fromkeys(station_codes))

        # calculate the time of interest
        # TODO: the date should be on the base of the request, not per station.
        date_of_interest = request.date
        if not date_of_interest:
            date_of_interest = request.stations[0].date
        # we're interested in noon on the given day
        time_of_interest = get_hour_20_from_date(date_of_interest)

        async with ClientSession() as session:
            # authenticate against wfwx api
            header = await get_auth_header(session)
            # get station information from the wfwx api
            wfwx_stations = await get_wfwx_stations_from_station_codes(session, header, unique_station_codes)
            # get the dailies for all the stations
            dailies = await get_dailies(session, header, wfwx_stations, time_of_interest)
            # turn it into a dictionary so we can easily get at data using a station id
            dailies_by_station_id = {raw_daily.get('stationId'): raw_daily async for raw_daily in dailies}

        # we need a lookup from station code to station id
        # TODO: this is a bit silly, the call to get_wfwx_stations_from_station_codes repeats a lot of this!
        wfwx_station_lookup = {wfwx_station.code: wfwx_station for wfwx_station in wfwx_stations}

        stations_response = []
        # for each station code in our station list
        for requested_station in request.stations:
            # get station id from station code
            wfwx_station = wfwx_station_lookup[requested_station.station_code]
            raw_daily = dailies_by_station_id[wfwx_station.wfwx_id]
            fba_station = FBACalculatorWeatherStation(
                wfwx_id=wfwx_station.wfwx_id,
                code=requested_station.station_code,
                elevation=wfwx_station.elevation,
                fuel_type=requested_station.fuel_type,
                time_of_interest=time_of_interest,
                percentage_conifer=requested_station.percentage_conifer,
                percentage_dead_balsam_fir=requested_station.percentage_dead_balsam_fir,
                grass_cure=requested_station.grass_cure,
                crown_base_height=requested_station.crown_base_height,
                lat=wfwx_station.lat,
                long=wfwx_station.long,
                name=wfwx_station.name)

            daily = generate_station_response(raw_daily, fba_station)
            stations_response.append(daily)

            # stations_response.append()
        return StationsListResponse(stations=stations_response)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise
