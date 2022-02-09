""" CRUD operations relating to HFI Calculator
"""
import logging
from typing import List
from datetime import date
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.orm import Session
from app.db.models.hfi_calc import (FireCentre, FuelType, PlanningArea, PlanningAreaSelectionOverride, PlanningWeatherStation,
                                    FireCentrePrepPeriod, PlanningAreaSelectionOverrideForDay)

logger = logging.getLogger(__name__)


def get_fire_weather_stations(session: Session) -> CursorResult:
    """ Get all PlanningWeatherStation with joined FuelType, PlanningArea and FireCentre
    for the provided list of station_codes. """
    return session.query(PlanningWeatherStation, FuelType, PlanningArea, FireCentre)\
        .join(FuelType, FuelType.id == PlanningWeatherStation.fuel_type_id)\
        .join(PlanningArea, PlanningArea.id == PlanningWeatherStation.planning_area_id)\
        .join(FireCentre, FireCentre.id == PlanningArea.fire_centre_id)\
        .order_by(FireCentre.name, PlanningArea.name)


def get_all_stations(session: Session) -> CursorResult:
    """ Get all known planning weather stations """
    return session.query(PlanningWeatherStation.station_code).all()


def get_stations_with_fuel_types(session: Session, station_codes: List[int]) -> CursorResult:
    """ Get all PlanningWeatherStations that match the supplied station codes
        and include their associated fuel types"""
    return session.query(PlanningWeatherStation, FuelType)\
        .filter(PlanningWeatherStation.station_code.in_(station_codes))\
        .join(FuelType, FuelType.id == PlanningWeatherStation.fuel_type_id)


def get_planning_area_overrides_for_day_in_period(session: Session,
                                                  prep_start_day: date,
                                                  prep_end_day: date) -> CursorResult:
    return session.query(PlanningAreaSelectionOverrideForDay).\
        filter(PlanningAreaSelectionOverrideForDay.day >= prep_start_day).\
        filter(PlanningAreaSelectionOverrideForDay.day <= prep_end_day)


def create_planning_area_selection_override_for_day(session: Session, planning_area_id: int, day: date,
                                                    fire_starts_min: int, fire_starts_max: int):
    override = PlanningAreaSelectionOverrideForDay(
        planning_area_id=planning_area_id,
        day=day,
        fire_starts_min=fire_starts_min,
        fire_starts_max=fire_starts_max)
    session.add(override)


def update_planning_area_selection_override_for_day(session: Session, override: PlanningAreaSelectionOverrideForDay):
    session.add(override)


def create_fire_centre_prep_period(session: Session,
                                   fire_centre_id: int,
                                   prep_start_day: date,
                                   prep_end_day: date):
    """ Create the fire centre prep period """
    prep_period = FireCentrePrepPeriod(fire_centre_id=fire_centre_id,
                                       prep_start_day=prep_start_day, prep_end_day=prep_end_day)
    session.add(prep_period)


def update_fire_centre_prep_period(session: Session,
                                   prep_period: FireCentrePrepPeriod):
    """ Update the fire centre prep period """
    session.add(prep_period)


def get_fire_centre_prep_period(session: Session,
                                fire_centre_id: int,
                                prep_start_day: date) -> FireCentrePrepPeriod:
    """ Get the fire centre prep period """
    return session.query(FireCentrePrepPeriod).\
        filter(FireCentrePrepPeriod.fire_centre_id == fire_centre_id).\
        filter(FireCentrePrepPeriod.prep_start_day == prep_start_day).\
        first()


def get_most_recent_fire_centre_prep_period(session: Session, fire_centre_id: int) -> FireCentrePrepPeriod:
    """ Get the most recent fire centre prep period """
    return session.query(FireCentrePrepPeriod).\
        filter(FireCentrePrepPeriod.fire_centre_id == fire_centre_id).\
        order_by(FireCentrePrepPeriod.prep_start_day.desc()).\
        first()


def get_fire_centre_planning_area_selection_overrides(session: Session, fire_centre_id: int) -> CursorResult:
    """ Get all the overrides for each planning area in a fire centre """
    return session.query(PlanningAreaSelectionOverride, FuelType).\
        join(PlanningArea, PlanningArea.id == PlanningAreaSelectionOverride.planning_area_id).\
        join(FireCentre, FireCentre.id == PlanningArea.fire_centre_id).\
        join(FuelType, FuelType.id == PlanningAreaSelectionOverride.fuel_type_id).\
        filter(FireCentre.id == fire_centre_id)


def create_planning_area_selection_override(session: Session,
                                            planning_area_id: int,
                                            station_id: int,
                                            fuel_type_id: int,
                                            station_selected: bool):
    override = PlanningAreaSelectionOverride(
        planning_area_id=planning_area_id,
        station_id=station_id,
        fuel_type_id=fuel_type_id,
        station_selected=station_selected)
    session.add(override)


def update_planning_area_selection_override(session: Session, override: PlanningAreaSelectionOverride):
    session.add(override)

# def get_planning_area_selection_overrides(session: Session):
#     """ Get all planning area selection overrides """
#     return session.query(PlanningArea.id, PlanningArea.name, PlanningArea.fire_centre_id)
