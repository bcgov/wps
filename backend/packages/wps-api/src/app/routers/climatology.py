"""Routers for station climatology."""

import asyncio
import logging
from typing import Annotated

from aiohttp import ClientSession
from fastapi import APIRouter, Depends, Query, Request
from wps_shared.auth import audit, authentication_required
from wps_shared.schemas.climatology import (
    ClimatologyFireCentre,
    ClimatologyFireCentresResponse,
    ClimatologyMethod,
    ClimatologyStation,
    ClimatologyVariable,
    DailyClimatologyResponse,
)
from wps_shared.utils.time import get_utc_now
from wps_weather_data.by_station import ByStationTable
from wps_weather_data.by_time import ACTUALS, DAILY
from wps_wf1.wfwx_api import WfwxApi

from app.climatology.daily import daily_climatology

logger = logging.getLogger(__name__)

# The most stations one request can combine. A fire centre has fewer than this.
MAX_STATIONS = 150

router = APIRouter(
    prefix="/climatology",
    dependencies=[Depends(authentication_required), Depends(audit)],
)


def get_by_station_table(request: Request) -> ByStationTable:
    """The `by_station` table the app created at startup (see `lifespan` in app.main)."""
    return request.app.state.by_station_table


def _daily_climatology(
    by_station_table: ByStationTable,
    station_codes: list[int],
    variable: ClimatologyVariable,
    year: int,
    method: ClimatologyMethod,
) -> DailyClimatologyResponse:
    rows = by_station_table.read_stations(DAILY, station_codes, [ACTUALS])
    return daily_climatology(rows, station_codes, variable, year, method)


@router.get("/daily", response_model=DailyClimatologyResponse)
async def get_daily_climatology(
    station_codes: Annotated[list[int], Query(min_length=1, max_length=MAX_STATIONS)],
    variable: ClimatologyVariable = ClimatologyVariable.TEMPERATURE,
    year: int | None = None,
    method: ClimatologyMethod = ClimatologyMethod.AVERAGE,
    by_station_table: ByStationTable = Depends(get_by_station_table),
):
    """Returns how the stations' daily observations of a variable have been distributed on each
    day of the year, and their observations in `year` to compare: combined by `method`, or for
    each station. `year` is left out of the distribution and defaults to the current year.
    """
    logger.info("/climatology/daily for %d stations", len(station_codes))
    year = year or get_utc_now().year
    # The read blocks on the network, so it runs in a thread to keep the event loop free.
    return await asyncio.to_thread(
        _daily_climatology, by_station_table, station_codes, variable, year, method
    )


@router.get("/fire-centres", response_model=ClimatologyFireCentresResponse)
async def get_fire_centres():
    """Returns each fire centre with its stations and their fire zones, to choose stations by."""
    logger.info("/climatology/fire-centres")
    async with ClientSession() as session:
        fire_centres = await WfwxApi(session).get_fire_centers()
    return ClimatologyFireCentresResponse(
        fire_centres=sorted(
            (
                ClimatologyFireCentre(
                    id=int(centre.id),
                    name=centre.name,
                    stations=sorted(
                        (
                            ClimatologyStation(
                                code=station.code, name=station.name, zone=station.zone
                            )
                            for station in centre.stations or []
                        ),
                        key=lambda station: station.name,
                    ),
                )
                for centre in fire_centres
            ),
            key=lambda centre: centre.name,
        )
    )
