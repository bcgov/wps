""" CRUD operations relating to HFI Calculator
"""
import datetime
from typing import List
from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.db.models.hfi_calc import FireCentre, FuelType, PlanningArea, PlanningWeatherStation


def get_fire_centres(
        session: Session):
    """ Query for all fire centres in database.
    """
    return session.query(FireCentre)


def get_fire_centre_by_id(session: Session, id: int):
    """ Query to return a specific fire centre identified by the id number provided. """
    return session.query(FireCentre).filter(FireCentre.id == id).first()


def get_planning_areas(session: Session):
    """ Query for all planning areas in database. """
    return session.query(PlanningArea)


def get_planning_area_by_id(session: Session, id: int):
    """ Query to return a specific planning area based on the id provided. """
    return session.query(PlanningArea).filter(PlanningArea.id == id).first()


def get_planning_weather_stations(session: Session):
    """ Query for all planning weather stations in database. """
    return session.query(PlanningWeatherStation).all()


def get_fuel_types(session: Session):
    """ Query for all fuel types in database. """
    return session.query(FuelType).all()


def get_fuel_type_by_id(session: Session, id: int):
    """ Query to return a specific fuel type based on the id provided. """
    return session.query(FuelType).filter(FuelType.id == id).first()
