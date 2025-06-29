"""Routers for Fire Behaviour Advisory Calculator"""

import logging
from datetime import date, datetime, timedelta
from aiohttp.client import ClientSession
from fastapi import APIRouter, Depends
from wps_shared.auth import authentication_required, audit
from app.fire_behaviour.advisory import (
    FBACalculatorWeatherStation,
    FireBehaviourAdvisory,
    calculate_fire_behaviour_advisory,
)
from app.fire_behaviour.fwi_adjust import calculate_adjusted_fwi_result
from app.hourlies import get_hourly_readings_in_time_interval
from wps_shared.schemas.fba_calc import (
    StationListRequest,
    StationRequest,
    StationsListResponse,
    StationResponse,
)
from wps_shared.utils.time import get_hour_20_from_date
from wps_shared.wildfire_one.schema_parsers import WFWXWeatherStation
from wps_shared.wildfire_one.wfwx_api import (
    get_auth_header,
    get_dailies_generator,
    get_wfwx_stations_from_station_codes,
)
from app.fire_behaviour.prediction import build_hourly_rh_dict


router = APIRouter(
    prefix="/fba-calc", dependencies=[Depends(authentication_required), Depends(audit)]
)

logger = logging.getLogger(__name__)


def prepare_response(
    requested_station: StationRequest,
    wfwx_station: WFWXWeatherStation,
    fba_station: FBACalculatorWeatherStation,
    raw_daily: dict,
    fire_behaviour_advisory: FireBehaviourAdvisory,
) -> StationResponse:
    """Construct a response object combining information from the request, the station from wf1,
    the daily response from wf1 and the fire behaviour advisory."""
    # TODO: Refactor this to simplify the flow of data & sources
    duff_moisture_code = fba_station.dmc
    drought_code = fba_station.dc
    bui = fba_station.bui
    ffmc = fba_station.ffmc
    isi = fba_station.isi
    fire_weather_index = fba_station.fwi
    wind_speed = (
        requested_station.wind_speed
        if requested_station.wind_speed is not None
        else raw_daily.get("windSpeed", None)
    )
    status = fba_station.status
    temp = raw_daily.get("temperature", None)
    rh = raw_daily.get("relativeHumidity", None)
    wind_direction = raw_daily.get("windDirection", None)
    precipitation = (
        requested_station.precipitation
        if requested_station.precipitation is not None
        else raw_daily.get("precipitation", None)
    )

    station_response = StationResponse(
        id=None if requested_station.id is None else requested_station.id,
        station_code=requested_station.station_code,
        station_name=wfwx_station.name,
        zone_code=wfwx_station.zone_code,
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
        head_fire_intensity=fire_behaviour_advisory.hfi,
        critical_hours_hfi_4000=fire_behaviour_advisory.critical_hours_hfi_4000,
        critical_hours_hfi_10000=fire_behaviour_advisory.critical_hours_hfi_10000,
        rate_of_spread=fire_behaviour_advisory.ros,
        fire_type=fire_behaviour_advisory.fire_type,
        percentage_crown_fraction_burned=fire_behaviour_advisory.cfb,
        flame_length=fire_behaviour_advisory.flame_length,
        sixty_minute_fire_size=fire_behaviour_advisory.sixty_minute_fire_size,
        thirty_minute_fire_size=fire_behaviour_advisory.thirty_minute_fire_size,
    )

    return station_response


async def process_request(
    dailies_by_station_id: dict,
    yesterday_dailies_by_station_id: dict,
    hourly_observations_by_station_id: dict,
    wfwx_station: WFWXWeatherStation,
    requested_station: StationRequest,
    time_of_interest: datetime,
) -> StationResponse:
    """Process a valid request"""

    raw_daily = dailies_by_station_id[wfwx_station.wfwx_id]
    raw_observations = hourly_observations_by_station_id[wfwx_station.code]
    yesterday = yesterday_dailies_by_station_id[wfwx_station.wfwx_id]
    last_observed_morning_rh_values = build_hourly_rh_dict(raw_observations.values)

    # extract variable from wf1 that we need to calculate the fire behaviour advisory.
    temperature = raw_daily.get("temperature", None)
    relative_humidity = raw_daily.get("relativeHumidity", None)
    wind_direction = raw_daily.get("windDirection", None)
    adjusted_fwi_result = calculate_adjusted_fwi_result(
        requested_station, wfwx_station, time_of_interest, yesterday, raw_daily
    )

    # Prepare the inputs for the fire behaviour advisory calculation.
    # This is a combination of inputs from the front end, information about the station from wf1
    # and the daily values (observations/forecasts).
    fba_station = FBACalculatorWeatherStation(
        elevation=wfwx_station.elevation,
        fuel_type=requested_station.fuel_type,
        status=adjusted_fwi_result.status,
        time_of_interest=time_of_interest,
        percentage_conifer=requested_station.percentage_conifer,
        percentage_dead_balsam_fir=requested_station.percentage_dead_balsam_fir,
        grass_cure=requested_station.grass_cure,
        crown_base_height=requested_station.crown_base_height,
        crown_fuel_load=requested_station.crown_fuel_load,
        lat=wfwx_station.lat,
        long=wfwx_station.long,
        bui=adjusted_fwi_result.bui,
        dmc=adjusted_fwi_result.dmc,
        dc=adjusted_fwi_result.dc,
        ffmc=adjusted_fwi_result.ffmc,
        isi=adjusted_fwi_result.isi,
        fwi=adjusted_fwi_result.fwi,
        prev_day_daily_ffmc=yesterday.get("fineFuelMoistureCode", None),
        precipitation=adjusted_fwi_result.precipitation,
        wind_speed=adjusted_fwi_result.wind_speed,
        wind_direction=wind_direction,
        temperature=temperature,
        relative_humidity=relative_humidity,
        last_observed_morning_rh_values=last_observed_morning_rh_values,
    )

    # Calculate the fire behaviour advisory.
    fire_behaviour_advisory = calculate_fire_behaviour_advisory(fba_station)

    # Prepare the response
    return prepare_response(
        requested_station, wfwx_station, fba_station, raw_daily, fire_behaviour_advisory
    )


def process_request_without_observation(
    requested_station: StationRequest,
    wfwx_station: WFWXWeatherStation,
    date_of_interest: date,
    status,
) -> StationResponse:
    """Process a request for which no observation/forecast is available"""
    station_response = StationResponse(
        id=None if requested_station.id is None else requested_station.id,
        zone_code=wfwx_station.zone_code,
        station_code=requested_station.station_code,
        station_name=wfwx_station.name,
        date=date_of_interest,
        elevation=wfwx_station.elevation,
        fuel_type=requested_station.fuel_type,
        status=status,
        grass_cure=requested_station.grass_cure,  # ignore the grass cure from WF1 api, return input back out
        wind_speed=requested_station.wind_speed,
    )

    return station_response


@router.post("/stations", response_model=StationsListResponse)
async def get_stations_data(request: StationListRequest, _=Depends(authentication_required)):
    """Returns per-station data for a list of requested stations"""
    logger.info("/fba-calc/stations")
    try:
        # build a list of station codes
        station_codes = [station.station_code for station in request.stations]
        # remove any duplicate station codes
        unique_station_codes = list(dict.fromkeys(station_codes))

        # we're interested in noon on the given day
        time_of_interest = get_hour_20_from_date(request.date)

        async with ClientSession() as session:
            # authenticate against wfwx api
            header = await get_auth_header(session)
            # get station information from the wfwx api
            wfwx_stations = await get_wfwx_stations_from_station_codes(
                session, header, unique_station_codes
            )
            # get the dailies for all the stations
            dailies = await get_dailies_generator(
                session, header, wfwx_stations, time_of_interest, time_of_interest
            )
            # turn it into a dictionary so we can easily get at data using a station id
            dailies_by_station_id = {
                raw_daily.get("stationId"): raw_daily async for raw_daily in dailies
            }
            # must retrieve the previous day's observed/forecasted FFMC value from WFWX
            prev_day = time_of_interest - timedelta(days=1)
            # get the "daily" data for the station for the previous day
            yesterday_response = await get_dailies_generator(
                session, header, wfwx_stations, prev_day, prev_day
            )
            # turn it into a dictionary so we can easily get at data
            yesterday_dailies_by_station_id = {
                raw_daily.get("stationId"): raw_daily async for raw_daily in yesterday_response
            }
            # get hourly observation history from our API (used for calculating morning diurnal FFMC)
            hourly_observations = await get_hourly_readings_in_time_interval(
                unique_station_codes, time_of_interest - timedelta(days=4), time_of_interest
            )
            # also turn hourly obs data into a dict indexed by station id
            hourly_obs_by_station_code = {
                raw_hourly.station.code: raw_hourly for raw_hourly in hourly_observations
            }

        # we need a lookup from station code to station id
        # TODO: this is a bit silly, the call to get_wfwx_stations_from_station_codes repeats a lot of this!
        wfwx_station_lookup = {wfwx_station.code: wfwx_station for wfwx_station in wfwx_stations}

        stations_response = []
        # for each station code in our station list.
        for requested_station in request.stations:
            # get the wfwx station
            wfwx_station = wfwx_station_lookup[requested_station.station_code]
            # get the raw daily response from wf1.
            if (
                wfwx_station.wfwx_id in dailies_by_station_id
                and requested_station.station_code in hourly_obs_by_station_code
            ):
                try:
                    station_response = await process_request(
                        dailies_by_station_id,
                        yesterday_dailies_by_station_id,
                        hourly_obs_by_station_code,
                        wfwx_station,
                        requested_station,
                        time_of_interest,
                    )
                except Exception as exception:
                    # If something goes wrong processing the request, then we return this station
                    # with an error response.
                    logger.error("request object: %s", request.__str__())
                    logger.critical(exception, exc_info=True)
                    station_response = process_request_without_observation(
                        requested_station, wfwx_station, request.date, "ERROR"
                    )

            else:
                # if we can't get the daily (no forecast, or no observation)
                station_response = process_request_without_observation(
                    requested_station, wfwx_station, request.date, "N/A"
                )

            # Add the response to our list of responses
            stations_response.append(station_response)

        return StationsListResponse(date=request.date, stations=stations_response)
    except Exception as exception:
        logger.error("request object: %s", request.__str__())
        logger.critical(exception, exc_info=True)
        raise
