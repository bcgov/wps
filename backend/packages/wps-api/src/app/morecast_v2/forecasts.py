import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from urllib.parse import urljoin

from aiohttp import ClientResponseError
from cffdrs import (
    buildup_index,
    drought_code,
    duff_moisture_code,
    fine_fuel_moisture_code,
    fire_weather_index,
    initial_spread_index,
)
from sqlalchemy.orm import Session
from wps_shared import config
from wps_shared.db.crud.hfi_calc import get_fire_centre_station_codes
from wps_shared.db.crud.morecast_v2 import get_forecasts_in_range
from wps_shared.schemas.morecast_v2 import (
    MoreCastForecastInput,
    MoreCastForecastOutput,
    WeatherDeterminate,
    WeatherIndeterminate,
    WF1ForecastRecordType,
    WF1PostForecast,
    WF1SkippedForecast,
)
from wps_shared.schemas.stations import WFWXWeatherStation
from wps_wf1.util import is_station_valid
from wps_wf1.wfwx_api import WfwxApi

logger = logging.getLogger(__name__)


def get_forecasts(
    db_session: Session,
    start_time: Optional[datetime],
    end_time: Optional[datetime],
    station_codes: List[int],
) -> List[MoreCastForecastOutput]:
    if start_time is None or end_time is None:
        return []

    result = get_forecasts_in_range(db_session, start_time, end_time, station_codes)

    forecasts: List[MoreCastForecastOutput] = [
        MoreCastForecastOutput(
            station_code=forecast.station_code,
            for_date=forecast.for_date.timestamp() * 1000,
            temp=forecast.temp,
            rh=forecast.rh,
            precip=forecast.precip,
            wind_speed=forecast.wind_speed,
            wind_direction=forecast.wind_direction,
            grass_curing=forecast.grass_curing,
            update_timestamp=int(forecast.update_timestamp.timestamp()),
        )
        for forecast in result
    ]
    return forecasts


def construct_wf1_forecast(
    forecast: MoreCastForecastInput,
    stations: List[WFWXWeatherStation],
    forecast_id: Optional[str],
    created_by: Optional[str],
) -> WF1PostForecast:
    station = next(filter(lambda obj: obj.code == forecast.station_code, stations))
    station_id = station.wfwx_id
    station_url = urljoin(
        config.get("WFWX_BASE_URL"), f"wfwx-fireweather-api/v1/stations/{station_id}"
    )
    wf1_post_forecast = WF1PostForecast(
        createdBy=created_by,
        id=forecast_id,
        stationId=station_id,
        station=station_url,
        temperature=forecast.temp,
        relativeHumidity=forecast.rh,
        precipitation=forecast.precip,
        windSpeed=forecast.wind_speed,
        windDirection=forecast.wind_direction,
        weatherTimestamp=forecast.for_date,
        recordType=WF1ForecastRecordType(),
        grasslandCuring=forecast.grass_curing,
    )
    return wf1_post_forecast


@dataclass
class WF1ForecastSubmission:
    forecasts: list[WF1PostForecast]
    skipped: list[WF1SkippedForecast]
    station_ids: list[str]


async def _get_existing_wf1_dailies(
    wfwx_api: WfwxApi,
    forecast_records: List[MoreCastForecastInput],
    stations: List[WFWXWeatherStation],
) -> tuple[dict[tuple[int, int], dict], set[tuple[int, int]]]:
    timestamps = [record.for_date for record in forecast_records]
    dailies = await wfwx_api.get_dailies_generator(
        wfwx_stations=stations,
        time_of_interest=datetime.fromtimestamp(min(timestamps) / 1000, timezone.utc),
        end_time_of_interest=datetime.fromtimestamp(max(timestamps) / 1000, timezone.utc),
        check_cache=False,
        use_no_cache_header=True,
    )
    existing_forecasts = {}
    observed_keys = set()
    async for daily in dailies:
        if not is_station_valid(daily.get("stationData")):
            continue
        key = (daily["stationData"]["stationCode"], daily["weatherTimestamp"])
        record_type = daily["recordType"]["id"]
        if record_type in ("ACTUAL", "MANUAL"):
            observed_keys.add(key)
        elif record_type == "FORECAST":
            existing_forecasts[key] = daily
    return existing_forecasts, observed_keys


async def construct_wf1_forecasts(
    wfwx_api: WfwxApi,
    forecast_records: List[MoreCastForecastInput],
    stations: List[WFWXWeatherStation],
    username: str,
) -> WF1ForecastSubmission:
    submission = WF1ForecastSubmission([], [], [station.wfwx_id for station in stations])
    if not forecast_records:
        return submission

    existing_forecasts, observed_keys = await _get_existing_wf1_dailies(
        wfwx_api, forecast_records, stations
    )
    station_names = {station.code: station.name for station in stations}
    for forecast in forecast_records:
        key = (forecast.station_code, forecast.for_date)
        if key in observed_keys:
            submission.skipped.append(
                WF1SkippedForecast(
                    station_code=forecast.station_code,
                    station_name=station_names[forecast.station_code],
                    for_date=forecast.for_date,
                )
            )
            continue
        daily = existing_forecasts.get(key)
        submission.forecasts.append(
            construct_wf1_forecast(
                forecast,
                stations,
                daily["id"] if daily is not None else None,
                daily["createdBy"] if daily is not None else username,
            )
        )
    return submission


async def format_as_wf1_post_forecasts(
    wfwx_api: WfwxApi,
    forecast_records: List[MoreCastForecastInput],
    username: str,
) -> WF1ForecastSubmission:
    if not forecast_records:
        return WF1ForecastSubmission([], [], [])
    station_codes = list({record.station_code for record in forecast_records})
    fire_centre_station_codes = get_fire_centre_station_codes()
    stations = await wfwx_api.get_wfwx_stations_from_station_codes(
        station_codes, fire_centre_station_codes, use_no_cache_header=True
    )
    return await construct_wf1_forecasts(wfwx_api, forecast_records, stations, username)


async def publish_wf1_forecasts(
    wfwx_api: WfwxApi,
    forecast_records: List[MoreCastForecastInput],
    username: str,
    *,
    max_retries: int = 1,
) -> WF1ForecastSubmission:
    if max_retries < 0:
        raise ValueError("max_retries must be nonnegative")

    submission = await format_as_wf1_post_forecasts(wfwx_api, forecast_records, username)
    retries_remaining = max_retries
    while submission.forecasts:
        try:
            await wfwx_api.post_forecasts(forecasts=submission.forecasts)
            return submission
        except ClientResponseError as exc:
            if exc.status != 400 or retries_remaining == 0:
                raise
            skipped_keys = {(row.station_code, row.for_date) for row in submission.skipped}
            attempted_records = [
                row
                for row in forecast_records
                if (row.station_code, row.for_date) not in skipped_keys
            ]
            # refresh forecast IDs too in case WF1 wrote any rows before rejecting the batch
            retry = await format_as_wf1_post_forecasts(wfwx_api, attempted_records, username)
            if not retry.skipped:
                raise
            retries_remaining -= 1
            logger.info(
                "Retrying WF1 submission %s/%s after %s new actuals",
                max_retries - retries_remaining,
                max_retries,
                len(retry.skipped),
            )
            submission.forecasts = retry.forecasts
            submission.skipped.extend(retry.skipped)
    return submission


def actual_exists(forecast: WeatherIndeterminate, actuals: List[WeatherIndeterminate]):
    """Returns True if the actuals contain a WeatherIndeterminate with station_code and utc_timestamp that
    matches those of the forecast; otherwise, returns False."""
    station_code_matches = [
        actual for actual in actuals if actual.station_code == forecast.station_code
    ]
    utc_timestamp_matches = [
        station_code_match
        for station_code_match in station_code_matches
        if station_code_match.utc_timestamp == forecast.utc_timestamp
    ]
    return len(utc_timestamp_matches) > 0


def filter_for_api_forecasts(
    forecasts: List[WeatherIndeterminate], actuals: List[WeatherIndeterminate]
):
    """Returns a list of forecasts where each forecast has a corresponding WeatherIndeterminate in the
    actuals with a matching station_code and utc_timestamp."""
    filtered_forecasts = []
    for forecast in forecasts:
        if actual_exists(forecast, actuals):
            filtered_forecasts.append(forecast)
    return filtered_forecasts


def get_fwi_values(
    actuals: List[WeatherIndeterminate], forecasts: List[WeatherIndeterminate]
) -> Tuple[List[WeatherIndeterminate], List[WeatherIndeterminate]]:
    """
    Calculates actuals and forecasts with Fire Weather Index System values by calculating based off previous actuals and subsequent forecasts.

    :param actuals: List of actual weather values
    :type actuals: List[WeatherIndeterminate]
    :param forecasts: List of existing forecasted values
    :type forecasts: List[WeatherIndeterminate]
    :return: Actuals and forecasts with calculated fire weather index values
    :rtype: Tuple[List[WeatherIndeterminate], List[WeatherIndeterminate]
    """
    all_indeterminates = actuals + forecasts
    indeterminates_dict = defaultdict(dict)

    # Shape indeterminates into nested dicts for quick and easy look ups by station code and date
    for indeterminate in all_indeterminates:
        indeterminates_dict[indeterminate.station_code][indeterminate.utc_timestamp.date()] = (
            indeterminate
        )

    for idx, indeterminate in enumerate(all_indeterminates):
        last_indeterminate = indeterminates_dict[indeterminate.station_code].get(
            indeterminate.utc_timestamp.date() - timedelta(days=1), None
        )
        if last_indeterminate is not None:
            updated_forecast = calculate_fwi_values(last_indeterminate, indeterminate)
            all_indeterminates[idx] = updated_forecast

    updated_forecasts = [
        indeterminate
        for indeterminate in all_indeterminates
        if indeterminate.determinate == WeatherDeterminate.FORECAST
    ]
    updated_actuals = [
        indeterminate
        for indeterminate in all_indeterminates
        if indeterminate.determinate == WeatherDeterminate.ACTUAL
    ]

    return updated_actuals, updated_forecasts


def indeterminate_missing_fwi(indeterminate: WeatherIndeterminate):
    return (
        indeterminate.fine_fuel_moisture_code is None
        or indeterminate.duff_moisture_code is None
        or indeterminate.drought_code is None
        or indeterminate.initial_spread_index is None
        or indeterminate.build_up_index is None
    )


def calculate_fwi_from_seed_indeterminates(
    seed_indeterminates: List[WeatherIndeterminate],
    target_indeterminates: List[WeatherIndeterminate],
) -> List[WeatherIndeterminate]:
    """
    Calculates FWI values for a list of target indeterminates based on seed indeterminates.

    :param seed_indeterminates: List of seed WeatherIndeterminate objects used as the base for calculations
    :param target_indeterminates: List of WeatherIndeterminate objects that need FWI values calculated
    :return: List of updated WeatherIndeterminate objects with calculated FWI values
    """
    # Combine seed and target indeterminates for lookup
    all_indeterminates = seed_indeterminates + target_indeterminates
    indeterminates_dict = defaultdict(dict)

    # Shape indeterminates into nested dicts for quick lookups by station code and date
    for indeterminate in all_indeterminates:
        indeterminates_dict[indeterminate.station_code][indeterminate.utc_timestamp.date()] = (
            indeterminate
        )

    # Calculate FWI values for target indeterminates
    for idx, indeterminate in enumerate(target_indeterminates):
        previous_date = indeterminate.utc_timestamp.date() - timedelta(days=1)
        last_indeterminate = indeterminates_dict[indeterminate.station_code].get(
            previous_date, None
        )
        if last_indeterminate is not None and indeterminate_missing_fwi(indeterminate):
            # If the target indeterminate already has FWI values, skip calculation
            target_indeterminates[idx] = calculate_fwi_values(last_indeterminate, indeterminate)

    return target_indeterminates


def calculate_fwi_values(
    yesterday: WeatherIndeterminate, today: WeatherIndeterminate
) -> WeatherIndeterminate:
    """
    Uses CFFDRS library to calculate Fire Weather Index System values

    :param yesterday: The WeatherIndeterminate from the day before the date to calculate
    :type yesterday: WeatherIndeterminate
    :param today: The WeatherIndeterminate from the date to calculate
    :type today: WeatherIndeterminate
    :return: Updated WeatherIndeterminate
    :rtype: WeatherIndeterminate
    """

    # weather params for calculation date
    month_to_calculate_for = int(today.utc_timestamp.strftime("%m"))
    latitude = today.latitude
    temp = today.temperature
    rh = today.relative_humidity
    precip = today.precipitation
    wind_spd = today.wind_speed

    if any(value is None for value in [temp, rh, precip, wind_spd]):
        # All the FWIs should already be None if a weather variable is None but let's explicitly set
        # them to None to prevent erroneous data from being provided to the front end.
        today.fine_fuel_moisture_code = None
        today.duff_moisture_code = None
        today.drought_code = None
        today.initial_spread_index = None
        today.build_up_index = None
        today.fire_weather_index = None
        return today

    if yesterday.fine_fuel_moisture_code is not None:
        today.fine_fuel_moisture_code = fine_fuel_moisture_code(
            ffmc_yda=yesterday.fine_fuel_moisture_code, temp=temp, rh=rh, prec=precip, ws=wind_spd
        )
    if yesterday.duff_moisture_code is not None:
        today.duff_moisture_code = duff_moisture_code(
            dmc_yda=yesterday.duff_moisture_code,
            temp=temp,
            rh=rh,
            prec=precip,
            lat=latitude,
            mon=month_to_calculate_for,
            lat_adjust=True,
        )
    if yesterday.drought_code is not None:
        today.drought_code = drought_code(
            dc_yda=yesterday.drought_code,
            temp=temp,
            rh=rh,
            prec=precip,
            lat=latitude,
            mon=month_to_calculate_for,
            lat_adjust=True,
        )
    if today.fine_fuel_moisture_code is not None:
        today.initial_spread_index = initial_spread_index(
            ffmc=today.fine_fuel_moisture_code, ws=today.wind_speed
        )
    if today.duff_moisture_code is not None and today.drought_code is not None:
        today.build_up_index = buildup_index(dmc=today.duff_moisture_code, dc=today.drought_code)
    if today.initial_spread_index is not None and today.build_up_index is not None:
        today.fire_weather_index = fire_weather_index(
            isi=today.initial_spread_index, bui=today.build_up_index
        )

    return today


def transform_morecastforecastoutput_to_weatherindeterminate(
    forecast_outputs: List[MoreCastForecastOutput], wfwx_stations: List[WFWXWeatherStation]
) -> List[WeatherIndeterminate]:
    """Helper function to convert list of MoreCastForecastOutput objects (taken from our database)
    into list of WeatherIndeterminate objects to match the structure of the forecasts pulled from WFWX.
    wfwx_stations list (station data from WFWX) is used to populate station_name data.
    """
    weather_indeterminates: List[WeatherIndeterminate] = []
    for output in forecast_outputs:
        station = next((s for s in wfwx_stations if s.code == output.station_code), None)

        weather_indeterminates.append(
            WeatherIndeterminate(
                station_code=output.station_code,
                station_name=station.name if station else "",
                utc_timestamp=output.for_date,
                determinate=WeatherDeterminate.FORECAST,
                temperature=output.temp,
                relative_humidity=output.rh,
                precipitation=output.precip,
                wind_direction=output.wind_direction,
                wind_speed=output.wind_speed,
            )
        )
    return weather_indeterminates
