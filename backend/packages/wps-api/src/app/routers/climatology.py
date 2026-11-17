"""Routers for station climatology."""

import asyncio
import logging

from fastapi import APIRouter, Depends, Request
from wps_shared.auth import audit, authentication_required
from wps_shared.schemas.climatology import ClimatologyVariable, DailyClimatologyResponse
from wps_shared.utils.time import get_utc_now
from wps_weather_data.by_station import ByStationTable
from wps_weather_data.by_time import ACTUALS, DAILY

from app.climatology.daily import daily_climatology

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/climatology",
    dependencies=[Depends(authentication_required), Depends(audit)],
)


def get_by_station_table(request: Request) -> ByStationTable:
    """The `by_station` table the app created at startup (see `lifespan` in app.main)."""
    return request.app.state.by_station_table


def _daily_climatology(
    by_station_table: ByStationTable, station_code: int, variable: ClimatologyVariable, year: int
) -> DailyClimatologyResponse:
    rows = by_station_table.read(DAILY, station_code, [ACTUALS])
    return daily_climatology(rows, station_code, variable, year)


@router.get("/stations/{station_code}/daily", response_model=DailyClimatologyResponse)
async def get_daily_climatology(
    station_code: int,
    variable: ClimatologyVariable = ClimatologyVariable.TEMPERATURE,
    year: int | None = None,
    by_station_table: ByStationTable = Depends(get_by_station_table),
):
    """Returns how a station's daily observations of a variable have been distributed on each
    day of the year, and its observations in `year` to compare. `year` is left out of the
    distribution and defaults to the current year.
    """
    logger.info("/climatology/stations/%s/daily", station_code)
    year = year or get_utc_now().year
    # The read blocks on the network, so it runs in a thread to keep the event loop free.
    return await asyncio.to_thread(
        _daily_climatology, by_station_table, station_code, variable, year
    )
