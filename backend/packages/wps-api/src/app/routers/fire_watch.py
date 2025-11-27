from collections import defaultdict
import logging
from datetime import datetime
from typing import List, Sequence, Tuple

from aiohttp import ClientSession
from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from shapely import from_wkt
from sqlalchemy import Row

from app.fire_watch.calculate_weather import (
    MissingWeatherDataError,
    reprocess_fire_watch_weather,
)
from wps_shared.auth import audit, authentication_required
from wps_shared.db.crud.fire_watch import (
    get_all_fire_watch_weather_with_prescription_status,
    get_all_fire_watches,
    get_fire_centre_by_name,
    get_fire_centres,
    get_fire_watch_by_id,
    get_fire_watch_weather_by_model_with_prescription_status,
    get_latest_processed_model_run_id_in_fire_watch_weather,
    save_fire_watch,
    update_fire_watch,
)
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.fire_watch import BurnStatusEnum, FireWatch, FireWatchWeather
from wps_shared.db.models.fire_watch import FireWatch as DBFireWatch
from wps_shared.fuel_types import FuelTypeEnum
from wps_shared.geospatial.geospatial import NAD83_BC_ALBERS, WEB_MERCATOR, PointTransformer
from wps_shared.schemas.fire_watch import (
    BurnForecastOutput,
    FireWatchBurnForecastsResponse,
    FireWatchFireCentre,
    FireWatchFireCentresResponse,
    FireWatchInput,
    FireWatchInputRequest,
    FireWatchListResponse,
    FireWatchOutput,
    FireWatchOutputBurnForecast,
    FireWatchResponse,
    FireWatchStation,
)
from wps_shared.schemas.hfi_calc import FireCentre
from wps_shared.schemas.stations import GeoJsonWeatherStation
from wps_shared.stations import get_stations_as_geojson
from wps_shared.utils.time import get_utc_now

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fire-watch",
    dependencies=[Depends(authentication_required), Depends(audit)],
)


def reproject_burn_location(coordinate: List[float], source_srs, target_srs):
    """Reproject a coordinate between the specified spatial references"""
    transformer = PointTransformer(source_srs, target_srs)
    return transformer.transform_coordinate(coordinate[0], coordinate[1])


async def get_fire_centre_id_by_name(name: str):
    async with ClientSession as session:
        result = await get_fire_centre_by_name(session, name)
        return result.id


def marshall_fire_watch_input_to_db(
    fire_watch_input: FireWatchInput, idir_username: str
) -> DBFireWatch:
    now = get_utc_now()
    x, y = reproject_burn_location(fire_watch_input.burn_location, WEB_MERCATOR, NAD83_BC_ALBERS)
    db_fire_watch = DBFireWatch(
        burn_location=f"POINT({x} {y})",
        burn_window_end=datetime.fromisoformat(fire_watch_input.burn_window_end)
        if fire_watch_input.burn_window_end
        else None,
        burn_window_start=datetime.fromisoformat(fire_watch_input.burn_window_start)
        if fire_watch_input.burn_window_start
        else None,
        contact_email=fire_watch_input.contact_email,
        create_timestamp=now,
        create_user=idir_username,
        fire_centre=fire_watch_input.fire_centre.id,
        station_code=fire_watch_input.station.code,
        status=BurnStatusEnum(fire_watch_input.status),
        title=fire_watch_input.title,
        update_timestamp=now,
        update_user=idir_username,
        # Fuel parameters
        fuel_type=FuelTypeEnum(fire_watch_input.fuel_type),
        percent_conifer=fire_watch_input.percent_conifer,
        percent_dead_fir=fire_watch_input.percent_dead_fir,
        percent_grass_curing=fire_watch_input.percent_grass_curing,
        # Weather parameters
        temp_min=fire_watch_input.temp_min,
        temp_preferred=fire_watch_input.temp_preferred,
        temp_max=fire_watch_input.temp_max,
        rh_min=fire_watch_input.rh_min,
        rh_preferred=fire_watch_input.rh_preferred,
        rh_max=fire_watch_input.rh_max,
        wind_speed_min=fire_watch_input.wind_speed_min,
        wind_speed_preferred=fire_watch_input.wind_speed_preferred,
        wind_speed_max=fire_watch_input.wind_speed_max,
        # FWI and FBP parameters
        ffmc_min=fire_watch_input.ffmc_min,
        ffmc_preferred=fire_watch_input.ffmc_preferred,
        ffmc_max=fire_watch_input.ffmc_max,
        dmc_min=fire_watch_input.dmc_min,
        dmc_preferred=fire_watch_input.dmc_preferred,
        dmc_max=fire_watch_input.dmc_max,
        dc_min=fire_watch_input.dc_min,
        dc_preferred=fire_watch_input.dc_preferred,
        dc_max=fire_watch_input.dc_max,
        isi_min=fire_watch_input.isi_min,
        isi_preferred=fire_watch_input.isi_preferred,
        isi_max=fire_watch_input.isi_max,
        bui_min=fire_watch_input.bui_min,
        bui_preferred=fire_watch_input.bui_preferred,
        bui_max=fire_watch_input.bui_max,
        hfi_min=fire_watch_input.hfi_min,
        hfi_preferred=fire_watch_input.hfi_preferred,
        hfi_max=fire_watch_input.hfi_max,
    )
    return db_fire_watch


def get_coordinates_from_geometry(geometry) -> List[float]:
    if isinstance(geometry, str):
        return from_wkt(geometry)
    elif isinstance(geometry, WKBElement):
        return to_shape(geometry)
    raise TypeError("Unrecognized geometry type.")


def create_fire_watch_output(
    db_fire_watch: DBFireWatch,
    fire_centre: FireWatchFireCentre,
    stations: List[GeoJsonWeatherStation],
) -> FireWatchOutput:
    station = next(
        (station for station in stations if station.properties.code == db_fire_watch.station_code),
        None,
    )
    fw_station = None
    if station:
        fw_station = FireWatchStation(code=station.properties.code, name=station.properties.name)

    location = get_coordinates_from_geometry(db_fire_watch.burn_location)
    coords = location.coords[0]
    x, y = reproject_burn_location(coords, NAD83_BC_ALBERS, WEB_MERCATOR)
    return FireWatchOutput(
        id=db_fire_watch.id,
        burn_location=[x, y],
        burn_window_end=db_fire_watch.burn_window_end.isoformat()
        if db_fire_watch.burn_window_end
        else None,
        burn_window_start=db_fire_watch.burn_window_start.isoformat()
        if db_fire_watch.burn_window_start
        else None,
        contact_email=db_fire_watch.contact_email,
        create_timestamp=db_fire_watch.create_timestamp.isoformat(),
        create_user=db_fire_watch.create_user,
        fire_centre=FireWatchFireCentre(id=fire_centre.id, name=fire_centre.name),
        station=fw_station,
        status=db_fire_watch.status,
        title=db_fire_watch.title,
        update_timestamp=db_fire_watch.update_timestamp.isoformat(),
        update_user=db_fire_watch.update_user,
        # Fuel parameters
        fuel_type=db_fire_watch.fuel_type,
        percent_conifer=db_fire_watch.percent_conifer,
        percent_dead_fir=db_fire_watch.percent_dead_fir,
        percent_grass_curing=db_fire_watch.percent_grass_curing,
        # Weather parameters
        temp_min=db_fire_watch.temp_min,
        temp_preferred=db_fire_watch.temp_preferred,
        temp_max=db_fire_watch.temp_max,
        rh_min=db_fire_watch.rh_min,
        rh_preferred=db_fire_watch.rh_preferred,
        rh_max=db_fire_watch.rh_max,
        wind_speed_min=db_fire_watch.wind_speed_min,
        wind_speed_preferred=db_fire_watch.wind_speed_preferred,
        wind_speed_max=db_fire_watch.wind_speed_max,
        # FWI and FBP parameters
        ffmc_min=db_fire_watch.ffmc_min,
        ffmc_preferred=db_fire_watch.ffmc_preferred,
        ffmc_max=db_fire_watch.ffmc_max,
        dmc_min=db_fire_watch.dmc_min,
        dmc_preferred=db_fire_watch.dmc_preferred,
        dmc_max=db_fire_watch.dmc_max,
        dc_min=db_fire_watch.dc_min,
        dc_preferred=db_fire_watch.dc_preferred,
        dc_max=db_fire_watch.dc_max,
        isi_min=db_fire_watch.isi_min,
        isi_preferred=db_fire_watch.isi_preferred,
        isi_max=db_fire_watch.isi_max,
        bui_min=db_fire_watch.bui_min,
        bui_preferred=db_fire_watch.bui_preferred,
        bui_max=db_fire_watch.bui_max,
        hfi_min=db_fire_watch.hfi_min,
        hfi_preferred=db_fire_watch.hfi_preferred,
        hfi_max=db_fire_watch.hfi_max,
    )


def create_burn_forecast_output(fire_watch_weather: FireWatchWeather, prescription: str):
    return BurnForecastOutput(
        id=fire_watch_weather.id,
        fire_watch_id=fire_watch_weather.fire_watch_id,
        date=fire_watch_weather.date.isoformat(),
        temp=fire_watch_weather.temperature,
        rh=fire_watch_weather.relative_humidity,
        wind_speed=fire_watch_weather.wind_speed,
        ffmc=fire_watch_weather.ffmc,
        dmc=fire_watch_weather.dmc,
        dc=fire_watch_weather.dc,
        isi=fire_watch_weather.isi,
        bui=fire_watch_weather.bui,
        hfi=fire_watch_weather.hfi,
        in_prescription=prescription,
    )


def create_fire_watch_burn_forecasts_response(
    stations: List[GeoJsonWeatherStation],
    fire_watches: Sequence[Row[Tuple[FireWatch, FireCentre]]],
    fire_watch_weather: Sequence[Row[Tuple[FireWatchWeather, str]]],
) -> FireWatchBurnForecastsResponse:
    # Build a dictionary of BurnForecastOutputs keyed by fire watch id for easy lookup
    fire_watch_weather_dict = defaultdict(list)
    for item, prescription in fire_watch_weather:
        fire_watch_weather_dict[item.fire_watch_id].append(
            create_burn_forecast_output(item, prescription)
        )
    fire_watch_burn_forecasts: List[FireWatchOutputBurnForecast] = []
    for fire_watch, fire_centre in fire_watches:
        fire_watch_output = create_fire_watch_output(fire_watch, fire_centre, stations)
        burn_forecast_outputs = fire_watch_weather_dict.get(fire_watch.id, [])
        burn_forecast_outputs.sort(key=lambda x: x.date)
        fire_watch_burn_forecasts.append(
            FireWatchOutputBurnForecast(
                fire_watch=fire_watch_output, burn_forecasts=burn_forecast_outputs
            )
        )
    return FireWatchBurnForecastsResponse(fire_watch_burn_forecasts=fire_watch_burn_forecasts)


@router.get("/", response_model=FireWatchListResponse)
async def get_fire_watches(_=Depends(authentication_required)):
    """Returns all FireWatch records"""
    logger.info("/fire-watch/")
    stations = await get_stations_as_geojson()
    async with get_async_read_session_scope() as session:
        results = await get_all_fire_watches(session)
        api_watch_list = []
        for fire_watch, fire_centre in results:
            if fire_watch is None or fire_centre is None:
                continue
            fire_watch_output = create_fire_watch_output(fire_watch, fire_centre, stations)
            api_watch_list.append(fire_watch_output)
    return FireWatchListResponse(watch_list=api_watch_list)


@router.post("/watch", response_model=FireWatchResponse, status_code=status.HTTP_201_CREATED)
async def save_new_fire_watch(
    fire_watch_input_request: FireWatchInputRequest, token=Depends(authentication_required)
):
    idir = token.get("idir_username", None)
    db_fire_watch = marshall_fire_watch_input_to_db(fire_watch_input_request.fire_watch, idir)
    stations = await get_stations_as_geojson()

    async with get_async_write_session_scope() as session:
        new_fire_watch_id = await save_fire_watch(session, db_fire_watch)
        fire_watch, fire_centre = await get_fire_watch_by_id(session, new_fire_watch_id)
        fire_watch_output = create_fire_watch_output(fire_watch, fire_centre, stations)
        return FireWatchResponse(fire_watch=fire_watch_output)


@router.patch("/watch/{fire_watch_id}", response_model=FireWatchBurnForecastsResponse)
async def update_existing_fire_watch(
    fire_watch_id: int,
    fire_watch_input_request: FireWatchInputRequest,
    token=Depends(authentication_required),
):
    idir = token.get("idir_username", None)
    fire_watch_input = marshall_fire_watch_input_to_db(fire_watch_input_request.fire_watch, idir)
    stations = await get_stations_as_geojson()

    async with get_async_write_session_scope() as session:
        # Check if FireWatch exists
        fire_watch = await get_fire_watch_by_id(session, fire_watch_id)
        if not fire_watch:
            raise HTTPException(status_code=404, detail=f"FireWatch {fire_watch_id} not found")
        updated_fire_watch = await update_fire_watch(session, fire_watch_id, fire_watch_input)

        latest_model_run_parameters_id = (
            await get_latest_processed_model_run_id_in_fire_watch_weather(session)
        )

        try:
            await reprocess_fire_watch_weather(
                session,
                updated_fire_watch,
                latest_model_run_parameters_id,
            )
        except MissingWeatherDataError as e:
            logger.error(f"Missing weather data: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Missing actual weather data for FireWatch {fire_watch_id}: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error reprocessing fire watch weather: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reprocess fire watch weather for FireWatch {fire_watch_id}: {str(e)}",
            )

        fire_watch_weather = await get_fire_watch_weather_by_model_with_prescription_status(
            session, updated_fire_watch.id, latest_model_run_parameters_id
        )

        updated_burn_forecast = create_fire_watch_burn_forecasts_response(
            stations, [fire_watch], fire_watch_weather
        )

        return updated_burn_forecast


@router.get("/fire-centres", response_model=FireWatchFireCentresResponse)
async def get_all_fire_centres(token=Depends(authentication_required)):
    logger.info("/fire-watch/fire-centres")
    async with get_async_read_session_scope() as session:
        result = await get_fire_centres(session)
        fire_centres = [FireWatchFireCentre(id=item.id, name=item.name) for item in result]
        return FireWatchFireCentresResponse(fire_centres=fire_centres)


@router.get("/burn-forecasts", response_model=FireWatchBurnForecastsResponse)
async def get_burn_forecasts(_=Depends(authentication_required)):
    logger.info("/fire-watch/burn-locations")
    stations = await get_stations_as_geojson()
    async with get_async_read_session_scope() as session:
        fire_watches = await get_all_fire_watches(session)
        latest_model_run_parameters_id = (
            await get_latest_processed_model_run_id_in_fire_watch_weather(session)
        )
        fire_watch_weather = await get_all_fire_watch_weather_with_prescription_status(
            session, latest_model_run_parameters_id
        )
        fire_watch_burn_forecasts_response = create_fire_watch_burn_forecasts_response(
            stations, fire_watches, fire_watch_weather
        )
        return fire_watch_burn_forecasts_response
