""" CRUD operations relating to HFI Calculator
"""
from typing import List
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.orm import Session, joinedload
from app.db.models.hfi_calc import FireCentre, FuelType, PlanningArea, PlanningWeatherStation


def get_hydrated_planning_stations(session: Session) -> CursorResult:
    """ Get all PlanningWeatherStation with joined FuelType, PlanningArea and FireCentre
    for the provided list of station_codes. """
    return session.query(PlanningWeatherStation).options(
        joinedload(PlanningWeatherStation.planning_area).subqueryload(PlanningArea.fire_centre),
        joinedload(PlanningWeatherStation.fuel_type))


def get_all_stations(session: Session) -> CursorResult:
    """ Get all known planning weather stations """
    return session.query(PlanningWeatherStation.station_code).all()


def get_stations_with_fuel_types(session: Session, station_codes: List[int]) -> CursorResult:
    """ Get all PlanningWeatherStations that match the supplied station codes
        and include their associated fuel types"""
    return session.query(PlanningWeatherStation, FuelType)\
        .filter(PlanningWeatherStation.station_code.in_(station_codes))\
        .join(FuelType, FuelType.id == PlanningWeatherStation.fuel_type_id)
