from collections import defaultdict
from datetime import datetime, timedelta

from aiohttp import ClientSession
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.crud.weather_models import get_latest_model_prediction_for_stations
from wps_shared.schemas.morecast_v2 import WeatherDeterminate, WeatherIndeterminate
from wps_shared.schemas.weather_models import ModelPredictionDetails
from wps_shared.weather_models import ModelEnum
from wps_shared.wildfire_one.schema_parsers import WFWXWeatherStation
from wps_shared.wildfire_one.wfwx_api import get_auth_header, get_daily_determinates_for_stations_and_date, get_wfwx_stations_from_station_codes

from app.morecast_v2.forecasts import calculate_fwi_from_seed_indeterminates

WEATHER_MODEL = ModelEnum.GFS


def map_model_prediction_to_weather_indeterminate(model_prediction: ModelPredictionDetails, station_details: WFWXWeatherStation) -> WeatherIndeterminate:
    """Map ModelPredictionDetails to WeatherIndeterminateWithMetadata."""
    return WeatherIndeterminate(
        station_code=model_prediction.station_code,
        station_name=station_details.name,
        latitude=station_details.lat,
        longitude=station_details.long,
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


async def collect_fire_weather_data(db_session: AsyncSession, start_date: datetime, end_date: datetime, station_ids: list[int]):
    """
    Collect fire weather data for the given date range and station IDs. It will also project out the FWI values for predictions using actuals/forecasts
    as starting values.
    """
    # step 1: Fetch data
    predictions = await get_latest_model_prediction_for_stations(db_session, station_ids, WEATHER_MODEL, start_date, end_date)
    wfwx_station_map = await fetch_station_metadata(station_ids)
    wf1_actuals, wf1_forecasts = await fetch_actuals_and_forecasts(start_date, end_date, station_ids)

    # step 2: Prepare data for FWI calculation
    actuals_forecasts_in_range, predictions_in_range = prepare_data_for_fwi(wf1_actuals, wf1_forecasts, predictions, wfwx_station_map, station_ids, start_date, end_date)

    # if the date range is covered by actuals and forecasts, we don't need to calculate FWI for predictions
    if not predictions_in_range:
        return actuals_forecasts_in_range, []

    # step 3: Calculate FWI values for the predictions
    fwi_filled_predictions = calculate_fwi_from_seed_indeterminates(actuals_forecasts_in_range, predictions_in_range)

    return actuals_forecasts_in_range, fwi_filled_predictions


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


def prepare_data_for_fwi(
    wf1_actuals: list[WeatherIndeterminate],
    wf1_forecasts: list[WeatherIndeterminate],
    predictions: list[ModelPredictionDetails],
    wfwx_station_map: dict[int, WFWXWeatherStation],
    station_ids: list[int],
    start_date: datetime,
    end_date: datetime,
) -> tuple[list[WeatherIndeterminate], list[WeatherIndeterminate]]:
    """
    Prepare data for FWI calculation by filtering actuals, forecasts, and predictions within a range of dates.
    It will prioritize actuals over forecasts and forecasts over predictions for each station and date.
    """
    actuals_forecasts_in_range: list[WeatherIndeterminate] = []
    predictions_in_range: list[WeatherIndeterminate] = []
    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    # make dicts for fast lookup by station code and date
    forecast_map = {(f.station_code, f.utc_timestamp.date()): f for f in wf1_forecasts}
    actuals_map = {(a.station_code, a.utc_timestamp.date()): a for a in wf1_actuals}
    prediction_map = {(p.station_code, p.prediction_timestamp.date()): p for p in predictions}

    for station_id in station_ids:
        for date in date_range:
            key = (station_id, date.date())

            if key in actuals_map:
                actuals_forecasts_in_range.append(actuals_map[key])
            elif key in forecast_map:
                actuals_forecasts_in_range.append(forecast_map[key])
            elif key in prediction_map:
                prediction = map_model_prediction_to_weather_indeterminate(prediction_map[key], wfwx_station_map[station_id])
                predictions_in_range.append(prediction)

    return actuals_forecasts_in_range, predictions_in_range


def marshal_weather_data_to_api(actuals_forecasts: list[WeatherIndeterminate], predictions: list[WeatherIndeterminate]) -> dict[int, list[WeatherIndeterminate]]:
    # Group records by station code
    grouped_records = defaultdict(list)
    for record in actuals_forecasts + predictions:
        grouped_records[record.station_code].append(record)

    # Sort records by date for each station code
    sorted_records = {station_code: sorted(records, key=lambda r: r.utc_timestamp) for station_code, records in grouped_records.items()}

    return sorted_records
