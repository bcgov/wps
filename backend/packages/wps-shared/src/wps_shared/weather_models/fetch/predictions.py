"""Code for fetching data for API."""

import datetime
import logging
from collections import defaultdict
from datetime import time
from time import perf_counter
from typing import List

from sqlalchemy.orm import Session

from wps_shared.db.crud.weather_models import get_latest_station_prediction
from wps_shared.schemas.morecast_v2 import WeatherIndeterminate
from wps_shared.schemas.stations import WeatherStation
from wps_shared.utils.time import get_days_from_range, vancouver_tz

logger = logging.getLogger(__name__)


def fetch_latest_model_run_predictions_by_station_code_and_date_range(
    session: Session,
    all_stations: List[WeatherStation],
    start_time: datetime.datetime,
    end_time: datetime.datetime,
) -> List[WeatherIndeterminate]:
    cffdrs_start = perf_counter()
    results: List[WeatherIndeterminate] = []
    days = get_days_from_range(start_time, end_time)
    stations = {station.code: station for station in all_stations}
    active_station_codes = stations.keys()
    for day in days:
        day_start = datetime.datetime.combine(day, time.min, tzinfo=vancouver_tz)
        day_end = datetime.datetime.combine(day, time.max, tzinfo=vancouver_tz)

        daily_result = get_latest_station_prediction(
            session, active_station_codes, day_start, day_end
        )
        for (
            timestamp,
            model_abbrev,
            prediction_run_timestamp,
            station_code,
            rh,
            temp,
            bias_adjusted_temp,
            bias_adjusted_rh,
            bias_adjusted_wind_speed,
            bias_adjusted_wdir,
            precip_24hours,
            bias_adjusted_precip_24h,
            wind_dir,
            wind_speed,
        ) in daily_result:
            # Create two WeatherIndeterminates, one for model predictions and one for bias corrected predictions
            results.append(
                WeatherIndeterminate(
                    station_code=station_code,
                    station_name=stations[station_code].name,
                    determinate=model_abbrev,
                    utc_timestamp=timestamp,
                    temperature=temp,
                    relative_humidity=rh,
                    precipitation=precip_24hours,
                    wind_direction=wind_dir,
                    wind_speed=wind_speed,
                    prediction_run_timestamp=prediction_run_timestamp,
                )
            )
            results.append(
                WeatherIndeterminate(
                    station_code=station_code,
                    station_name=stations[station_code].name,
                    determinate=f"{model_abbrev}_BIAS",
                    utc_timestamp=timestamp,
                    temperature=bias_adjusted_temp,
                    relative_humidity=bias_adjusted_rh,
                    precipitation=bias_adjusted_precip_24h,
                    wind_speed=bias_adjusted_wind_speed,
                    wind_direction=bias_adjusted_wdir,
                    prediction_run_timestamp=prediction_run_timestamp,
                )
            )
    post_processed_results = post_process_fetched_predictions(results)
    cffdrs_end = perf_counter()
    delta = cffdrs_end - cffdrs_start
    # Any delta below 100 milliseconds is just noise in the logs.
    if delta > 0.1:
        logger.info("%f delta count before and after latest prediction model query", delta)
    return post_processed_results


def post_process_fetched_predictions(weather_indeterminates: List[WeatherIndeterminate]):
    results: List[WeatherIndeterminate] = []
    grouped_data = defaultdict(list)

    for weather_indeterminate in weather_indeterminates:
        key = f"${weather_indeterminate.station_code}-${str(weather_indeterminate.determinate)}-${weather_indeterminate.utc_timestamp.date()}"
        grouped_data[key].append(weather_indeterminate)

    for key, station_indeterminates in grouped_data.items():
        # max keeps the first match, and the query orders model runs newest first
        latest_for_station = max(station_indeterminates, key=lambda x: x.utc_timestamp)
        results.append(latest_for_station)

    return results
