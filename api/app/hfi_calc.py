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


async def _fetch_fire_centres_from_db():
    """ Fetch a list of all fire centres. """
    with app.db.database.get_read_session_scope() as session:
        return get_fire_centres(session)


async def fetch_fire_centre_by_id(id: int):
    with app.db.database.get_read_session_scope() as session:
        return get_fire_centre_by_id(session, id)


async def fetch_fuel_types_from_db():
    with app.db.database.get_read_session_scope() as session:
        return get_fuel_types(session)


async def fetch_fuel_type_by_id(id: int):
    with app.db.database.get_read_session_scope() as session:
        return get_fuel_type_by_id(session, id)


async def fetch_planning_area_by_id(id: int):
    with app.db.database.get_read_session_scope() as session:
        return get_planning_area_by_id(session, id)


async def _fetch_planning_areas_from_db(session: Session):
    """ Fetch a list of all planning areas that should appear in the HFI Calculator worksheet
    (across all fire centres). """
    return get_planning_areas(session)


async def fetch_hfi_station_data():
    """  """
    with app.db.database.get_read_session_scope() as session:
        stations = get_planning_weather_stations(session)
    print(stations)
    return stations
