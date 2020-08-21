""" This module is used to fetch noon forecasts in percentiles for each day """

import json
import logging
from collections import defaultdict
from datetime import datetime
from numpy import percentile
from sqlalchemy import desc
from app.wildfire_one import get_stations_by_codes
from app.db.models import NoonForecasts
import app.db.database
from app.schemas import (
    StationCodeList, NoonForecastSummariesResponse,
    NoonForecastSummary, NoonForecastSummaryValues, WeatherStation
)

LOGGER = logging.getLogger(__name__)


def query_noon_forecast_records(station_codes: StationCodeList,
                                start_date: datetime,
                                end_date: datetime
                                ):
    """ Sends a query to get noon forecast records """
    session = app.db.database.get_session()
    return session.query(NoonForecasts)\
        .filter(NoonForecasts.station_code.in_(station_codes))\
        .filter(NoonForecasts.weather_date >= start_date)\
        .filter(NoonForecasts.weather_date <= end_date)\
        .order_by(NoonForecasts.weather_date)\
        .order_by(desc(NoonForecasts.created_at))


def create_noon_forecast_summary(station: WeatherStation,
                                 records_by_station: dict
                                 ) -> NoonForecastSummary:
    """ Returns NoonForecastSummary with percentiles for each day """
    summary = NoonForecastSummary(station=station)

    records_for_one_station = records_by_station[station.code]

    # Dict[str, Dict[str, List[int]]]
    # e.g. { "2020-08-16T20:00:00+00:00": { "temp": [27.0, 26.0], "rh": [40.0, 41.0] } }
    nested_dict = defaultdict(lambda: defaultdict(list))

    for record in records_for_one_station:
        date = record.weather_date.isoformat()
        nested_dict[date]['temp'].append(record.temperature)
        nested_dict[date]['rh'].append(record.relative_humidity)

    LOGGER.debug(json.dumps(nested_dict, sort_keys=True, indent=4))

    for date in nested_dict:
        percentile_values = NoonForecastSummaryValues(
            datetime=date,
            tmp_5th=percentile(nested_dict[date]['temp'], 5),
            tmp_median=percentile(nested_dict[date]['temp'], 50),
            tmp_90th=percentile(nested_dict[date]['temp'], 90),
            rh_5th=percentile(nested_dict[date]['rh'], 5),
            rh_median=percentile(nested_dict[date]['rh'], 50),
            rh_90th=percentile(nested_dict[date]['rh'], 90),
        )
        summary.values.append(percentile_values)

    return summary


async def fetch_noon_forecast_summaries(station_codes: StationCodeList,
                                        start_date: datetime,
                                        end_date: datetime
                                        ) -> NoonForecastSummariesResponse:
    """ Fetch noon forecasts from the database and parse them,
    then calculate percentiles and put them in NoonForecastSummariesResponse """
    records = query_noon_forecast_records(station_codes, start_date, end_date)

    records_by_station = defaultdict(list)
    for record in records:
        code = record.station_code
        records_by_station[code].append(record)

    response = NoonForecastSummariesResponse()
    stations = await get_stations_by_codes(station_codes)
    for station in stations:
        summary = create_noon_forecast_summary(station, records_by_station)
        response.summaries.append(summary)

    return response
