""" This module contains functions related to hfi calculator.
"""

from typing import List
from app.db.crud.hfi_calc import get_all_stations
from app.db.database import get_read_session_scope


def get_fire_centre_station_codes() -> List[int]:
    """ Retrieves station codes for fire centers
    """
    station_codes = []
    with get_read_session_scope() as session:
        station_query = get_all_stations(session)
        for station in station_query:
            station_codes.append(int(station['station_code']))

    return station_codes
