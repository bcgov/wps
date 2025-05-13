import asyncio
import logging
from datetime import datetime, time, timedelta, timezone

from aiohttp import ClientSession
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.crud.fire_watch import get_all_fire_watches, get_all_prescription_status
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

from app.fire_behaviour.prediction import FireBehaviourPrediction, calculate_fire_behaviour_prediction
from app.morecast_v2.forecasts import calculate_fwi_from_seed_indeterminates

logger = logging.getLogger(__name__)

FIREWATCH_WEATHER_MODEL = ModelEnum.GFS


async def gather_fire_watch_inputs(
    session: AsyncSession,
    fire_watch: FireWatch,
    start_date: datetime,
    end_date: datetime,
) -> tuple[list[ModelPredictionDetails], list[WeatherIndeterminate]]:
    """
    Gather all the inputs required for processing a FireWatch.
    """

    # fetch weather model predictions
    predictions = await get_latest_model_prediction_for_stations(session, [fire_watch.station_code], FIREWATCH_WEATHER_MODEL, start_date, end_date)

    # fetch actual weather data. Using this method as it may make it easier to pull in forecasts if we want to.
    actual_weather_data, _ = await fetch_actuals_and_forecasts(start_date - timedelta(days=1), start_date, [fire_watch.station_code])

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
    actual_weather_data: list[WeatherIndeterminate],
    predictions: list[ModelPredictionDetails],
    start_date: datetime,
    end_date: datetime,
) -> bool:
    """
    Validate that all required data is available for processing a FireWatch.
    """
    if not station_metadata:
        logger.warning(f"Missing station metadata for station {fire_watch.station_code}.")
        return False

    if not validate_actual_weather_data(actual_weather_data, fire_watch.station_code):
        return False

    if not validate_prediction_dates(predictions, start_date, end_date, fire_watch.station_code):
        return False

    return True


def validate_actual_weather_data(actual_weather_data: list[WeatherIndeterminate], station_code: int) -> bool:
    """
    Validate actual weather data for a station.
    """
    if any(
        actual.temperature is None  # use temp as a smoke test for missing weather data
        or actual.fine_fuel_moisture_code is None
        or actual.initial_spread_index is None
        or actual.duff_moisture_code is None
        or actual.drought_code is None
        or actual.build_up_index is None
        for actual in actual_weather_data
    ):
        logger.warning(f"Invalid actual weather data for station {station_code}.")
        return False
    return True


def validate_prediction_dates(
    predictions: list[ModelPredictionDetails],
    start_date: datetime,
    end_date: datetime,
    station_code: int,
) -> bool:
    """
    Validate that there is a prediction at 20:00 UTC for every day in the date range.
    """
    required_datetimes = {datetime.combine(start_date.date() + timedelta(days=i), time(20, 0), tzinfo=timezone.utc) for i in range((end_date.date() - start_date.date()).days + 1)}

    prediction_datetimes = {prediction.prediction_timestamp.replace(second=0, microsecond=0) for prediction in predictions}

    missing_datetimes = required_datetimes - prediction_datetimes

    if missing_datetimes:
        missing_str = ", ".join(dt.strftime("%Y-%m-%d %H:%M UTC") for dt in sorted(missing_datetimes))
        logger.warning(f"Missing 20Z prediction data for station {station_code} on: {missing_str}")
        return False

    return True


def map_model_prediction_to_weather_indeterminate(model_prediction: ModelPredictionDetails, station_data: WFWXWeatherStation) -> WeatherIndeterminate:
    """
    Map a ModelPredictionDetails object to a WeatherIndeterminate object, filling in station metadata that is needed for FWI calculations.
    """
    return WeatherIndeterminate(
        station_code=model_prediction.station_code,
        station_name=station_data.name,
        latitude=station_data.lat,  # latitude is needed for FWI calculations
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
    assert fire_watch.station_code == station_data.code == prediction.station_code, "Station codes do not match for fbp calculation"

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
    except Exception as e:
        logger.error(f"Error calculating FBP for fire watch {fire_watch.id} at station {fire_watch.station_code}: {e}")
        return None

    return fbp


def check_prescription_status(fire_watch: FireWatch, weather: FireWatchWeather, status_id_dict: dict[str, int]) -> str:
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


async def fetch_station_metadata(station_ids: list[int]) -> dict[int, WFWXWeatherStation]:
    """Fetch station metadata from the WFWX API."""
    async with ClientSession() as session:
        header = await get_auth_header(session)
        wfwx_stations = await get_wfwx_stations_from_station_codes(session, header, station_ids)
        return {station.code: station for station in wfwx_stations}


async def fetch_actuals_and_forecasts(start_date: datetime, end_date: datetime, station_ids: list[int]) -> tuple[list[WeatherIndeterminate], list[WeatherIndeterminate]]:
    """Fetch actuals and forecasts from the WFWX API."""
    async with ClientSession() as session:
        header = await get_auth_header(session)
        wf1_actuals, wf1_forecasts = await get_daily_determinates_for_stations_and_date(session, header, start_date, end_date, station_ids)
        return wf1_actuals, wf1_forecasts


async def save_all_fire_watch_weather(session: AsyncSession, fire_watch_weather_records: list[FireWatchWeather]):
    logger.info("Writing Fire Watch Weather records")
    session.add_all(fire_watch_weather_records)


async def process_single_fire_watch(
    session: AsyncSession,
    fire_watch: FireWatch,
    wfwx_station_map: dict[int, WFWXWeatherStation],
    status_id_dict: dict[str, int],
    start_date: datetime,
    end_date: datetime,
):
    """
    Process a single FireWatch by gathering inputs, validating them, and saving results.
    """
    station_metadata = wfwx_station_map.get(fire_watch.station_code)
    if not station_metadata:
        logger.warning(f"Skipping FireWatch {fire_watch.id}: Missing station metadata.")
        return

    predictions, actual_weather_data = await gather_fire_watch_inputs(session, fire_watch, start_date, end_date)

    if not validate_fire_watch_inputs(fire_watch, station_metadata, actual_weather_data, predictions, start_date, end_date):
        logger.warning(f"Skipping FireWatch {fire_watch.id} due to missing or invalid data.")
        return

    fire_watch_predictions = await process_predictions(fire_watch, station_metadata, predictions, actual_weather_data, status_id_dict)

    if fire_watch_predictions:
        await save_all_fire_watch_weather(session, fire_watch_predictions)
        logger.info(f"Saved {len(fire_watch_predictions)} records for FireWatch {fire_watch.id}.")


async def process_predictions(
    fire_watch: FireWatch,
    station_metadata: WFWXWeatherStation,
    predictions: list[ModelPredictionDetails],
    actual_weather_data: list[WeatherIndeterminate],
    status_id_dict: dict[str, int],
) -> list[FireWatchWeather]:
    """
    Process predictions for a FireWatch and calculate FBP and prescription status.
    """
    prediction_indeterminates = [map_model_prediction_to_weather_indeterminate(p, station_metadata) for p in predictions]
    fwi_prediction_indeterminates = calculate_fwi_from_seed_indeterminates(actual_weather_data, prediction_indeterminates)

    fire_watch_predictions = []
    for prediction in fwi_prediction_indeterminates:
        fbp = calculate_fbp(fire_watch, station_metadata, prediction)
        if not fbp:
            continue

        prediction_timestamp_id = next(
            (p.prediction_model_run_timestamp_id for p in predictions if p.prediction_timestamp == prediction.utc_timestamp),
            None,
        )
        fire_watch_weather = map_to_fire_watch_weather(fire_watch, prediction, fbp, prediction_timestamp_id)

        # Check prescription status
        status_id = check_prescription_status(fire_watch, fire_watch_weather, status_id_dict)
        fire_watch_weather.in_prescription = status_id
        fire_watch_predictions.append(fire_watch_weather)

    return fire_watch_predictions


async def process_all_fire_watch_weather(start_date: datetime):
    """
    Process all FireWatch weather data by gathering inputs, validating them, and saving results.
    """
    # Set the end date to 10 calendar days after the start date, including today
    end_date = datetime.combine(start_date + timedelta(days=9), time.max, tzinfo=timezone.utc)

    async with get_async_write_session_scope() as session:
        fire_watches = await get_all_fire_watches(session)
        station_ids = {fire_watch.station_code for fire_watch, _ in fire_watches}
        wfwx_station_map = await fetch_station_metadata(station_ids)
        status_id_dict = await get_all_prescription_status(session)

        for fire_watch, _ in fire_watches:
            await process_single_fire_watch(session, fire_watch, wfwx_station_map, status_id_dict, start_date, end_date)
