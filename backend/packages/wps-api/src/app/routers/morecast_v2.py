"""Routes for Morecast v2"""

import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import List

from aiohttp.client import ClientSession
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import ORJSONResponse
from wps_wf1.wfwx_api import WfwxApi
from wps_shared.auth import audit, auth_with_forecaster_role_required, authentication_required
from wps_shared.db.crud.grass_curing import get_percent_grass_curing_by_station_for_date_range
from wps_shared.db.crud.hfi_calc import get_fire_centre_station_codes
from wps_shared.db.crud.morecast_v2 import (
    get_forecasts_in_range,
    get_user_forecasts_for_date,
    save_all_forecasts,
)
from wps_shared.db.database import get_read_session_scope, get_write_session_scope
from wps_shared.db.models.morecast_v2 import MorecastForecastRecord
from wps_shared.schemas.morecast_v2 import (
    IndeterminateDailiesResponse,
    MoreCastForecastOutput,
    MoreCastForecastRequest,
    MorecastForecastResponse,
    ObservedDailiesForStations,
    StationDailiesResponse,
    WeatherDeterminate,
    WeatherIndeterminate,
)
from wps_shared.schemas.shared import StationsRequest
from wps_shared.utils.redis import clear_cache_matching
from wps_shared.utils.time import get_hour_20_from_date, get_utc_now, vancouver_tz
from wps_shared.weather_models.fetch.predictions import (
    fetch_latest_model_run_predictions_by_station_code_and_date_range,
)


from app.morecast_v2.forecasts import (
    filter_for_api_forecasts,
    format_as_wf1_post_forecasts,
    get_forecasts,
    get_fwi_values,
    transform_morecastforecastoutput_to_weatherindeterminate,
)

logger = logging.getLogger(__name__)

no_cache = "max-age=0"  # don't let the browser cache this

router = APIRouter(
    prefix="/morecast-v2", dependencies=[Depends(authentication_required), Depends(audit)]
)

WF1_HTTP_ERROR = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="""
        Error submitting forecasts to WF1, please retry.
        All your forecast inputs have been saved as a draft on your browser and can be submitted at a later time.
        If the problem persists, use the following link to verify the status of the WF1 service: https://wfapps.nrs.gov.bc.ca/pub/wfwx-fireweather-web/stations
    """,
)


@router.get("/forecasts/{for_date}")
async def get_forecasts_for_date_and_user(
    for_date: date, response: Response, token=Depends(authentication_required)
) -> List[MorecastForecastResponse]:
    """Return forecasts"""
    logger.info("/forecasts/")
    response.headers["Cache-Control"] = no_cache

    username = token.get("idir_username", None)

    with get_read_session_scope() as db_session:
        return get_user_forecasts_for_date(db_session, username, for_date)


@router.post("/forecasts/{start_date}/{end_date}")
async def get_forecasts_by_date_range(
    start_date: date, end_date: date, request: StationsRequest, response: Response
):
    """Return forecasts for the specified date range and stations"""
    logger.info(f"/forecasts/{start_date}/{end_date}")
    response.headers["Cache-Control"] = no_cache

    start_time = datetime.combine(start_date, time.min, tzinfo=vancouver_tz)
    end_time = datetime.combine(end_date, time.max, tzinfo=vancouver_tz)

    with get_read_session_scope() as db_session:
        result = get_forecasts_in_range(db_session, start_time, end_time, request.stations)
        morecast_forecast_outputs = [
            MoreCastForecastOutput(
                station_code=forecast.station_code,
                for_date=forecast.for_date.timestamp() * 1000,
                temp=forecast.temp,
                rh=forecast.rh,
                precip=forecast.precip,
                wind_speed=forecast.wind_speed,
                wind_direction=forecast.wind_direction,
                grass_curing=forecast.grass_curing,
                update_timestamp=forecast.update_timestamp.timestamp(),
            )
            for forecast in result
        ]
    return MorecastForecastResponse(forecasts=morecast_forecast_outputs)


@router.post("/forecast", status_code=status.HTTP_201_CREATED)
async def save_forecasts(
    forecasts: MoreCastForecastRequest,
    response: Response,
    token=Depends(auth_with_forecaster_role_required),
) -> MorecastForecastResponse:
    """Persist a forecast"""
    logger.info("/forecast")
    response.headers["Cache-Control"] = no_cache
    logger.info("Saving %s forecasts", len(forecasts.forecasts))

    username = token.get("idir_username", None)
    now = get_utc_now()
    forecasts_list = forecasts.forecasts

    forecasts_to_save = [
        MorecastForecastRecord(
            station_code=forecast.station_code,
            for_date=datetime.fromtimestamp(forecast.for_date / 1000, timezone.utc),
            temp=forecast.temp,
            rh=forecast.rh,
            precip=forecast.precip,
            wind_speed=forecast.wind_speed,
            wind_direction=forecast.wind_direction,
            grass_curing=forecast.grass_curing,
            create_user=username,
            create_timestamp=now,
            update_user=username,
            update_timestamp=now,
        )
        for forecast in forecasts_list
    ]

    async with ClientSession() as client_session:
        try:
            wfwx_api = WfwxApi(client_session)
            wf1_forecast_records = await format_as_wf1_post_forecasts(
                wfwx_api, forecasts_list, username
            )
            await wfwx_api.post_forecasts(forecasts=wf1_forecast_records)

            station_ids = [wfwx_station.stationId for wfwx_station in wf1_forecast_records]
            for station_id in station_ids:
                clear_cache_matching(station_id)
        except Exception as exc:
            logger.error("Encountered error posting forecast data to WF1 API", exc_info=exc)
            raise WF1_HTTP_ERROR

    with get_write_session_scope() as db_session:
        save_all_forecasts(db_session, forecasts_to_save)
    morecast_forecast_outputs = [
        MoreCastForecastOutput(
            station_code=forecast.station_code,
            for_date=forecast.for_date,
            temp=forecast.temp,
            rh=forecast.rh,
            precip=forecast.precip,
            wind_speed=forecast.wind_speed,
            wind_direction=forecast.wind_direction,
            grass_curing=forecast.grass_curing,
            update_timestamp=int(now.timestamp() * 1000),
        )
        for forecast in forecasts_list
    ]
    return MorecastForecastResponse(forecasts=morecast_forecast_outputs)


@router.post("/yesterday-dailies/{today}", response_model=StationDailiesResponse)
async def get_yesterdays_actual_dailies(today: date, request: ObservedDailiesForStations):
    """Returns the daily actuals for the day before the requested day."""
    logger.info("/yesterday-dailies/%s/", today)

    unique_station_codes = list(set(request.station_codes))

    time_of_interest = get_hour_20_from_date(today) - timedelta(days=1)
    fire_centre_station_codes = get_fire_centre_station_codes()

    async with ClientSession() as session:
        wfwx_api = WfwxApi(session)

        yesterday_dailies = await wfwx_api.get_dailies_for_stations_and_date(
            time_of_interest, time_of_interest, unique_station_codes, fire_centre_station_codes
        )

        return StationDailiesResponse(dailies=yesterday_dailies)


@router.post("/observed-dailies/{start_date}/{end_date}", response_model=StationDailiesResponse)
async def get_observed_dailies(
    start_date: date, end_date: date, request: ObservedDailiesForStations
):
    """Returns the daily observations for the requested station codes, from the given start_date to the
    most recent date where daily observation data is available.
    """
    logger.info("/observed-dailies/%s/", start_date)

    unique_station_codes = list(set(request.station_codes))

    start_date_of_interest = get_hour_20_from_date(start_date)
    end_date_of_interest = get_hour_20_from_date(end_date)
    fire_centre_station_codes = get_fire_centre_station_codes()

    async with ClientSession() as session:
        wfwx_api = WfwxApi(session)
        observed_dailies = await wfwx_api.get_dailies_for_stations_and_date(
            start_date_of_interest,
            end_date_of_interest,
            unique_station_codes,
            fire_centre_station_codes,
        )

        return StationDailiesResponse(dailies=observed_dailies)


@router.post(
    "/determinates/{start_date}/{end_date}",
    response_model=IndeterminateDailiesResponse,
    response_class=ORJSONResponse,
)
async def get_determinates_for_date_range(
    start_date: date, end_date: date, request: StationsRequest
):
    """Returns the weather values for any actuals, predictions and forecasts for the
    requested stations within the requested date range.
    """
    logger.info("/morecast-v2/determinates/%s/%s", start_date, end_date)

    unique_station_codes = list(set(request.stations))

    start_time = datetime.combine(start_date, time.min, tzinfo=vancouver_tz)
    end_time = datetime.combine(end_date, time.max, tzinfo=vancouver_tz)
    start_date_of_interest = get_hour_20_from_date(start_date)
    end_date_of_interest = get_hour_20_from_date(end_date)
    start_date_for_fwi_calc = start_date_of_interest - timedelta(days=1)

    async with ClientSession() as session:
        fire_centre_station_codes = get_fire_centre_station_codes()
        # get station information from the wfwx api
        wfwx_api = WfwxApi(session)
        wfwx_stations = await wfwx_api.get_wfwx_stations_from_station_codes(
            unique_station_codes, fire_centre_station_codes
        )
        wf1_actuals, wf1_forecasts = await wfwx_api.get_daily_determinates_for_stations_and_date(
            start_date_for_fwi_calc,
            end_date_of_interest,
            unique_station_codes,
            fire_centre_station_codes,
        )

        wf1_actuals, wf1_forecasts = get_fwi_values(wf1_actuals, wf1_forecasts)

        # drop the days before the date of interest that were needed to calculate fwi values
        wf1_actuals = [
            actual for actual in wf1_actuals if actual.utc_timestamp >= start_date_of_interest
        ]
        wf1_forecasts = [
            forecast
            for forecast in wf1_forecasts
            if forecast.utc_timestamp >= start_date_of_interest
        ]

        # Find the min and max dates for actuals from wf1. These define the range of dates for which
        # we need to retrieve forecasts from our API database. Note that not all stations report actuals
        # at the same time, so every station won't necessarily have an actual for each date in the range.
        wf1_actuals_dates = [actual.utc_timestamp for actual in wf1_actuals]
        min_wf1_actuals_date = min(wf1_actuals_dates, default=None)
        max_wf1_actuals_date = max(wf1_actuals_dates, default=None)

    with get_read_session_scope() as db_session:
        forecasts_from_db: List[MoreCastForecastOutput] = get_forecasts(
            db_session, min_wf1_actuals_date, max_wf1_actuals_date, request.stations
        )
        predictions: List[
            WeatherIndeterminate
        ] = await fetch_latest_model_run_predictions_by_station_code_and_date_range(
            db_session, unique_station_codes, start_time, end_time
        )
        station_codes = [station.code for station in wfwx_stations]
        grass_curing_rows = get_percent_grass_curing_by_station_for_date_range(
            db_session, start_time.date(), end_time.date(), station_codes
        )
        grass_curing = []

        for gc_tuple in grass_curing_rows:
            gc_row = gc_tuple[0]
            current_station = [
                station for station in wfwx_stations if station.code == gc_row.station_code
            ][0]
            gc_indeterminate = WeatherIndeterminate(
                determinate=WeatherDeterminate.GRASS_CURING_CWFIS,
                station_code=current_station.code,
                station_name=current_station.name,
                latitude=current_station.lat,
                longitude=current_station.long,
                utc_timestamp=get_hour_20_from_date(gc_row.for_date),
                grass_curing=gc_row.percent_grass_curing,
            )
            grass_curing.append(gc_indeterminate)

        transformed_forecasts = transform_morecastforecastoutput_to_weatherindeterminate(
            forecasts_from_db, wfwx_stations
        )

        # Not all weather stations report actuals at the same time, so we can end up in a situation where
        # for a given date, we need to show the forecast from the wf1 API for one station, and the forecast
        # from our API database for another station. We can check this by testing for the presence of an
        # actual for the given date and station; if an actual exists we use the forecast from our API database.
        transformed_forecasts_to_add = filter_for_api_forecasts(transformed_forecasts, wf1_actuals)

        wf1_forecasts.extend(transformed_forecasts_to_add)

    return IndeterminateDailiesResponse(
        actuals=wf1_actuals,
        forecasts=wf1_forecasts,
        grass_curing=grass_curing,
        predictions=predictions,
    )
