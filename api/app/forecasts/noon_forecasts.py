""" This module is used to fetch noon forecasts for weather stations from
the noon_forecasts table in our database.
"""
import logging
from collections import defaultdict
from typing import List
from datetime import datetime, timezone
import math
from wps_shared.schemas.forecasts import NoonForecast, NoonForecastResponse, NoonForecastValue
from wps_shared.schemas.stations import StationCodeList
import wps_shared.db.database
from wps_shared.db.crud.forecasts import query_noon_forecast_records
import wps_shared.db.models


logger = logging.getLogger(__name__)


class StationNotFoundException(Exception):
    """ Custom exception for when a station cannot be found """


def parse_table_records_to_noon_forecast_response(data: List[wps_shared.db.models.forecasts.NoonForecast]):
    """ Given a list of table records from the database, parse each record
    (which is a NoonForecast object) and structure it as a NoonForecast
    object, then return the list of NoonForecast objects as a NoonForecastResponse
    """
    noon_forecasts = defaultdict(list)
    for record in data:
        # NOTE: have to fill NaN values with None for FE compatibility
        station_code = record.station_code
        noon_forecast_value = NoonForecastValue(
            datetime=datetime(
                year=record.weather_date.year,
                month=record.weather_date.month,
                day=record.weather_date.day,
                hour=record.weather_date.hour,
                tzinfo=timezone.utc).isoformat(),
            temp_valid=record.temp_valid,
            temperature=None if math.isnan(record.temperature) else record.temperature,
            rh_valid=record.rh_valid,
            relative_humidity=None if math.isnan(record.relative_humidity) else record.relative_humidity,
            wdir_valid=record.wdir_valid,
            wind_direction=None if math.isnan(
                record.wind_direction) else record.wind_direction,
            wspeed_valid=record.wspeed_valid,
            wind_speed=record.wind_speed,
            precip_valid=record.precip_valid,
            total_precipitation=record.precipitation,
            gc=None if math.isnan(record.gc) else record.gc,
            ffmc=None if math.isnan(record.ffmc) else record.ffmc,
            dmc=None if math.isnan(record.dmc) else record.dmc,
            dc=None if math.isnan(record.dc) else record.dc,
            isi=None if math.isnan(record.isi) else record.isi,
            bui=None if math.isnan(record.bui) else record.bui,
            fwi=None if math.isnan(record.fwi) else record.fwi,
            danger_rating=None,
            created_at=record.created_at
        )
        noon_forecasts[station_code].append(noon_forecast_value)

    values = []
    for key, value in noon_forecasts.items():
        noon_forecast = NoonForecast(
            station_code=key,
            values=value
        )
        values.append(noon_forecast)
    return NoonForecastResponse(noon_forecasts=values)


def fetch_noon_forecasts(stations: StationCodeList,
                         start_date: datetime,
                         end_date: datetime) -> NoonForecastResponse:
    """ Query all noon forecasts between start_date and end_date for the specified weather station. Note that
    there may be multiple records for the same weather station and same weather_date, as noon forecasts
    are updated twice daily. """
    logger.debug('Querying noon forecasts for stations %s from %s to %s',
                 stations, start_date, end_date)
    with wps_shared.db.database.get_read_session_scope() as session:
        forecasts = query_noon_forecast_records(
            session, stations, start_date, end_date)

    return parse_table_records_to_noon_forecast_response(forecasts)
