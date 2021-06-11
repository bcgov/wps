""" Get stations, planning areas, and fire centres for HFI calculator
"""
import logging
import app.db.database
from app.db.crud.hfi_calc import get_fire_centre_by_id,\
    get_fuel_type_by_id,\
    get_planning_area_by_id,\
    get_planning_weather_stations

logger = logging.getLogger(__name__)


async def fetch_fire_centre_by_id(fire_centre_id: int):
    """ Fetches and returns FireCentre object identified by id """
    with app.db.database.get_read_session_scope() as session:
        return get_fire_centre_by_id(session, fire_centre_id)


async def fetch_fuel_type_by_id(fuel_type_id: int):
    """ Fetches and returns FuelType object identified by id. """
    with app.db.database.get_read_session_scope() as session:
        return get_fuel_type_by_id(session, fuel_type_id)


async def fetch_planning_area_by_id(planning_area_id: int):
    """ Fetches and returns PlanningArea object identified by id. """
    with app.db.database.get_read_session_scope() as session:
        return get_planning_area_by_id(session, planning_area_id)


async def fetch_hfi_station_data():
    """ Fetch all station data relevant to HFI Calculator, including station's planning area
    and fire centre, and station-specific info such as assigned fuel type and elevation. """
    with app.db.database.get_read_session_scope() as session:
        stations = get_planning_weather_stations(session)
    return stations
