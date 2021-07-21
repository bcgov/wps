""" Routers for Fire Behaviour Advisory Calculator """

import logging
from datetime import date, datetime, timedelta
from aiohttp.client import ClientSession
from fastapi import APIRouter, Depends
from app.auth import authentication_required, audit
from app.main import get_hourlies
from app.schemas.fba_calc import StationListRequest, StationRequest, StationsListResponse, StationResponse
from app.schemas.shared import WeatherDataRequest
from app.utils import cffdrs
from app.utils.time import get_hour_20_from_date
from app.wildfire_one.schema_parsers import WFWXWeatherStation
from app.wildfire_one.wfwx_api import (get_auth_header,
                                       get_dailies,
                                       get_wfwx_stations_from_station_codes)
from app.utils.fba_calculator import (FBACalculatorWeatherStation,
                                      FireBehaviourAdvisory, calculate_fire_behaviour_advisory)


router = APIRouter(
    prefix="/fba-calc",
    dependencies=[Depends(authentication_required), Depends(audit)]
)

logger = logging.getLogger(__name__)


def prepare_response(
        requested_station: StationRequest,
        wfwx_station: WFWXWeatherStation,
        fba_station: FBACalculatorWeatherStation,
        raw_daily: dict,
        fire_behavour_advisory: FireBehaviourAdvisory,
        time_of_interest: date) -> StationResponse:
    """ Construct a response object combining information from the request, the station from wf1,
    the daily response from wf1 and the fire behaviour advisory. """
    # TODO: Refactor this to simplify the flow of data & sources
    # Extract values from the daily
    bui = raw_daily.get('buildUpIndex', None)
    ffmc = fba_station.ffmc
    isi = fba_station.isi
    wind_speed = requested_station.wind_speed if requested_station.wind_speed is not None else raw_daily.get(
        'windSpeed', None)
    status = fba_station.status
    temp = raw_daily.get('temperature', None)
    rh = raw_daily.get('relativeHumidity', None)  # pylint: disable=invalid-name
    wind_direction = raw_daily.get('windDirection', None)
    precipitation = raw_daily.get('precipitation', None)
    drought_code = raw_daily.get('droughtCode', None)
    duff_moisture_code = raw_daily.get('duffMoistureCode', None)
    fire_weather_index = raw_daily.get('fireWeatherIndex', None)

    station_response = StationResponse(
        station_code=requested_station.station_code,
        station_name=wfwx_station.name,
        date=time_of_interest,
        elevation=wfwx_station.elevation,
        fuel_type=requested_station.fuel_type,
        status=status,
        temp=temp,
        rh=rh,
        wind_speed=wind_speed,
        wind_direction=wind_direction,
        precipitation=precipitation,
        grass_cure=requested_station.grass_cure,  # ignore the grass cure from WF1 api, return input back out
        fine_fuel_moisture_code=ffmc,
        drought_code=drought_code,
        initial_spread_index=isi,
        build_up_index=bui,
        duff_moisture_code=duff_moisture_code,
        fire_weather_index=fire_weather_index,
        head_fire_intensity=fire_behavour_advisory.hfi,
        critical_hours_hfi_4000=fire_behavour_advisory.critical_hours_hfi_4000,
        critical_hours_hfi_10000=fire_behavour_advisory.critical_hours_hfi_10000,
        rate_of_spread=fire_behavour_advisory.ros,
        fire_type=fire_behavour_advisory.fire_type,
        percentage_crown_fraction_burned=fire_behavour_advisory.cfb,
        flame_length=fire_behavour_advisory.flame_length,
        sixty_minute_fire_size=fire_behavour_advisory.sixty_minute_fire_size,
        thirty_minute_fire_size=fire_behavour_advisory.thirty_minute_fire_size
    )

    return station_response


async def process_request(
        dailies_by_station_id: dict,
        hourly_observations_by_station_id: dict,
        wfwx_station: WFWXWeatherStation,
        requested_station: StationRequest,
        time_of_interest: datetime,
        date_of_interest: date) -> StationResponse:
    """ Process a valid request """
    # pylint: disable=too-many-locals
    raw_daily = dailies_by_station_id[wfwx_station.wfwx_id]
    raw_observations = hourly_observations_by_station_id[wfwx_station.wfwx_id]

    logger.info(raw_observations)

    # extract variable from wf1 that we need to calculate the fire behaviour advisory.
    bui = raw_daily.get('buildUpIndex', None)
    temperature = raw_daily.get('temperature', None)
    relative_humidity = raw_daily.get('relativeHumidity', None)
    precipitation = raw_daily.get('precipitation', None)
    wind_direction = raw_daily.get('windDirection', None)
    # if user has not specified wind speed as part of StationRequest, use the
    # values retrieved from WFWX in raw_daily
    if requested_station.wind_speed is None:
        ffmc = raw_daily.get('fineFuelMoistureCode', None)
        isi = raw_daily.get('initialSpreadIndex', None)
        wind_speed = raw_daily.get('windSpeed', None)
        status = raw_daily.get('recordType').get('id')
    # if user has specified wind speed as part of StationRequest, will need to
    # re-calculate FFMC & ISI with modified value of wind speed
    else:
        wind_speed = requested_station.wind_speed
        status = 'ADJUSTED'
        # must retrieve the previous day's observed/forecasted FFMC value from WFWX
        async with ClientSession() as session:
            # authenticate against wfwx api
            header = await get_auth_header(session)
            # set time_of_interest to previous day
            prev_day = time_of_interest - timedelta(days=1)
            # get the "daily" data for the station for the previous day
            yesterday_response = await get_dailies(session, header, [wfwx_station], prev_day)
            # turn it into a dictionary so we can easily get at data
            yesterday = {raw_daily.get('stationId'): raw_daily async for raw_daily in yesterday_response}

        ffmc = cffdrs.fine_fuel_moisture_code(
            yesterday.get(wfwx_station.wfwx_id, '').get('fineFuelMoistureCode', None),
            temperature,
            relative_humidity,
            precipitation,
            wind_speed)
        isi = cffdrs.initial_spread_index(ffmc, wind_speed)

    # Prepare the inputs for the fire behaviour advisory calculation.
    # This is a combination of inputs from the front end, information about the station from wf1
    # and the daily values (observations/forecasts).
    fba_station = FBACalculatorWeatherStation(
        elevation=wfwx_station.elevation,
        fuel_type=requested_station.fuel_type,
        status=status,
        time_of_interest=time_of_interest,
        percentage_conifer=requested_station.percentage_conifer,
        percentage_dead_balsam_fir=requested_station.percentage_dead_balsam_fir,
        grass_cure=requested_station.grass_cure,
        crown_base_height=requested_station.crown_base_height,
        lat=wfwx_station.lat,
        long=wfwx_station.long,
        bui=bui,
        ffmc=ffmc,
        isi=isi,
        prev_day_daily_ffmc=85.0,
        wind_speed=wind_speed,
        wind_direction=wind_direction,
        temperature=temperature,
        relative_humidity=relative_humidity,
        precipitation=precipitation)

    # Calculate the fire behaviour advisory.
    fire_behaviour_advisory = calculate_fire_behaviour_advisory(fba_station)

    # Prepare the response
    return prepare_response(
        requested_station, wfwx_station, fba_station, raw_daily, fire_behaviour_advisory, date_of_interest)


def process_request_without_observation(requested_station: StationRequest,
                                        wfwx_station: WFWXWeatherStation,
                                        date_of_interest: date,
                                        status) -> StationResponse:
    """ Process a request for which no observation/forecast is available """
    station_response = StationResponse(
        station_code=requested_station.station_code,
        station_name=wfwx_station.name,
        date=date_of_interest,
        elevation=wfwx_station.elevation,
        fuel_type=requested_station.fuel_type,
        status=status,
        grass_cure=requested_station.grass_cure,  # ignore the grass cure from WF1 api, return input back out
        wind_speed=requested_station.wind_speed
    )

    return station_response


@router.post('/stations', response_model=StationsListResponse)
async def get_stations_data(  # pylint:disable=too-many-locals
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
            # get hourly observation history from our API (used for calculating morning diurnal FFMC)
            hourly_observations = await get_hourlies(
                request=WeatherDataRequest(
                    stations=unique_station_codes, time_of_interest=time_of_interest))
            # also turn hourly obs data into a dict indexed by station id
            hourly_obs_by_station_id = \
                {raw_hourly.get('stationId'): raw_hourly async for raw_hourly in hourly_observations}

        # we need a lookup from station code to station id
        # TODO: this is a bit silly, the call to get_wfwx_stations_from_station_codes repeats a lot of this!
        wfwx_station_lookup = {wfwx_station.code: wfwx_station for wfwx_station in wfwx_stations}

        stations_response = []
        # for each station code in our station list.
        for requested_station in request.stations:
            # get the wfwx station
            wfwx_station = wfwx_station_lookup[requested_station.station_code]
            # get the raw daily response from wf1.
            if wfwx_station.wfwx_id in dailies_by_station_id and wfwx_station.wfwx_id in hourly_obs_by_station_id:
                try:
                    station_response = await process_request(
                        dailies_by_station_id,
                        hourly_obs_by_station_id,
                        wfwx_station,
                        requested_station,
                        time_of_interest,
                        date_of_interest)
                except Exception as exception:  # pylint: disable=broad-except
                    # If something goes wrong processing the request, then we return this station
                    # with an error response.
                    logger.error('request object: %s', request.__str__())
                    logger.critical(exception, exc_info=True)
                    station_response = process_request_without_observation(
                        requested_station, wfwx_station, date_of_interest, 'ERROR')

            else:
                # if we can't get the daily (no forecast, or no observation)
                station_response = process_request_without_observation(
                    requested_station, wfwx_station, date_of_interest, 'N/A')

            # Add the response to our list of responses
            stations_response.append(station_response)

        return StationsListResponse(stations=stations_response)
    except Exception as exception:
        logger.error('request object: %s', request.__str__())
        logger.critical(exception, exc_info=True)
        raise
