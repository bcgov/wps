import asyncio
import logging
from datetime import datetime, time, timedelta, timezone
from typing import Dict, List, Tuple

from aiohttp import ClientSession
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.crud.fire_watch import get_all_active_fire_watches, get_all_prescription_status
from wps_shared.db.crud.weather_models import get_latest_model_prediction_for_stations
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.fire_watch import FireWatch, FireWatchWeather
from wps_shared.fuel_types import FUEL_TYPE_DEFAULTS
from wps_shared.schemas.morecast_v2 import WeatherDeterminate, WeatherIndeterminate
from wps_shared.schemas.weather_models import ModelPredictionDetails
from wps_shared.utils.time import get_utc_now
from wps_shared.weather_models import ModelEnum
from wps_shared.wildfire_one.schema_parsers import WFWXWeatherStation
from wps_shared.wildfire_one.wfwx_api import get_auth_header, get_daily_determinates_for_stations_and_date, get_wfwx_stations_from_station_codes
from wps_shared.wps_logging import configure_logging

from app.fire_behaviour.cffdrs import CFFDRSException
from app.fire_behaviour.prediction import FireBehaviourPrediction, FireBehaviourPredictionInputError, calculate_fire_behaviour_prediction
from app.morecast_v2.forecasts import calculate_fwi_from_seed_indeterminates

logger = logging.getLogger(__name__)

FIREWATCH_WEATHER_MODEL = ModelEnum.GFS


async def gather_fire_watch_inputs(
    session: AsyncSession,
    fire_watch: FireWatch,
    start_date: datetime,
    end_date: datetime,
) -> Tuple[List[ModelPredictionDetails], List[WeatherIndeterminate]]:
    """
    Gather all the inputs required for processing a FireWatch.
    """

    # fetch weather model predictions
    predictions = await get_latest_model_prediction_for_stations(session, [fire_watch.station_code], FIREWATCH_WEATHER_MODEL, start_date, end_date)

    # fetch actual weather data. Using this method as it may make it easier to pull in forecasts if we want to.
    actual_weather_data, _ = await fetch_actuals_and_forecasts(start_date - timedelta(days=1), end_date, [fire_watch.station_code])
    actual_weather_data = actual_weather_data[:1]

    return predictions, actual_weather_data


def map_to_fire_watch_weather(
    fire_watch: FireWatch,
    prediction: WeatherIndeterminate,
    fbp_result: FireBehaviourPrediction,
    prediction_model_run_timestamp_id: int,
) -> FireWatchWeather:
    """
    Map a WeatherIndeterminate and FBP result to a FireWatchWeather object.

    :param fire_watch: The FireWatch object being processed.
    :param prediction: The WeatherIndeterminate object containing weather/FWI data.
    :param fbp_result: The result of the Fire Behaviour Prediction (FBP) calculation.
    :return: A FireWatchWeather object.
    """
    return FireWatchWeather(
        fire_watch_id=fire_watch.id,
        date=prediction.utc_timestamp.date(),
        prediction_model_run_timestamp_id=prediction_model_run_timestamp_id,
        temperature=prediction.temperature,
        relative_humidity=prediction.relative_humidity,
        precip_24hr=prediction.precipitation,
        wind_speed=prediction.wind_speed,
        ffmc=prediction.fine_fuel_moisture_code,
        isi=prediction.initial_spread_index,
        bui=prediction.build_up_index,
        dc=prediction.drought_code,
        dmc=prediction.duff_moisture_code,
        hfi=fbp_result.hfi,
        created_at=get_utc_now(),
    )


def validate_fire_watch_inputs(
    fire_watch: FireWatch,
    station_metadata: WFWXWeatherStation,
    actual_weather_data: List[WeatherIndeterminate],
    predictions: List[ModelPredictionDetails],
    start_date: datetime,
    end_date: datetime,
) -> bool:
    """
    Validate that all required data is available for processing a FireWatch.

    :param fire_watch: The FireWatch object being processed.
    :param station_metadata: Metadata about the weather station.
    :param actual_weather_data: List of actual weather data.
    :param predictions: List of weather model predictions.
    :param start_date: The start date for the required data range.
    :param end_date: The end date for the required data range.
    :return: True if all required data is available, False otherwise.
    """
    if not station_metadata:
        logger.error(f"Missing station metadata for station {fire_watch.station_code}.")
        return False

    # Check if all actual weather data contains valid temperature and FWI indices
    for actual in actual_weather_data:
        if actual.temperature is None or actual.fine_fuel_moisture_code is None or actual.initial_spread_index is None:
            logger.error(f"Invalid actual weather data for station {fire_watch.station_code} on {actual.utc_timestamp.date()}.")
            return False

    # extract dates from predictions and compare with required dates
    required_dates = set(start_date.date() + timedelta(days=i) for i in range((end_date - start_date).days + 1))
    prediction_dates = {prediction.prediction_timestamp.date() for prediction in predictions}

    # Check if all required dates are covered
    missing_dates = required_dates - prediction_dates
    if missing_dates:
        logger.error(f"Missing prediction data for station {fire_watch.station_code} on dates: {missing_dates}.")
        return False

    return True


def map_model_prediction_to_weather_indeterminate(model_prediction: ModelPredictionDetails, station_data: WFWXWeatherStation) -> WeatherIndeterminate:
    """Map ModelPredictionDetails to WeatherIndeterminate."""
    return WeatherIndeterminate(
        station_code=model_prediction.station_code,
        station_name=station_data.name,
        latitude=station_data.lat,  # latitude is need for FWI calculations
        longitude=station_data.long,
        determinate=WeatherDeterminate.from_string(model_prediction.abbreviation),
        utc_timestamp=model_prediction.prediction_timestamp,
        temperature=model_prediction.tmp_tgl_2,
        relative_humidity=model_prediction.rh_tgl_2,
        precipitation=model_prediction.precip_24h,
        wind_direction=model_prediction.wdir_tgl_10,
        wind_speed=model_prediction.wind_tgl_10,
        update_date=model_prediction.update_date,
        prediction_run_timestamp=model_prediction.prediction_run_timestamp,
    )


def calculate_fbp(
    fire_watch: FireWatch,
    station_data: WFWXWeatherStation,
    prediction: WeatherIndeterminate,
) -> FireBehaviourPrediction:
    """Calculate Fire Behaviour Prediction (FBP) and create FireWatchWeather."""
    # assert that we're working with all the same station's data
    assert fire_watch.station_code == station_data.code == prediction.station_code

    crown_base_height = FUEL_TYPE_DEFAULTS[fire_watch.fuel_type]["CBH"]
    crown_fuel_load = FUEL_TYPE_DEFAULTS[fire_watch.fuel_type]["CFL"]

    try:
        fbp = calculate_fire_behaviour_prediction(
            station_data.lat,
            station_data.long,
            station_data.elevation,
            fire_watch.fuel_type,
            prediction.build_up_index,
            prediction.fine_fuel_moisture_code,
            prediction.wind_speed,
            fire_watch.percent_grass_curing,
            fire_watch.percent_conifer,
            prediction.initial_spread_index,
            fire_watch.percent_dead_fir,
            crown_base_height,
            crown_fuel_load,
            prediction.utc_timestamp,
        )
    except (FireBehaviourPredictionInputError, CFFDRSException):
        logger.error(f"Error calculating FBP for fire watch {fire_watch.id} at station {fire_watch.station_code}.")
        return None

    return fbp


def check_prescription_status(fire_watch: FireWatch, weather: FireWatchWeather, status_id_dict: Dict[str, int]) -> str:
    """
    Check the prescription status of a fire watch based on weather conditions. Currently, we have three statuses:
    - All: All weather conditions are within the specified range.
    - HFI: Only the HFI is within the specified range.
    - No: Neither of the above conditions are met.
    """

    def in_range(val, min_val, max_val):
        return min_val <= val <= max_val

    checks = [
        in_range(weather.temperature, fire_watch.temp_min, fire_watch.temp_max),
        in_range(weather.relative_humidity, fire_watch.rh_min, fire_watch.rh_max),
        in_range(weather.wind_speed, fire_watch.wind_speed_min, fire_watch.wind_speed_max),
        in_range(weather.ffmc, fire_watch.ffmc_min, fire_watch.ffmc_max),
        in_range(weather.dmc, fire_watch.dmc_min, fire_watch.dmc_max),
        in_range(weather.dc, fire_watch.dc_min, fire_watch.dc_max),
        in_range(weather.isi, fire_watch.isi_min, fire_watch.isi_max),
        in_range(weather.bui, fire_watch.bui_min, fire_watch.bui_max),
    ]

    hfi_check = in_range(weather.hfi, fire_watch.hfi_min, fire_watch.hfi_max)

    if all(checks) and hfi_check:
        return status_id_dict["all"]
    elif hfi_check:
        return status_id_dict["hfi"]
    else:
        return status_id_dict["no"]


async def fetch_station_metadata(station_ids: List[int]) -> Dict[int, WFWXWeatherStation]:
    """Fetch station metadata from the WFWX API."""
    async with ClientSession() as session:
        header = await get_auth_header(session)
        wfwx_stations = await get_wfwx_stations_from_station_codes(session, header, station_ids)
        return {station.code: station for station in wfwx_stations}


async def fetch_actuals_and_forecasts(start_date: datetime, end_date: datetime, station_ids: List[int]) -> Tuple[List[WeatherIndeterminate], List[WeatherIndeterminate]]:
    """Fetch actuals and forecasts from the WFWX API."""
    async with ClientSession() as session:
        header = await get_auth_header(session)
        wf1_actuals, wf1_forecasts = await get_daily_determinates_for_stations_and_date(session, header, start_date, end_date, station_ids)
        return wf1_actuals, wf1_forecasts


async def save_all_hfi_wind_speeds(session: AsyncSession, fire_watch_weather_records: list[FireWatchWeather]):
    logger.info("Writing Fire Watch Weather records")
    session.add_all(fire_watch_weather_records)


async def process_all_fire_watch_weather(start_date: datetime):
    """Process fire watch weather data."""
    end_date = start_date + timedelta(days=10)
    end_date = datetime.combine(end_date, time.max, tzinfo=timezone.utc)

    async with get_async_write_session_scope() as session:
        fire_watches = await get_all_active_fire_watches(session)
        station_ids = list(set([fire_watch.station_code for fire_watch in fire_watches]))
        wfwx_station_map = await fetch_station_metadata(station_ids)
        status_id_dict = await get_all_prescription_status(session)

        for fire_watch in fire_watches:
            station_metadata = wfwx_station_map[fire_watch.station_code]

            predictions, actual_weather_data = await gather_fire_watch_inputs(session, fire_watch, start_date, end_date)

            if not validate_fire_watch_inputs(fire_watch, station_metadata, actual_weather_data, predictions, start_date, end_date):
                logger.warning(f"Skipping FireWatch {fire_watch.id} due to missing data.")
                continue

            # map prediction data from our db to WeatherIndeterminate for easy FWI calculations
            prediction_indeterminates = [map_model_prediction_to_weather_indeterminate(p, station_metadata) for p in predictions]
            fwi_prediction_indeterminates = calculate_fwi_from_seed_indeterminates(actual_weather_data, prediction_indeterminates)

            # iterate through our predictions to calculate FBP/prescription status and store results
            fire_watch_predictions = []
            for prediction in fwi_prediction_indeterminates:
                fbp = calculate_fbp(fire_watch, station_metadata, prediction)
                if fbp:
                    prediction_timestamp_id = next((p.prediction_model_run_timestamp_id for p in predictions if p.prediction_timestamp == prediction.utc_timestamp), None)
                    fire_watch_weather = map_to_fire_watch_weather(fire_watch, prediction, fbp, prediction_timestamp_id)

                    # finally check prescription status after running all calculations
                    status_id = check_prescription_status(fire_watch, fire_watch_weather, status_id_dict)
                    fire_watch_weather.in_prescription = status_id
                    fire_watch_predictions.append(fire_watch_weather)

            if fire_watch_predictions:
                await save_all_hfi_wind_speeds(session, fire_watch_predictions)
                logger.info(f"Saved {len(fire_watch_predictions)} records for FireWatch {fire_watch.id}.")


async def main():
    start_date = datetime(2025, 5, 5, tzinfo=timezone.utc)

    await process_all_fire_watch_weather(start_date)


if __name__ == "__main__":
    configure_logging()
    asyncio.run(main())
