""" CRUD operations relating to HFI Calculator
"""
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.orm import Session
from app.db.models.hfi_calc import FireCentre, FuelType, PlanningArea, PlanningWeatherStation


def get_fire_weather_stations(session: Session) -> CursorResult:
    """ Get all PlanningWeatherStation with joined FuelType, PlanningArea and FireCentre
    for the provided list of station_codes. """
    return session.query(PlanningWeatherStation, FuelType, PlanningArea, FireCentre)\
        .join(FuelType, FuelType.id == PlanningWeatherStation.fuel_type_id)\
        .join(PlanningArea, PlanningArea.id == PlanningWeatherStation.planning_area_id)\
        .join(FireCentre, FireCentre.id == PlanningArea.fire_centre_id)\
        .order_by(FireCentre.name, PlanningArea.name)
