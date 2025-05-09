import asyncio
from datetime import datetime, timedelta, timezone

from aiohttp import ClientSession
from shapely import Point
from sqlalchemy.ext.asyncio import AsyncSession
from wps_shared.db.crud.fire_watch import get_all_prescription_status
from wps_shared.db.crud.weather_models import get_latest_model_prediction_for_stations
from wps_shared.db.database import get_async_write_session_scope
from wps_shared.db.models.fire_watch import BurnStatusEnum, FireWatch, FireWatchWeather
from wps_shared.fuel_types import FUEL_TYPE_DEFAULTS, FuelTypeEnum
from wps_shared.schemas.morecast_v2 import WeatherDeterminate, WeatherIndeterminate
from wps_shared.schemas.weather_models import ModelPredictionDetails
from wps_shared.weather_models import ModelEnum
from wps_shared.wildfire_one.schema_parsers import WFWXWeatherStation
from wps_shared.wildfire_one.wfwx_api import get_auth_header, get_daily_determinates_for_stations_and_date, get_wfwx_stations_from_station_codes

from app.fire_behaviour.cffdrs import CFFDRSException
from app.fire_behaviour.prediction import FireBehaviourPredictionInputError, calculate_fire_behaviour_prediction
from app.morecast_v2.forecasts import calculate_fwi_from_seed_indeterminates

FIREWATCH_WEATHER_MODEL = ModelEnum.GFS


def create_test_fire_watch(station_code: int) -> FireWatch:
    # Create a FireWatch object with sample data
    fire_watch = FireWatch(
        burn_location=Point(-123.3656, 48.4284),
        burn_window_start=datetime.now(timezone.utc),
        burn_window_end=datetime.now(timezone.utc) + timedelta(days=1),
        contact_email=["test@example.com"],
        create_timestamp=datetime.now(timezone.utc),
        create_user="test_user",
        fire_centre=None,  # Set to None or a valid FireCentre ID if available
        station_code=station_code,
        status=BurnStatusEnum.ACTIVE,
        title="Test Burn",
        update_timestamp=datetime.now(timezone.utc),
        update_user="test_user",
        fuel_type=FuelTypeEnum.C3,
        percent_conifer=0.0,
        percent_dead_fir=0.0,
        percent_grass_curing=0.0,
        temp_min=10.0,
        temp_preferred=20.0,
        temp_max=30.0,
        rh_min=30.0,
        rh_preferred=50.0,
        rh_max=70.0,
        wind_speed_min=5.0,
        wind_speed_preferred=10.0,
        wind_speed_max=20.0,
        ffmc_min=85.0,
        ffmc_preferred=90.0,
        ffmc_max=95.0,
        dmc_min=10.0,
        dmc_preferred=15.0,
        dmc_max=20.0,
        dc_min=300.0,
        dc_preferred=400.0,
        dc_max=500.0,
        isi_min=2.0,
        isi_preferred=5.0,
        isi_max=10.0,
        bui_min=40.0,
        bui_preferred=50.0,
        bui_max=60.0,
        hfi_min=1000.0,
        hfi_preferred=2000.0,
        hfi_max=3000.0,
    )
    return fire_watch


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


async def calculate_fire_watch_weather(db_session: AsyncSession, start_date: datetime, end_date: datetime, fire_watch: FireWatch, station_data: WFWXWeatherStation):
    """
    Collect fire weather data for the given date range and station IDs. It will also project out the FWI values for predictions using actuals/forecasts
    as starting values.
    """
    day_before_start_date = start_date - timedelta(days=1)

    # step 1: Fetch data
    predictions = await get_latest_model_prediction_for_stations(db_session, [fire_watch.station_code], FIREWATCH_WEATHER_MODEL, start_date, end_date)
    prediction_id = predictions[0].prediction_model_run_timestamp_id  # all predictions should have the same id
    wf1_actuals, _ = await fetch_actuals_and_forecasts(day_before_start_date, end_date, [fire_watch.station_code])
    wf1_actuals = [wf1_actuals[0]]

    # step 2: Map model predictions to WeatherIndeterminate to calculate FWI
    prediction_indeterminates = [map_model_prediction_to_weather_indeterminate(p, station_data) for p in predictions]
    fwi_prediction_indeterminates = calculate_fwi_from_seed_indeterminates(wf1_actuals, prediction_indeterminates)

    # step 3: Calculate FBP
    fire_watch_predictions = []
    for prediction in fwi_prediction_indeterminates:
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
            continue

        # step 4: Create FireWatchWeather object
        fire_watch_weather = FireWatchWeather(
            fire_watch_id=fire_watch.id,
            date=prediction.utc_timestamp.date(),
            prediction_model_run_timestamp_id=prediction_id,
            temperature=prediction.temperature,
            relative_humidity=prediction.relative_humidity,
            precip_24hr=prediction.precipitation,
            wind_speed=prediction.wind_speed,
            ffmc=prediction.fine_fuel_moisture_code,
            isi=prediction.initial_spread_index,
            bui=prediction.build_up_index,
            dc=prediction.drought_code,
            dmc=prediction.duff_moisture_code,
            hfi=fbp.hfi,
        )
        fire_watch_predictions.append(fire_watch_weather)

    return fire_watch_predictions


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


def check_prescription_statuses(watch: FireWatch, weather: FireWatchWeather, status_id_dict: dict[str, int]) -> str:
    def in_range(val, min_val, max_val):
        return min_val <= val <= max_val

    checks = [
        in_range(weather.temperature, watch.temp_min, watch.temp_max),
        in_range(weather.relative_humidity, watch.rh_min, watch.rh_max),
        in_range(weather.wind_speed, watch.wind_speed_min, watch.wind_speed_max),
        in_range(weather.ffmc, watch.ffmc_min, watch.ffmc_max),
        in_range(weather.dmc, watch.dmc_min, watch.dmc_max),
        in_range(weather.dc, watch.dc_min, watch.dc_max),
        in_range(weather.isi, watch.isi_min, watch.isi_max),
        in_range(weather.bui, watch.bui_min, watch.bui_max),
    ]

    hfi_check = in_range(weather.hfi, watch.hfi_min, watch.hfi_max)

    if all(checks) and hfi_check:
        return status_id_dict["all"]
    elif hfi_check:
        return status_id_dict["hfi"]
    else:
        return status_id_dict["no"]


async def process_all_fire_watch_weather(fire_watches: list[FireWatch]):
    """
    Process fire watch weather data by fetching actuals and forecasts, preparing data for FWI calculation,
    and marshaling the results into a format suitable for API response.
    """
    start_date = datetime(2025, 4, 25, tzinfo=timezone.utc)
    end_date = start_date + timedelta(days=10)

    station_ids = [fire_watch.station_code for fire_watch in fire_watches]
    wfwx_station_map = await fetch_station_metadata(station_ids)  # we need station metadata (lat/long/elevation) for FBP calculation

    async with get_async_write_session_scope() as session:
        status_id_dict = await get_all_prescription_status(session)
        for fire_watch in fire_watches:
            station_metadata = wfwx_station_map[fire_watch.station_code]
            fire_watch_weather_predictions = await calculate_fire_watch_weather(session, start_date, end_date, fire_watch, station_metadata)

            for weather in fire_watch_weather_predictions:
                # Check the prescription status based on the weather data
                status_id = check_prescription_statuses(fire_watch, weather, status_id_dict)
                weather.in_prescription = status_id

                print(weather.in_prescription)


async def main():
    fire_watches = [create_test_fire_watch(station_code) for station_code in [392, 393]]

    await process_all_fire_watch_weather(fire_watches)


if __name__ == "__main__":
    asyncio.run(main())
