""" CRUD operations relating to HFI Calculator
"""
from typing import List
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.orm import Session
from sqlalchemy import desc, insert, update
from app.db.database import get_read_session_scope
from app.schemas.hfi_calc import DateRange, HFIAdminRemovedStation, HFIAdminStationUpdateRequest, HFIResultRequest
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
        .filter(PlanningWeatherStation.is_deleted is False)


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
        .filter(PlanningWeatherStation.is_deleted is False)\
        .filter(PlanningArea.fire_centre_id == fire_centre_id)


def get_planning_weather_stations(session, fire_centre_id: int) -> List[PlanningWeatherStation]:
    """ Get all the stations for a fire centre. """
    return session.query(PlanningWeatherStation)\
        .join(PlanningArea, PlanningArea.id == PlanningWeatherStation.planning_area_id)\
        .filter(PlanningArea.fire_centre_id == fire_centre_id)\
        .filter(PlanningWeatherStation.is_deleted is False)\
        .all()


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


def get_last_station_in_planning_area(session: Session, planning_area_id: int) -> PlanningWeatherStation:
    """ Get the last station in a planning area """
    return session.query(PlanningWeatherStation)\
        .filter(PlanningWeatherStation.planning_area_id == planning_area_id)\
        .filter(PlanningWeatherStation.is_deleted is False)\
        .order_by(desc(PlanningWeatherStation.order_of_appearance_in_planning_area_list))\
        .first()


def get_planning_areas(session: Session, fire_centre_id: int):
    """ Retrieve the planning areas for a fire centre"""
    return session.query(PlanningArea)\
        .filter(PlanningArea.fire_centre_id == fire_centre_id)\
        .all()


def get_stations_for_removal(session: Session,
                             station_requests: List[HFIAdminRemovedStation]):
    """ Returns the station model requested to remove, along with all
    stations in in planning area, in ascending order. """
    remove_request_planning_area_ids = [request.planning_area_id for request in station_requests]
    remove_request_station_codes = [request.station_code for request in station_requests]

    # ordering is 1-based, row_id is 0-based
    remove_request_orders = [request.row_id + 1 for request in station_requests]

    stations_to_remove = session.query(PlanningWeatherStation)\
        .filter(PlanningWeatherStation.planning_area_id.in_(remove_request_planning_area_ids))\
        .filter(PlanningWeatherStation.station_code.in_(remove_request_station_codes))\
        .filter(PlanningWeatherStation.order_of_appearance_in_planning_area_list.in_(remove_request_orders))\
        .all()
    return stations_to_remove


def get_stations_for_affected_planning_areas(session: Session, request: HFIAdminStationUpdateRequest):
    removed_planning_area_ids = [remove_request.planning_area_id for remove_request in request.removed]
    added_planning_area_ids = [add_request.planning_area_id for add_request in request.added]
    affected_planning_area_ids = removed_planning_area_ids + added_planning_area_ids

    return session.query(PlanningWeatherStation)\
        .filter(PlanningWeatherStation.planning_area_id.in_(affected_planning_area_ids))\
        .filter(PlanningWeatherStation.is_deleted is False)\
        .order_by(PlanningWeatherStation.order_of_appearance_in_planning_area_list)\
        .all()


def unready_planning_areas(session: Session,
                           fire_centre_id: int,
                           username: str,
                           planning_area_ids):
    now = get_utc_now()
    query = update(HFIReady).values(
        {HFIReady.ready: False, HFIReady.update_user: username, HFIReady.update_timestamp: now})\
        .where(HFIReady.planning_area_id.in_(planning_area_ids))\
        .where(HFIReady.hfi_request_id == HFIRequest.id)\
        .where(HFIRequest.fire_centre_id == fire_centre_id)\
        .execution_options(synchronize_session="fetch")
    session.execute(query)


def save_hfi_stations(session: Session,
                      stations_to_save: List[PlanningWeatherStation]):

    session.bulk_save_objects(stations_to_save)
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
