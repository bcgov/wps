import logging
from typing import List
from aiohttp import ClientSession
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, status
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from shapely import from_wkt
from wps_shared.auth import audit, authentication_required
from wps_shared.db.crud.fire_watch import get_all_active_fire_watches, get_fire_centre_by_name, get_fire_watch_by_id, save_fire_watch
from wps_shared.db.database import get_async_read_session_scope, get_async_write_session_scope
from wps_shared.db.models.fire_watch import BurnStatusEnum, FireWatch as DBFireWatch
from wps_shared.fuel_types import FuelTypeEnum
from wps_shared.schemas.fire_watch import FireWatchInput, FireWatchOutput, FireWatchListResponse, FireWatchResponse
from wps_shared.utils.time import get_utc_now


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fire-watch",
    dependencies=[Depends(authentication_required), Depends(audit)],
)


async def get_fire_centre_id_by_name(name: str):
    async with ClientSession as session:
        result = await get_fire_centre_by_name(session, name)
        return result.id


def marshall_fire_watch_input_to_db(fire_watch_input: FireWatchInput, idir_username: str) -> DBFireWatch:
    now = get_utc_now()
    db_fire_watch = DBFireWatch(
        burn_location=f"POINT({fire_watch_input.burn_location[0]} {fire_watch_input.burn_location[1]})",
        burn_window_end=datetime.fromtimestamp(fire_watch_input.burn_window_end, UTC),
        burn_window_start=datetime.fromtimestamp(fire_watch_input.burn_window_start, UTC),
        contact_email=fire_watch_input.contact_email,
        create_timestamp=now,
        create_user=idir_username,
        fire_centre=fire_watch_input.fire_centre,
        station_code=fire_watch_input.station_code,
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


def get_cordinates_from_geometry(geometry) -> List[float]:
    if isinstance(geometry, str):
        return from_wkt(geometry)
    elif isinstance(geometry, WKBElement):
        return to_shape(geometry)
    raise TypeError("Unrecognized geometry type.")


def marshall_fire_watch_db_to_api(db_fire_watch: DBFireWatch) -> FireWatchOutput:
    location = get_cordinates_from_geometry(db_fire_watch.burn_location)
    coords = location.coords[0]
    return FireWatchOutput(
        id=db_fire_watch.id,
        burn_location=[coords[0], coords[1]],
        burn_window_end=int(db_fire_watch.burn_window_end.timestamp()),
        burn_window_start=int(db_fire_watch.burn_window_end.timestamp()),
        contact_email=db_fire_watch.contact_email,
        create_timestamp=int(db_fire_watch.create_timestamp.timestamp()),
        create_user=db_fire_watch.create_user,
        fire_centre=db_fire_watch.fire_centre,
        station_code=db_fire_watch.station_code,
        status=db_fire_watch.status,
        title=db_fire_watch.title,
        update_timestamp=int(db_fire_watch.update_timestamp.timestamp()),
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


def marshal_watch_list(watch_list: List[DBFireWatch]) -> List[FireWatchOutput]:
    api_watch_list: List[FireWatchOutput] = []
    for db_fire_watch in watch_list:
        api_fire_watch = marshall_fire_watch_db_to_api(db_fire_watch)
        api_watch_list.append(api_fire_watch)
    return api_watch_list


@router.get("/active", response_model=FireWatchListResponse)
async def get_all_fire_watches(_=Depends(authentication_required)):
    """Returns all active fire watch records."""
    logger.info("/fire-watch/active")
    async with get_async_read_session_scope() as session:
        db_watch_list = await get_all_active_fire_watches(session)
        api_watch_list = marshal_watch_list(db_watch_list)
    return FireWatchListResponse(watch_list=api_watch_list)


@router.post("/watch", response_model=FireWatchResponse, status_code=status.HTTP_201_CREATED)
async def save_new_fire_watch(fire_watch_input: FireWatchInput, token=Depends(authentication_required)):
    idir = token.get("idir_username", None)
    db_fire_watch = marshall_fire_watch_input_to_db(fire_watch_input, idir)
    async with get_async_write_session_scope() as session:
        new_fire_watch_id = await save_fire_watch(session, db_fire_watch)
        new_fire_watch = await get_fire_watch_by_id(session, new_fire_watch_id)
        fire_watch_output = marshall_fire_watch_db_to_api(new_fire_watch)
        return FireWatchResponse(fire_watch=fire_watch_output)
