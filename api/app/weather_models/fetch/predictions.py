""" Code for fetching data for API.
"""

import logging
from typing import List
import datetime
from collections import defaultdict
from sqlalchemy.orm import Session
import app.db.database
from app.schemas.weather_models import (WeatherStationModelPredictionValues, WeatherModelPredictionValues, WeatherModelRun,
                                        ModelRunPredictions,
                                        WeatherStationModelRunsPredictions)
from app.db.models.weather_models import WeatherStationModelPrediction
from app.db.crud.weather_models import (get_latest_station_model_prediction_per_day, get_station_model_predictions,
                                        get_station_model_prediction_from_previous_model_run)
import app.stations
from app.weather_models import ModelEnum

logger = logging.getLogger(__name__)


class MatchingStationNotFoundException(Exception):
    """ Exception raised when station cannot be found. """


def _fetch_delta_precip_for_prev_model_run(
        session: Session,
        model: ModelEnum,
        prediction: WeatherStationModelPrediction,
        prev_station_predictions: dict,
        prediction_model_run_timestamp: datetime.datetime):
    # Look if we can find the previous value in memory
    if prediction.prediction_timestamp in prev_station_predictions[prediction.station_code]:
        prev_station_prediction = prev_station_predictions[prediction.station_code]
        return prev_station_prediction[prediction.prediction_timestamp]['prediction'].delta_precipitation
    # Uh oh - couldn't find it - let's go look in the database.
    # This should only happen in extreme edge cases!
    prev_prediction = get_station_model_prediction_from_previous_model_run(
        session, prediction.station_code, model, prediction.prediction_timestamp,
        prediction_model_run_timestamp)
    if prev_prediction:
        return prev_prediction.delta_precip
    return None


async def fetch_model_run_predictions_by_station_code(
        model: ModelEnum,
        station_codes: List[int],
        time_of_interest: datetime) -> List[WeatherStationModelRunsPredictions]:
    """ Fetch model predictions from database based on list of station codes, for a specified datetime.
    Predictions are grouped by station and model run.
    """
    # We're interested in the 5 days prior to and 10 days following the time_of_interest.
    start_date = time_of_interest - datetime.timedelta(days=5)
    end_date = time_of_interest + datetime.timedelta(days=10)
    return await fetch_model_run_predictions_by_station_code_and_date_range(model, station_codes, start_date, end_date)


async def fetch_model_run_predictions_by_station_code_and_date_range(
        model: ModelEnum,
        station_codes: List[int],
        start_time: datetime.datetime,
        end_time: datetime.datetime) -> List[WeatherStationModelRunsPredictions]:
    """ Fetch model predictions from database based on list of station codes and date range.
    Predictions are grouped by station and model run.
    """
    # send the query (ordered by prediction date.)
    with app.db.database.get_read_session_scope() as session:
        historic_predictions = get_station_model_predictions(
            session, station_codes, model, start_time, end_time)

        return await marshall_predictions(session, model, station_codes, historic_predictions)


async def fetch_latest_daily_model_run_predictions_by_station_code_and_date_range(
        model: ModelEnum,
        station_codes: List[int],
        start_time: datetime.datetime,
        end_time: datetime.datetime) -> List[WeatherStationModelRunsPredictions]:
    """ Fetch the latest model prediction for each day from database based on
        list of station codes and date range. Predictions are grouped by station and model run.
    """
    latest_predictions: List[WeatherStationModelPredictionValues] = []

    stations = {station.code: station for station in await app.stations.get_stations_by_codes(station_codes)}

    with app.db.database.get_read_session_scope() as session:
        latest_prediction_per_day = get_latest_station_model_prediction_per_day(
            session, station_codes, model, start_time, end_time)

        for id, timestamp, station_code, rh, temp, bias_adjusted_temp, bias_adjusted_rh, delta_precip, wind_dir, wind_speed, run_timestamp, _ in latest_prediction_per_day:
            latest_predictions.append(
                WeatherStationModelPredictionValues(
                    id=str(id),
                    abbreviation=model.value,
                    station=stations[station_code],
                    temperature=temp,
                    bias_adjusted_temperature=bias_adjusted_temp,
                    relative_humidity=rh,
                    bias_adjusted_relative_humidity=bias_adjusted_rh,
                    delta_precipitation=delta_precip,
                    wind_speed=wind_speed,
                    wind_direction=wind_dir,
                    datetime=timestamp,
                    run_timestamp=run_timestamp
                ))

        return latest_predictions


async def marshall_predictions(session: Session, model: ModelEnum, station_codes: List[int], query):
    station_predictions = defaultdict(dict)

    for prediction, prediction_model_run_timestamp, prediction_model in query:
        # If this is true, it means that we are at hour 000 of the model run but not at the 0th hour of the
        # day, so we need to look at the accumulated precip from the previous model run to calculate the
        # delta_precip
        precip_value = None
        if prediction.prediction_timestamp == prediction_model_run_timestamp.prediction_run_timestamp and \
                prediction.prediction_timestamp.hour > 0:
            precip_value = _fetch_delta_precip_for_prev_model_run(
                session,
                model,
                prediction,
                station_predictions,
                prediction_model_run_timestamp.prediction_run_timestamp)
        # This condition catches situations where we are not at hour 000 of the model run, or where it is
        # hour 000 but there was nothing returned from _fetch_delta_precip_for_prev_model_run()
        if precip_value is None:
            precip_value = prediction.delta_precip
        station_predictions[prediction.station_code][prediction.prediction_timestamp] = {
            'model_run': WeatherModelRun(
                datetime=prediction_model_run_timestamp.prediction_run_timestamp,
                name=prediction_model.name,
                abbreviation=model,
                projection=prediction_model.projection
            ),
            'prediction': WeatherModelPredictionValues(
                temperature=prediction.tmp_tgl_2,
                bias_adjusted_temperature=prediction.bias_adjusted_temperature,
                relative_humidity=prediction.rh_tgl_2,
                bias_adjusted_relative_humidity=prediction.bias_adjusted_rh,
                delta_precipitation=precip_value,
                wind_speed=prediction.wind_tgl_10,
                wind_direction=prediction.wdir_tgl_10,
                datetime=prediction.prediction_timestamp
            )
        }

    # Re-structure the data, grouping data by station and model run.
    # NOTE: It means looping through twice, but the code reads easier this way.
    stations = {station.code: station for station in await app.stations.get_stations_by_codes(station_codes)}
    response = []
    for station_code, predictions in station_predictions.items():
        model_run_dict = {}
        for prediction in predictions.values():

            if prediction['model_run'].datetime in model_run_dict:
                model_run_predictions = model_run_dict[prediction['model_run'].datetime]
            else:
                model_run_predictions = ModelRunPredictions(
                    model_run=prediction['model_run'],
                    values=[]
                )
                model_run_dict[prediction['model_run'].datetime] = model_run_predictions
            model_run_predictions.values.append(prediction['prediction'])

        response.append(WeatherStationModelRunsPredictions(
            station=stations[station_code],
            model_runs=list(model_run_dict.values())
        ))
    return response
