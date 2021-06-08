""" Get stations, planning areas, and fire centres for HFI calculator 
"""
from datetime import datetime
import math
import asyncio
import logging
from typing import List, Final
import json
from sqlalchemy.engine.row import Row
from sqlalchemy.orm.session import Session
import app.db.database
from app.db.crud.hfi_calc import get_fire_centre_by_id, get_fire_centres, get_fuel_type_by_id, get_planning_area_by_id, get_planning_areas, get_planning_weather_stations, get_fuel_types

logger = logging.getLogger(__name__)


async def fetch_fire_centre_by_id(id: int):
    with app.db.database.get_read_session_scope() as session:
        return get_fire_centre_by_id(session, id)


async def fetch_fuel_type_by_id(id: int):
    with app.db.database.get_read_session_scope() as session:
        return get_fuel_type_by_id(session, id)


async def fetch_planning_area_by_id(id: int):
    with app.db.database.get_read_session_scope() as session:
        return get_planning_area_by_id(session, id)


async def fetch_hfi_station_data():
    """ Fetch all station data relevant to HFI Calculator, including station's planning area
    and fire centre, and station-specific info such as assigned fuel type and elevation. """
    with app.db.database.get_read_session_scope() as session:
        stations = get_planning_weather_stations(session)
    return stations
