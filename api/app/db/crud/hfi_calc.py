""" CRUD operations relating to HFI Calculator
"""
from typing import List
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.orm import Session
from sqlalchemy import desc, insert
from app.db.database import get_read_session_scope
from app.schemas.hfi_calc import DateRange, HFIResultRequest
from app.db.models.hfi_calc import (FireCentre, FuelType, HFIReady, PlanningArea, PlanningWeatherStation, HFIRequest,
                                    FireStartRange, FireCentreFireStartRange, FireStartLookup)
from app.utils.time import get_utc_now


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


def get_fire_centre_station_codes() -> List[int]:
    """ Retrieves station codes for fire centers
    """
    station_codes = []
    with get_read_session_scope() as session:
        station_query = get_all_stations(session)
        for station in station_query:
            station_codes.append(int(station['station_code']))

    return station_codes


def get_fire_centre_stations(session, fire_centre_id: int) -> CursorResult:
    """ Get all the stations, along with default fuel type for a fire centre. """
    return session.query(PlanningWeatherStation, FuelType)\
        .join(PlanningArea, PlanningArea.id == PlanningWeatherStation.planning_area_id)\
        .join(FuelType, FuelType.id == PlanningWeatherStation.fuel_type_id)\
        .filter(PlanningArea.fire_centre_id == fire_centre_id)


def get_planning_weather_stations(session, fire_centre_id: int) -> List[PlanningWeatherStation]:
    """ Get all the stations for a fire centre. """
    return session.query(PlanningWeatherStation)\
        .join(PlanningArea, PlanningArea.id == PlanningWeatherStation.planning_area_id)\
        .filter(PlanningArea.fire_centre_id == fire_centre_id).all()


def get_most_recent_updated_hfi_request(session: Session,
                                        fire_centre_id: int,
                                        date_range: DateRange) -> HFIRequest:
    """ Get the most recently updated hfi request for a fire centre """
    query = session.query(HFIRequest)\
        .filter(HFIRequest.fire_centre_id == fire_centre_id)\
        .filter(HFIRequest.prep_start_day == date_range.start_date)\
        .filter(HFIRequest.prep_end_day == date_range.end_date)
    return query.order_by(HFIRequest.create_timestamp.desc()).first()


def get_most_recent_updated_hfi_request_for_current_date(session: Session,
                                                         fire_centre_id: int) -> HFIRequest:
    """ Get the most recently updated hfi request within some date range, for a fire centre """
    now = get_utc_now().date()
    query = session.query(HFIRequest)\
        .filter(HFIRequest.fire_centre_id == fire_centre_id)\
        .filter(HFIRequest.prep_start_day <= now)\
        .filter(HFIRequest.prep_end_day >= now)
    return query.order_by(HFIRequest.create_timestamp.desc()).first()


def store_hfi_request(session: Session, hfi_result_request: HFIResultRequest, username: str):
    """ Store the supplied hfi request """
    previous_latest_request = get_most_recent_updated_hfi_request(
        session,
        fire_centre_id=hfi_result_request.selected_fire_center_id,
        date_range=hfi_result_request.date_range)
    stmt = (
        insert(HFIRequest).values(fire_centre_id=hfi_result_request.selected_fire_center_id,
                                  prep_start_day=hfi_result_request.date_range.start_date,
                                  prep_end_day=hfi_result_request.date_range.end_date,
                                  create_timestamp=get_utc_now(),
                                  create_user=username,
                                  request=hfi_result_request.json()).returning(HFIRequest.id)
    )
    res = session.execute(stmt).fetchone()
    latest_hfi_request_id = res.id
    now = get_utc_now()

    if previous_latest_request is not None:
        # Copy over ready records for existing hfi request
        latest_hfi_ready_records = get_latest_hfi_ready_records(session, previous_latest_request.id)
        updated_hfi_ready_records = []
        for latest_hfi_ready_record in latest_hfi_ready_records:
            updated_hfi_ready_records.append(HFIReady(hfi_request_id=latest_hfi_request_id,
                                                      planning_area_id=latest_hfi_ready_record.planning_area_id,
                                                      ready=latest_hfi_ready_record.ready,
                                                      create_timestamp=latest_hfi_ready_record.create_timestamp,
                                                      create_user=latest_hfi_ready_record.create_user,
                                                      update_timestamp=now,
                                                      update_user=username))
        session.bulk_save_objects(updated_hfi_ready_records)
    else:
        # Create ready records for new hfi request
        planning_areas = get_planning_areas(session, hfi_result_request.selected_fire_center_id)
        new_hfi_ready_records = []
        for planning_area in planning_areas:
            new_hfi_ready_records.append(HFIReady(hfi_request_id=latest_hfi_request_id,
                                                  planning_area_id=planning_area.id,
                                                  ready=False,
                                                  create_timestamp=now,
                                                  create_user=username,
                                                  update_timestamp=now,
                                                  update_user=username))
        session.bulk_save_objects(new_hfi_ready_records)


def get_latest_hfi_ready_records(session: Session, hfi_request_id: int) -> List[HFIReady]:
    """ Retrieve the latest hfi ready records for each distinct planning area in a hfi request """
    return session.query(HFIReady)\
        .filter(HFIReady.hfi_request_id == hfi_request_id)\
        .all()


def get_planning_areas(session: Session, fire_centre_id: int):
    """ Retrieve the planning areas for a fire centre"""
    return session.query(PlanningArea)\
        .filter(PlanningArea.fire_centre_id == fire_centre_id)\
        .all()


def add_hfi_station(session: Session, station_code: int, fuel_type_id: int, planning_area_id: int, order: int, username: str):
    """ Add planning weather station """
    now = get_utc_now()
    planning_weather_station = PlanningWeatherStation(station_code=station_code,
                                                      fuel_type_id=fuel_type_id,
                                                      planning_area_id=planning_area_id,
                                                      order_of_appearance_in_planning_area_list=order,
                                                      create_user=username,
                                                      update_user=username,
                                                      create_timestamp=now,
                                                      update_timestamp=now,
                                                      is_deleted=False)
    session.add(planning_weather_station)
    session.commit()


def remove_hfi_station(session: Session, station_code: int, planning_area_id: int, username: str):
    """ Remove planning weather station """
    now = get_utc_now()
    planning_weather_station = session.query(PlanningWeatherStation)\
        .filter(PlanningWeatherStation.station_code == station_code)\
        .filter(PlanningWeatherStation.planning_area_id == planning_area_id)\
        .first()
    position = planning_weather_station.order_of_appearance_in_planning_area_list
    planning_weather_station.is_deleted = True
    planning_weather_station.order_of_appearance_in_planning_area_list = None
    planning_weather_station.update_username = username
    planning_weather_station.update_timestamp = now
    all_stations_in_planning_area = session.query(PlanningWeatherStation)\
        .filter(PlanningWeatherStation.planning_area_id == planning_area_id)\
        .all()
    for station in all_stations_in_planning_area:
        if station.order_of_appearance_in_planning_area_list > position:
            station.order_of_appearance_in_planning_area_list -= 1
    session.commit()


def toggle_ready(session: Session,
                 fire_centre_id: int,
                 planning_area_id: int,
                 date_range: DateRange,
                 username: str) -> HFIReady:
    """ Toggles the planning area ready state for an hfi request """
    now = get_utc_now()
    hfi_request = get_most_recent_updated_hfi_request(session, fire_centre_id, date_range)
    ready_state: HFIReady = session.query(HFIReady)\
        .filter(HFIReady.planning_area_id == planning_area_id)\
        .filter(HFIReady.hfi_request_id == hfi_request.id)\
        .first()
    if ready_state.ready is True:
        ready_state.ready = False
    else:
        ready_state.ready = True
    ready_state.update_timestamp = now
    ready_state.update_user = username
    session.add(ready_state)
    session.commit()
    return ready_state


def get_last_station_in_planning_area(session: Session, planning_area_id: int) -> PlanningWeatherStation:
    """ Get the last station in a planning area """
    return session.query(PlanningWeatherStation)\
        .filter(PlanningWeatherStation.planning_area_id == planning_area_id)\
        .order_by(desc(PlanningWeatherStation.order_of_appearance_in_planning_area_list))\
        .first()


def get_fire_centre_fire_start_ranges(session: Session, fire_centre_id: id) -> CursorResult:
    """ Get the fire start ranges for a fire centre """
    return session.query(FireStartRange)\
        .join(FireCentreFireStartRange, FireCentreFireStartRange.fire_start_range_id == FireStartRange.id)\
        .filter(FireCentreFireStartRange.fire_centre_id == fire_centre_id)\
        .order_by(FireCentreFireStartRange.order)


def get_fire_start_lookup(session: Session) -> CursorResult:
    """ Get the fire start lookup table """
    return session.query(FireStartLookup)


def get_fuel_types(session: Session) -> CursorResult:
    """ Get the fuel types table  """
    return session.query(FuelType).order_by(FuelType.abbrev)


def get_fuel_type_by_id(session: Session, fuel_type_id: int) -> FuelType:
    """ Get the fuel type for the supplied fuel type id """
    return session.query(FuelType).filter(FuelType.id == fuel_type_id).first()
