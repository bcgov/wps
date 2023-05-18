""" Routes for Morecast v2 """
import logging
from aiohttp.client import ClientSession
import pytz
from typing import List
from datetime import date, datetime, time, timedelta, timezone
from fastapi import APIRouter, Response, Depends, status
from app.auth import (auth_with_forecaster_role_required,
                      audit,
                      authentication_required)
from app.db.crud.morecast_v2 import get_forecasts_in_range, get_user_forecasts_for_date, save_all_forecasts
from app.db.database import get_read_session_scope, get_write_session_scope
from app.db.models.morecast_v2 import MorecastForecastRecord
from app.morecast_v2.forecasts import get_forecasts
from app.schemas.morecast_v2 import (IndeterminateDailiesResponse,
                                     MoreCastForecastOutput,
                                     MoreCastForecastRequest,
                                     MorecastForecastResponse,
                                     ObservedDailiesForStations,
                                     ObservedStationDailiesResponse,
                                     WeatherIndeterminate, WildfireOneForecastRequest)
from app.schemas.shared import StationsRequest
from app.utils.time import get_hour_20_from_date, get_utc_now
from app.weather_models.fetch.predictions import fetch_latest_model_run_predictions_by_station_code_and_date_range
from app.wildfire_one.wfwx_api import get_auth_header, get_dailies_for_stations_and_date, get_daily_determinates_for_stations_and_date


logger = logging.getLogger(__name__)

no_cache = "max-age=0"  # don't let the browser cache this

router = APIRouter(
    prefix="/morecast-v2",
    dependencies=[Depends(authentication_required), Depends(audit)]
)


@router.get("/forecasts/{for_date}")
async def get_forecasts_for_date_and_user(for_date: date,
                                          response: Response,
                                          token=Depends(authentication_required)) -> List[MorecastForecastResponse]:
    """ Return forecasts """
    logger.info('/forecasts/')
    response.headers["Cache-Control"] = no_cache

    username = token.get('idir_username', None)

    with get_read_session_scope() as db_session:
        return get_user_forecasts_for_date(db_session, username, for_date)


@router.post("/forecasts/{start_date}/{end_date}")
async def get_forecasts_by_date_range(start_date: date, end_date: date, request: StationsRequest, response: Response):
    """ Return forecasts for the specified date range and stations """
    logger.info(f"/forecast/{start_date}/{end_date}")
    response.headers["Cache-Control"] = no_cache

    vancouver_tz = pytz.timezone("America/Vancouver")

    start_time = vancouver_tz.localize(datetime.combine(start_date, time.min))
    end_time = vancouver_tz.localize(datetime.combine(end_date, time.max))

    with get_read_session_scope() as db_session:
        result = get_forecasts_in_range(db_session, start_time, end_time, request.stations)
        morecast_forecast_outputs = [MoreCastForecastOutput(station_code=forecast.station_code,
                                                            for_date=forecast.for_date.timestamp() * 1000,
                                                            temp=forecast.temp,
                                                            rh=forecast.rh,
                                                            precip=forecast.precip,
                                                            wind_speed=forecast.wind_speed,
                                                            wind_direction=forecast.wind_direction,
                                                            update_timestamp=forecast.update_timestamp.timestamp()) for forecast in result]
    return MorecastForecastResponse(forecasts=morecast_forecast_outputs)


@router.post("/forecast", status_code=status.HTTP_201_CREATED)
async def save_forecasts(forecasts: MoreCastForecastRequest,
                         response: Response,
                         token=Depends(auth_with_forecaster_role_required)) -> MorecastForecastResponse:
    """ Persist a forecast """
    logger.info('/forecast')
    response.headers["Cache-Control"] = no_cache
    logger.info('Saving %s forecasts', len(forecasts.forecasts))

    username = token.get('idir_username', None)
    now = get_utc_now()
    forecasts_list = forecasts.forecasts

    forecasts_to_save = [MorecastForecastRecord(station_code=forecast.station_code,
                                                for_date=datetime.fromtimestamp(forecast.for_date / 1000, timezone.utc),
                                                temp=forecast.temp,
                                                rh=forecast.rh,
                                                precip=forecast.precip,
                                                wind_speed=forecast.wind_speed,
                                                wind_direction=forecast.wind_direction,
                                                create_user=username,
                                                create_timestamp=now,
                                                update_user=username,
                                                update_timestamp=now) for forecast in forecasts_list]
    # write forecasts to our database
    with get_write_session_scope() as db_session:
        save_all_forecasts(db_session, forecasts_to_save)
    morecast_forecast_outputs = [MoreCastForecastOutput(station_code=forecast.station_code,
                                                        for_date=forecast.for_date,
                                                        temp=forecast.temp,
                                                        rh=forecast.rh,
                                                        precip=forecast.precip,
                                                        wind_speed=forecast.wind_speed,
                                                        wind_direction=forecast.wind_direction,
                                                        update_timestamp=int(now.timestamp() * 1000)) for forecast in forecasts_list]

    # send forecasts to WF1 API
    wildfire_one_forecast_requests = []
    for forecast in forecasts_to_save:
        wildfire_one_forecast_requests.append(WildfireOneForecastRequest(
            # TODO: need to get station UUID from ... ?
            stationId='1',
            weatherTimestamp=forecast.for_date,
            updateDate=get_utc_now().replace(tzinfo=timezone.utc).timestamp() * 1000,
            # TODO: insert user id strings
            createdBy='',
            lastModifiedBy='',
            temperature=forecast.temp,
            relativeHumidity=forecast.rh,
            windSpeed=forecast.wind_speed,
            windDirection=forecast.wind_direction
        ))

    return MorecastForecastResponse(forecasts=morecast_forecast_outputs)


@router.post('/yesterday-dailies/{today}',
             response_model=ObservedStationDailiesResponse)
async def get_yesterdays_actual_dailies(today: date, request: ObservedDailiesForStations):
    """ Returns the daily actuals for the day before the requested day.
    """
    logger.info('/yesterday-dailies/%s/', today)

    unique_station_codes = list(set(request.station_codes))

    time_of_interest = get_hour_20_from_date(today) - timedelta(days=1)

    async with ClientSession() as session:
        header = await get_auth_header(session)

        yeserday_dailies = await get_dailies_for_stations_and_date(session, header, time_of_interest,
                                                                   time_of_interest, unique_station_codes)

        return ObservedStationDailiesResponse(dailies=yeserday_dailies)


@router.post('/observed-dailies/{start_date}/{end_date}',
             response_model=ObservedStationDailiesResponse)
async def get_observed_dailies(start_date: date, end_date: date, request: ObservedDailiesForStations):
    """ Returns the daily observations for the requested station codes, from the given start_date to the
    most recent date where daily observation data is available.
    """
    logger.info('/observed-dailies/%s/', start_date)

    unique_station_codes = list(set(request.station_codes))

    start_date_of_interest = get_hour_20_from_date(start_date)
    end_date_of_interest = get_hour_20_from_date(end_date)

    async with ClientSession() as session:
        header = await get_auth_header(session)
        observed_dailies = await get_dailies_for_stations_and_date(session, header,
                                                                   start_date_of_interest, end_date_of_interest,
                                                                   unique_station_codes)

        return ObservedStationDailiesResponse(dailies=observed_dailies)


@router.post('/determinates/{start_date}/{end_date}',
             response_model=IndeterminateDailiesResponse)
async def get_determinates_for_date_range(start_date: date,
                                          end_date: date,
                                          request: StationsRequest):
    """ Returns the weather values for any actuals, predictions and forecasts for the 
    requested stations within the requested date range.
    """
    logger.info('/morecast-v2/determinates/%s/%s', start_date, end_date)

    unique_station_codes = list(set(request.stations))

    vancouver_tz = pytz.timezone("America/Vancouver")

    start_time = vancouver_tz.localize(datetime.combine(start_date, time.min))
    end_time = vancouver_tz.localize(datetime.combine(end_date, time.max))

    with get_read_session_scope() as db_session:
        forecasts: List[MoreCastForecastOutput] = get_forecasts(db_session, start_time, end_time, request.stations)
        predictions: List[WeatherIndeterminate] = await fetch_latest_model_run_predictions_by_station_code_and_date_range(db_session,
                                                                                                                          unique_station_codes,
                                                                                                                          start_time, end_time)

    start_date_of_interest = get_hour_20_from_date(start_date)
    end_date_of_interest = get_hour_20_from_date(end_date)

    async with ClientSession() as session:
        header = await get_auth_header(session)
        actuals: List[WeatherIndeterminate] = await get_daily_determinates_for_stations_and_date(session, header,
                                                                                                 start_date_of_interest,
                                                                                                 end_date_of_interest,
                                                                                                 unique_station_codes)
    return IndeterminateDailiesResponse(
        actuals=actuals,
        predictions=predictions,
        forecasts=forecasts)
