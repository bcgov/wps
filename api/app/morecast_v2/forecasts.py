
from datetime import datetime, time, timedelta
from urllib.parse import urljoin
from app import config

from aiohttp import ClientSession
from collections import defaultdict

from app.utils.time import vancouver_tz
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.crud.morecast_v2 import get_forecasts_in_range
from app.db.models.morecast_v2 import MorecastForecastRecord
from app.schemas.morecast_v2 import MoreCastForecastOutput, StationDailyFromWF1, WF1ForecastRecordType, WF1PostForecast, WeatherIndeterminate, WeatherDeterminate
from app.wildfire_one.schema_parsers import WFWXWeatherStation
from app.wildfire_one.wfwx_api import get_auth_header, get_forecasts_for_stations_by_date_range, get_wfwx_stations_from_station_codes
from app.fire_behaviour import cffdrs


def get_forecasts(db_session: Session, start_time: datetime, end_time: datetime, station_codes: List[int]) -> List[MoreCastForecastOutput]:
    result = get_forecasts_in_range(db_session, start_time, end_time, station_codes)

    forecasts: List[WeatherIndeterminate] = [MoreCastForecastOutput(station_code=forecast.station_code,
                                                                    for_date=forecast.for_date.timestamp() * 1000,
                                                                    temp=forecast.temp,
                                                                    rh=forecast.rh,
                                                                    precip=forecast.precip,
                                                                    wind_speed=forecast.wind_speed,
                                                                    wind_direction=forecast.wind_direction,
                                                                    update_timestamp=int(forecast.update_timestamp.timestamp())) for forecast in result]
    return forecasts


def construct_wf1_forecast(forecast: MorecastForecastRecord, stations: List[WFWXWeatherStation], forecast_id: Optional[str], created_by: Optional[str]) -> WF1PostForecast:
    station = next(filter(lambda obj: obj.code == forecast.station_code, stations))
    station_id = station.wfwx_id
    station_url = urljoin(config.get('WFWX_BASE_URL'), f'wfwx-fireweather-api/v1/stations/{station_id}')
    wf1_post_forecast = WF1PostForecast(createdBy=created_by,
                                        id=forecast_id,
                                        stationId=station_id,
                                        station=station_url,
                                        temperature=forecast.temp,
                                        relativeHumidity=forecast.rh,
                                        precipitation=forecast.precip,
                                        windSpeed=forecast.wind_speed,
                                        windDirection=forecast.wind_direction,
                                        weatherTimestamp=datetime.timestamp(forecast.for_date) * 1000,
                                        recordType=WF1ForecastRecordType())
    return wf1_post_forecast


async def construct_wf1_forecasts(session: ClientSession, forecast_records: List[MorecastForecastRecord], stations: List[WFWXWeatherStation]) -> List[WF1PostForecast]:
    # Fetch existing forecasts from WF1 for the stations and date range in the forecast records
    header = await get_auth_header(session)
    forecast_dates = [f.for_date for f in forecast_records]
    min_forecast_date = min(forecast_dates)
    max_forecast_date = max(forecast_dates)
    start_time = vancouver_tz.localize(datetime.combine(min_forecast_date, time.min))
    end_time = vancouver_tz.localize(datetime.combine(max_forecast_date, time.max))
    unique_station_codes = list(set([f.station_code for f in forecast_records]))
    dailies = await get_forecasts_for_stations_by_date_range(session, header, start_time,
                                                             end_time, unique_station_codes)

    # Shape the WF1 dailies into a dictionary keyed by station codes for easier consumption
    grouped_dailies = defaultdict(list[StationDailyFromWF1])
    for daily in dailies:
        grouped_dailies[daily.station_code].append(daily)

    # iterate through the MoreCast2 forecast records and create WF1PostForecast objects
    wf1_forecasts = []
    for forecast in forecast_records:
        # Check if an existing daily was retrieved from WF1 and use id and createdBy attributes if present
        observed_daily = next(
            (daily for daily in grouped_dailies[forecast.station_code] if daily.utcTimestamp == forecast.for_date), None)
        forecast_id = observed_daily.forecast_id if observed_daily is not None else None
        created_by = observed_daily.created_by if observed_daily is not None else None
        wf1_forecasts.append(construct_wf1_forecast(forecast, stations, forecast_id, created_by))
    return wf1_forecasts


async def format_as_wf1_post_forecasts(session: ClientSession, forecast_records: List[MorecastForecastRecord]) -> List[WF1PostForecast]:
    """ Returns list of forecast records re-formatted in the data structure WF1 API expects """
    header = await get_auth_header(session)
    station_codes = [record.station_code for record in forecast_records]
    stations = await get_wfwx_stations_from_station_codes(session, header, station_codes)
    unique_stations = list(set(stations))
    wf1_post_forecasts = await construct_wf1_forecasts(session, forecast_records, unique_stations)
    return wf1_post_forecasts


def actual_exists(forecast: WeatherIndeterminate, actuals: List[WeatherIndeterminate]):
    """ Returns True if the actuals contain a WeatherIndeterminate with station_code and utc_timestamp that
    matches those of the forecast; otherwise, returns False."""
    station_code_matches = [actual for actual in actuals if actual.station_code ==
                            forecast.station_code]
    utc_timestamp_matches = [station_code_match for station_code_match in station_code_matches
                             if station_code_match.utc_timestamp == forecast.utc_timestamp]
    return len(utc_timestamp_matches) > 0


def filter_for_api_forecasts(forecasts: List[WeatherIndeterminate], actuals: List[WeatherIndeterminate]):
    """ Returns a list of forecasts where each forecast has a corresponding WeatherIndeterminate in the
    actuals with a matching station_code and utc_timestamp."""
    filtered_forecasts = []
    for forecast in forecasts:
        if actual_exists(forecast, actuals):
            filtered_forecasts.append(forecast)
    return filtered_forecasts


def get_fwi_values(actuals: List[WeatherIndeterminate], forecasts: List[WeatherIndeterminate]) -> Tuple[List[WeatherIndeterminate], List[WeatherIndeterminate]]:
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
        indeterminates_dict[indeterminate.station_code][indeterminate.utc_timestamp.date()] = indeterminate

    for idx, indeterminate in enumerate(all_indeterminates):
        last_indeterminate = indeterminates_dict[indeterminate.station_code].get(
            indeterminate.utc_timestamp.date() - timedelta(days=1), None)
        if last_indeterminate:
            updated_forecast = calculate_fwi_values(last_indeterminate, indeterminate)
            all_indeterminates[idx] = updated_forecast

    forecasts = [indeterminate for indeterminate in all_indeterminates if indeterminate.determinate ==
                 WeatherDeterminate.FORECAST]
    actuals = [indeterminate for indeterminate in all_indeterminates if indeterminate.determinate == WeatherDeterminate.ACTUAL]

    return actuals, forecasts


def calculate_fwi_values(yesterday: WeatherIndeterminate, today: WeatherIndeterminate) -> WeatherIndeterminate:
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
    month_to_calculate_for = int(today.utc_timestamp.strftime('%m'))
    latitude = today.latitude
    temp = today.temperature
    rh = today.relative_humidity
    precip = today.precipitation
    wind_spd = today.wind_speed

    if yesterday.fine_fuel_moisture_code:
        today.fine_fuel_moisture_code = cffdrs.fine_fuel_moisture_code(ffmc=yesterday.fine_fuel_moisture_code,
                                                                       temperature=temp,
                                                                       relative_humidity=rh,
                                                                       precipitation=precip,
                                                                       wind_speed=wind_spd)
    if yesterday.duff_moisture_code:
        today.duff_moisture_code = cffdrs.duff_moisture_code(dmc=yesterday.duff_moisture_code,
                                                             temperature=temp,
                                                             relative_humidity=rh,
                                                             precipitation=precip,
                                                             latitude=latitude,
                                                             month=month_to_calculate_for,
                                                             latitude_adjust=True
                                                             )
    if yesterday.drought_code:
        today.drought_code = cffdrs.drought_code(dc=yesterday.drought_code,
                                                 temperature=temp,
                                                 relative_humidity=rh,
                                                 precipitation=precip,
                                                 latitude=latitude,
                                                 month=month_to_calculate_for,
                                                 latitude_adjust=True
                                                 )
    if today.fine_fuel_moisture_code:
        today.initial_spread_index = cffdrs.initial_spread_index(ffmc=today.fine_fuel_moisture_code,
                                                                 wind_speed=today.wind_speed)
    if today.duff_moisture_code and today.drought_code:
        today.build_up_index = cffdrs.bui_calc(dmc=today.duff_moisture_code, dc=today.drought_code)
    if today.initial_spread_index and today.build_up_index:
        today.fire_weather_index = cffdrs.fire_weather_index(isi=today.initial_spread_index, bui=today.build_up_index)

    return today
