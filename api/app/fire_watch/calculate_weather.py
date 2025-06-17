import logging
from datetime import datetime, time, timedelta, timezone

from aiohttp import ClientSession
from app.fire_behaviour.prediction import (
    FireBehaviourPrediction,
    calculate_fire_behaviour_prediction,
)
from app.morecast_v2.forecasts import calculate_fwi_from_seed_indeterminates
from sqlalchemy.ext.asyncio import AsyncSession

from wps_shared.db.crud.fire_watch import (
    get_all_prescription_status,
    get_fire_watch_weather_by_fire_watch_id_and_model_run,
    get_fire_watches_missing_weather_for_run,
)
from wps_shared.db.crud.weather_models import (
    get_latest_daily_model_prediction_for_stations,
    get_latest_prediction_timestamp_id_for_model,
)
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.fire_watch import FireWatch, FireWatchWeather
from wps_shared.fuel_types import FUEL_TYPE_DEFAULTS
from wps_shared.schemas.morecast_v2 import WeatherDeterminate, WeatherIndeterminate
from wps_shared.schemas.weather_models import ModelPredictionDetails
from wps_shared.utils.time import assert_all_utc, get_utc_now
from wps_shared.weather_models import ModelEnum
from wps_shared.wildfire_one.schema_parsers import WFWXWeatherStation
from wps_shared.wildfire_one.wfwx_api import (
    get_auth_header,
    get_daily_determinates_for_stations_and_date,
    get_wfwx_stations_from_station_codes,
)

logger = logging.getLogger(__name__)

FIREWATCH_WEATHER_MODEL = ModelEnum.GFS


class MissingWeatherDataError(Exception):
    """
    Exception raised when weather data that is needed for calculations is missing.
    """


async def gather_fire_watch_inputs(
    session: AsyncSession,
    fire_watch: FireWatch,
    prediction_run_timestamp_id: int,
) -> tuple[list[ModelPredictionDetails], list[WeatherIndeterminate]]:
    """
    Gather all the inputs required for processing a FireWatch.
    """

    # fetch weather model predictions
    predictions = await get_latest_daily_model_prediction_for_stations(
        session, [fire_watch.station_code], prediction_run_timestamp_id
    )

    first_prediction_date: datetime = min((p.prediction_timestamp for p in predictions))

    actual_datetime_needed = first_prediction_date - timedelta(days=1)

    # fetch actual weather data. Using this method as it may make it easier to pull in forecasts if we want to.
    actual_weather_data, _ = await get_actuals_and_forecasts(
        actual_datetime_needed, actual_datetime_needed, [fire_watch.station_code]
    )

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
) -> bool:
    """
    Validate that all required data is available for processing a FireWatch.
    """
    if not station_metadata:
        raise MissingWeatherDataError(
            f"Missing station metadata for station {fire_watch.station_code}."
        )

    if not validate_actual_weather_data(actual_weather_data):
        raise MissingWeatherDataError(
            f"Invalid actual weather data for station {fire_watch.station_code}."
        )

    return True


def validate_actual_weather_data(actual_weather_data: list[WeatherIndeterminate]) -> bool:
    """
    Validate actual weather data for a station.
    """
    if not actual_weather_data:
        logger.warning("Station missing actual weather data.")
        return False

    required_fields = [
        "temperature",
        "relative_humidity",
        "precipitation",
        "wind_speed",
        "fine_fuel_moisture_code",
        "initial_spread_index",
        "duff_moisture_code",
        "drought_code",
        "build_up_index",
    ]

    for actual in actual_weather_data:
        if any(getattr(actual, field) is None for field in required_fields):
            logger.warning(
                f"Invalid actual weather data for station {actual.station_code} at {actual.utc_timestamp}."
            )
            return False

    return True


def validate_prediction_dates(
    predictions: list[ModelPredictionDetails],
    start_date: datetime,
    end_date: datetime,
) -> bool:
    """
    Validate that there is a prediction at 20:00 UTC for every day in the date range.
    """

    required_datetimes = {
        datetime.combine(start_date.date() + timedelta(days=i), time(20, 0), tzinfo=timezone.utc)
        for i in range((end_date.date() - start_date.date()).days + 1)
    }

    prediction_datetimes = {
        prediction.prediction_timestamp.replace(second=0, microsecond=0)
        for prediction in predictions
    }

    try:
        assert_all_utc(*prediction_datetimes)  # ensure all datetimes are UTC
    except AssertionError:
        logger.warning("Prediction datetimes are not in UTC.")
        return False

    missing_datetimes = required_datetimes - prediction_datetimes
    if missing_datetimes:
        missing_str = ", ".join(
            dt.strftime("%Y-%m-%d %H:%M UTC") for dt in sorted(missing_datetimes)
        )
        logger.warning(
            f"Missing 20Z prediction data for station {predictions[0].station_code} on: {missing_str}"
        )
        return False

    return True


def map_model_prediction_to_weather_indeterminate(
    model_prediction: ModelPredictionDetails, station_data: WFWXWeatherStation
) -> WeatherIndeterminate:
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
    """Calculate Fire Behaviour Prediction (FBP)"""
    # assert that we're working with all the same station's data
    assert fire_watch.station_code == station_data.code == prediction.station_code, (
        "Station codes do not match for fbp calculation"
    )

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
        logger.error(
            f"Error calculating FBP for fire watch {fire_watch.id} - {fire_watch.title} at station {fire_watch.station_code}: {e}"
        )
        return None

    return fbp


def check_prescription_status(
    fire_watch: FireWatch, weather: FireWatchWeather, status_id_dict: dict[str, int]
) -> str:
    """
    Check the prescription status of a fire watch based on weather conditions. Currently, we have three statuses:
    - All: All weather conditions are within the specified range.
    - HFI: Only the HFI is within the specified range.
    - No: Neither of the above conditions are met.
    """

    def in_range(val, min_val, max_val):
        return min_val <= val <= max_val

    # always required weather checks
    weather_checks = [
        in_range(weather.temperature, fire_watch.temp_min, fire_watch.temp_max),
        in_range(weather.relative_humidity, fire_watch.rh_min, fire_watch.rh_max),
        in_range(weather.wind_speed, fire_watch.wind_speed_min, fire_watch.wind_speed_max),
    ]

    # always required FBP check
    hfi_check = in_range(weather.hfi, fire_watch.hfi_min, fire_watch.hfi_max)

    # optional FWI checks
    fwi_checks = dict()
    for field in FireWatch.OPTIONAL_FWI_FIELDS:
        min_val = getattr(fire_watch, f"{field}_min", None)
        max_val = getattr(fire_watch, f"{field}_max", None)
        # only check if both min and max is set (required for this FireWatch)
        if min_val is not None and max_val is not None:
            value = getattr(weather, field, None)

            if value is not None:
                # check if the value is in range
                fwi_in_range = in_range(value, min_val, max_val)
                fwi_checks[field] = fwi_in_range

    if all(weather_checks) and hfi_check and all(fwi_checks.values()):
        return status_id_dict["all"]
    elif hfi_check:
        return status_id_dict["hfi"]
    else:
        return status_id_dict["no"]


async def get_station_metadata(station_ids: list[int]) -> dict[int, WFWXWeatherStation]:
    """Fetch station metadata from the WFWX API."""
    async with ClientSession() as session:
        header = await get_auth_header(session)
        wfwx_stations = await get_wfwx_stations_from_station_codes(session, header, station_ids)
        return {station.code: station for station in wfwx_stations}


async def get_actuals_and_forecasts(
    start_date: datetime, end_date: datetime, station_ids: list[int]
) -> tuple[list[WeatherIndeterminate], list[WeatherIndeterminate]]:
    """Fetch actuals and forecasts from the WFWX API."""
    async with ClientSession() as session:
        header = await get_auth_header(session)
        wf1_actuals, wf1_forecasts = await get_daily_determinates_for_stations_and_date(
            session, header, start_date, end_date, station_ids, check_cache=False
        )
        return wf1_actuals, wf1_forecasts


async def save_all_fire_watch_weather(
    session: AsyncSession, fire_watch_weather_records: list[FireWatchWeather]
):
    logger.info("Writing Fire Watch Weather records")

    # fetch all existing records for this fire_watch and model run
    fire_watch_id = fire_watch_weather_records[0].fire_watch_id
    prediction_model_run_timestamp_id = fire_watch_weather_records[
        0
    ].prediction_model_run_timestamp_id

    existing_records = (
        await get_fire_watch_weather_by_fire_watch_id_and_model_run(
            session, fire_watch_id, prediction_model_run_timestamp_id
        )
        or []
    )

    existing_by_date = {rec.date: rec for rec in existing_records}

    for record in fire_watch_weather_records:
        existing_record = existing_by_date.get(record.date)
        if existing_record:
            for attr in FireWatchWeather.UPDATABLE_FIELDS:
                setattr(existing_record, attr, getattr(record, attr))
        else:
            session.add(record)


async def process_predictions(
    fire_watch: FireWatch,
    station_metadata: WFWXWeatherStation,
    predictions: list[ModelPredictionDetails],
    actual_weather_data: list[WeatherIndeterminate],
    status_id_dict: dict[str, int],
    prediction_run_timestamp_id: int,
) -> list[FireWatchWeather]:
    """
    Processes weather model predictions for a FireWatch to calculate FBP and prescription status.

    :param fire_watch: The FireWatch instance to process.
    :param station_metadata: Metadata for the weather station.
    :param predictions: List of model predictions.
    :param actual_weather_data: List of actual weather data.
    :param status_id_dict: Dictionary mapping status IDs to their descriptions.
    :return: List of FireWatchWeather instances.
    """
    prediction_indeterminates = [
        map_model_prediction_to_weather_indeterminate(p, station_metadata) for p in predictions
    ]
    fwi_prediction_indeterminates = calculate_fwi_from_seed_indeterminates(
        actual_weather_data, prediction_indeterminates
    )

    fire_watch_predictions = []
    for prediction in fwi_prediction_indeterminates:
        fbp = calculate_fbp(fire_watch, station_metadata, prediction)
        if not fbp:
            raise RuntimeError(
                f"Could not calculate FBP for prediction at {prediction.utc_timestamp} "
                f"for FireWatch {fire_watch.id} - {fire_watch.title} at station {fire_watch.station_code}"
            )

        fire_watch_weather = map_to_fire_watch_weather(
            fire_watch, prediction, fbp, prediction_run_timestamp_id
        )

        # Check prescription status
        status_id = check_prescription_status(fire_watch, fire_watch_weather, status_id_dict)
        fire_watch_weather.in_prescription = status_id
        fire_watch_predictions.append(fire_watch_weather)

    return fire_watch_predictions


async def process_single_fire_watch(
    session: AsyncSession,
    fire_watch: FireWatch,
    wfwx_station_map: dict[int, WFWXWeatherStation],
    status_id_dict: dict[str, int],
    prediction_run_timestamp_id: int,
):
    """
    Process a single FireWatch by gathering inputs, validating them, and saving results.

    :param session: Async database session.
    :param fire_watch: The FireWatch instance to process.
    :param wfwx_station_map: Mapping of station codes to their metadata.
    :param status_id_dict: Mapping of status IDs to their descriptions.
    :param prediction_run_timestamp_id: The ID of the prediction run timestamp.
    """
    station_metadata = wfwx_station_map.get(fire_watch.station_code)
    if not station_metadata:
        logger.warning(
            f"Skipping FireWatch {fire_watch.id} - {fire_watch.title}: Missing station metadata."
        )
        return

    predictions, actual_weather_data = await gather_fire_watch_inputs(
        session, fire_watch, prediction_run_timestamp_id
    )

    if not validate_fire_watch_inputs(fire_watch, station_metadata, actual_weather_data):
        raise ValueError(
            f"Invalid inputs for FireWatch {fire_watch.id} - {fire_watch.title} at station {fire_watch.station_code}."
        )

    fire_watch_predictions = await process_predictions(
        fire_watch,
        station_metadata,
        predictions,
        actual_weather_data,
        status_id_dict,
        prediction_run_timestamp_id,
    )

    if fire_watch_predictions:
        await save_all_fire_watch_weather(session, fire_watch_predictions)
        logger.info(
            f"Saved {len(fire_watch_predictions)} records for FireWatch {fire_watch.id} - {fire_watch.title}."
        )


async def process_all_fire_watch_weather():
    """
    Process all FireWatch weather data by gathering inputs, validating them, and saving results.
    """

    async with get_async_write_session_scope() as session:
        latest_prediction_id = await get_latest_prediction_timestamp_id_for_model(
            session, FIREWATCH_WEATHER_MODEL
        )
        fire_watches_to_process = await get_fire_watches_missing_weather_for_run(
            session, latest_prediction_id
        )

        if not fire_watches_to_process:
            logger.info(
                f"All FireWatch records already processed for prediction id: {latest_prediction_id}."
            )
            return

        station_ids = set(fire_watch.station_code for fire_watch in fire_watches_to_process)
        wfwx_station_map = await get_station_metadata(list(station_ids))
        status_id_dict = await get_all_prescription_status(session)

        for fire_watch in fire_watches_to_process:
            try:
                logger.info(
                    f"Processing FireWatch {fire_watch.id} - {fire_watch.title} using station {fire_watch.station_code} and {FIREWATCH_WEATHER_MODEL.value} data - prediction_timestamp_id {latest_prediction_id}."
                )
                await process_single_fire_watch(
                    session,
                    fire_watch,
                    wfwx_station_map,
                    status_id_dict,
                    latest_prediction_id,
                )
            except Exception as e:
                logger.error(f"Error processing FireWatch {fire_watch.id}: {e}")


async def reprocess_fire_watch_weather(
    session: AsyncSession,
    fire_watch: FireWatch,
    latest_model_run_parameters_id: int,
):
    wfwx_station_map = await get_station_metadata([fire_watch.station_code])
    status_id_dict = await get_all_prescription_status(session)
    await process_single_fire_watch(
        session,
        fire_watch,
        wfwx_station_map,
        status_id_dict,
        latest_model_run_parameters_id,
    )

    # flush to ensure the updated records are available for subsequent queries
    await session.flush()
