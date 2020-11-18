""" This module is used to fetch noon forecasts summaries with minimum and maximum values for each day """

import json
import logging
from collections import defaultdict
from datetime import datetime
import app.stations
import app.db.database
from app.db.crud.forecasts import query_noon_forecast_records
from app.schemas import (
    NoonForecastSummariesResponse,
    NoonForecastSummary, NoonForecastSummaryValues
)
from app.schemas.stations import WeatherStation, StationCodeList

LOGGER = logging.getLogger(__name__)


def create_noon_forecast_summary(station: WeatherStation,
                                 records_by_station: dict
                                 ) -> NoonForecastSummary:
    """ Returns NoonForecastSummary with min and max for each day """
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
        min_max_values = NoonForecastSummaryValues(
            datetime=date,
            tmp_min=min(nested_dict[date]['temp']),
            tmp_max=max(nested_dict[date]['temp']),
            rh_min=min(nested_dict[date]['rh']),
            rh_max=max(nested_dict[date]['rh']),
        )
        summary.values.append(min_max_values)

    return summary


async def fetch_noon_forecasts_summaries(station_codes: StationCodeList,
                                         start_date: datetime,
                                         end_date: datetime
                                         ) -> NoonForecastSummariesResponse:
    """ Fetch noon forecasts from the database and parse them,
    then calculate min&max and put them in NoonForecastSummariesResponse """
    session = app.db.database.get_read_session()
    records = query_noon_forecast_records(
        session, station_codes, start_date, end_date)

    records_by_station = defaultdict(list)
    for record in records:
        code = record.station_code
        records_by_station[code].append(record)

    response = NoonForecastSummariesResponse()
    stations = await app.stations.get_stations_by_codes(station_codes)
    for station in stations:
        summary = create_noon_forecast_summary(station, records_by_station)
        response.summaries.append(summary)

    return response
