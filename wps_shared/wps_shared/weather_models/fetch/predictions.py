"""Code for fetching data for API."""

from itertools import groupby
import logging
from typing import List
import datetime
from datetime import time
from time import perf_counter
from collections import defaultdict
import pytz
from sqlalchemy.orm import Session
import wps_shared.db.database
from wps_shared.schemas.morecast_v2 import WeatherIndeterminate
from wps_shared.schemas.weather_models import WeatherStationModelPredictionValues, WeatherModelPredictionValues, WeatherModelRun, ModelRunPredictions, WeatherStationModelRunsPredictions
from wps_shared.db.models.weather_models import WeatherStationModelPrediction
from wps_shared.db.crud.weather_models import (
    get_latest_station_model_prediction_per_day,
    get_station_model_predictions,
    get_station_model_prediction_from_previous_model_run,
    get_latest_station_prediction,
)
import wps_shared.stations
from wps_shared.utils.time import get_days_from_range
from wps_shared.weather_models import ModelEnum

logger = logging.getLogger(__name__)


class MatchingStationNotFoundException(Exception):
    """Exception raised when station cannot be found."""


def _fetch_delta_precip_for_prev_model_run(
    session: Session, model: ModelEnum, prediction: WeatherStationModelPrediction, prev_station_predictions: dict, prediction_model_run_timestamp: datetime.datetime
):
    # Look if we can find the previous value in memory
    if prediction.prediction_timestamp in prev_station_predictions[prediction.station_code]:
        prev_station_prediction = prev_station_predictions[prediction.station_code]
        return prev_station_prediction[prediction.prediction_timestamp]["prediction"].delta_precipitation
    # Uh oh - couldn't find it - let's go look in the database.
    # This should only happen in extreme edge cases!
    prev_prediction = get_station_model_prediction_from_previous_model_run(session, prediction.station_code, model, prediction.prediction_timestamp, prediction_model_run_timestamp)
    if prev_prediction:
        return prev_prediction.delta_precip
    return None


async def fetch_model_run_predictions_by_station_code(model: ModelEnum, station_codes: List[int], time_of_interest: datetime) -> List[WeatherStationModelRunsPredictions]:
    """Fetch model predictions from database based on list of station codes, for a specified datetime.
    Predictions are grouped by station and model run.
    """
    # We're interested in the 5 days prior to and 10 days following the time_of_interest.
    start_date = time_of_interest - datetime.timedelta(days=5)
    end_date = time_of_interest + datetime.timedelta(days=10)
    return await fetch_model_run_predictions_by_station_code_and_date_range(model, station_codes, start_date, end_date)


async def fetch_model_run_predictions_by_station_code_and_date_range(
    model: ModelEnum, station_codes: List[int], start_time: datetime.datetime, end_time: datetime.datetime
) -> List[WeatherStationModelRunsPredictions]:
    """Fetch model predictions from database based on list of station codes and date range.
    Predictions are grouped by station and model run.
    """
    # send the query (ordered by prediction date.)
    with wps_shared.db.database.get_read_session_scope() as session:
        historic_predictions = get_station_model_predictions(session, station_codes, model, start_time, end_time)

        return await marshall_predictions(session, model, station_codes, historic_predictions)


async def fetch_latest_daily_model_run_predictions_by_station_code_and_date_range(
    model: ModelEnum, station_codes: List[int], start_time: datetime.datetime, end_time: datetime.datetime
) -> List[WeatherStationModelRunsPredictions]:
    results = []
    days = get_days_from_range(start_time, end_time)
    stations = {station.code: station for station in await wps_shared.stations.get_stations_by_codes(station_codes)}

    with wps_shared.db.database.get_read_session_scope() as session:
        for day in days:
            day_results = []
            vancouver_tz = pytz.timezone("America/Vancouver")

            day_start = vancouver_tz.localize(datetime.datetime.combine(day, time.min))
            day_end = vancouver_tz.localize(datetime.datetime.combine(day, time.max))

            daily_result = get_latest_station_model_prediction_per_day(session, station_codes, model, day_start, day_end)
            for id, timestamp, model_abbrev, station_code, rh, temp, bias_adjusted_temp, bias_adjusted_rh, precip_24hours, wind_dir, wind_speed, update_date in daily_result:
                day_results.append(
                    WeatherStationModelPredictionValues(
                        id=str(id),
                        abbreviation=model_abbrev,
                        station=stations[station_code],
                        temperature=temp,
                        bias_adjusted_temperature=bias_adjusted_temp,
                        relative_humidity=rh,
                        bias_adjusted_relative_humidity=bias_adjusted_rh,
                        precip_24hours=precip_24hours,
                        wind_speed=wind_speed,
                        wind_direction=wind_dir,
                        datetime=timestamp,
                        update_date=update_date,
                    )
                )
            # sort the list by station_code
            day_results.sort(key=lambda x: x.station.code)

            # group the list by station_code
            groups = groupby(day_results, key=lambda x: x.station.code)
            for station_code, station_predictions in groups:
                prediction_list = list(station_predictions)
                latest_for_station = max(prediction_list, key=lambda x: x.update_date)
                results.append(latest_for_station)
        return results


async def fetch_latest_model_run_predictions_by_station_code_and_date_range(
    session: Session, station_codes: List[int], start_time: datetime.datetime, end_time: datetime.datetime
) -> List[WeatherIndeterminate]:
    cffdrs_start = perf_counter()
    results: List[WeatherIndeterminate] = []
    days = get_days_from_range(start_time, end_time)
    stations = {station.code: station for station in await wps_shared.stations.get_stations_by_codes(station_codes)}
    active_station_codes = stations.keys()
    for day in days:
        vancouver_tz = pytz.timezone("America/Vancouver")

        day_start = vancouver_tz.localize(datetime.datetime.combine(day, time.min))
        day_end = vancouver_tz.localize(datetime.datetime.combine(day, time.max))

        daily_result = get_latest_station_prediction(session, active_station_codes, day_start, day_end)
        for (
            timestamp,
            model_abbrev,
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
            if model_abbrev == ModelEnum.ECMWF.value:
                continue
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
        latest_for_station = max(station_indeterminates, key=lambda x: x.utc_timestamp)
        results.append(latest_for_station)

    return results


async def marshall_predictions(session: Session, model: ModelEnum, station_codes: List[int], query):
    station_predictions = defaultdict(dict)

    for prediction, prediction_model_run_timestamp, prediction_model in query:
        # If this is true, it means that we are at hour 000 of the model run but not at the 0th hour of the
        # day, so we need to look at the accumulated precip from the previous model run to calculate the
        # delta_precip
        precip_value = None
        if prediction.prediction_timestamp == prediction_model_run_timestamp.prediction_run_timestamp and prediction.prediction_timestamp.hour > 0:
            precip_value = _fetch_delta_precip_for_prev_model_run(session, model, prediction, station_predictions, prediction_model_run_timestamp.prediction_run_timestamp)
        # This condition catches situations where we are not at hour 000 of the model run, or where it is
        # hour 000 but there was nothing returned from _fetch_delta_precip_for_prev_model_run()
        if precip_value is None:
            precip_value = prediction.delta_precip
        station_predictions[prediction.station_code][prediction.prediction_timestamp] = {
            "model_run": WeatherModelRun(
                datetime=prediction_model_run_timestamp.prediction_run_timestamp, name=prediction_model.name, abbreviation=model, projection=prediction_model.projection
            ),
            "prediction": WeatherModelPredictionValues(
                temperature=prediction.tmp_tgl_2,
                bias_adjusted_temperature=prediction.bias_adjusted_temperature,
                relative_humidity=prediction.rh_tgl_2,
                bias_adjusted_relative_humidity=prediction.bias_adjusted_rh,
                delta_precipitation=precip_value,
                wind_speed=prediction.wind_tgl_10,
                wind_direction=prediction.wdir_tgl_10,
                datetime=prediction.prediction_timestamp,
            ),
        }

    # Re-structure the data, grouping data by station and model run.
    # NOTE: It means looping through twice, but the code reads easier this way.
    stations = {station.code: station for station in await wps_shared.stations.get_stations_by_codes(station_codes)}
    response = []
    for station_code, predictions in station_predictions.items():
        model_run_dict = {}
        for prediction in predictions.values():
            if prediction["model_run"].datetime in model_run_dict:
                model_run_predictions = model_run_dict[prediction["model_run"].datetime]
            else:
                model_run_predictions = ModelRunPredictions(model_run=prediction["model_run"], values=[])
                model_run_dict[prediction["model_run"].datetime] = model_run_predictions
            model_run_predictions.values.append(prediction["prediction"])

        response.append(WeatherStationModelRunsPredictions(station=stations[station_code], model_runs=list(model_run_dict.values())))
    return response
