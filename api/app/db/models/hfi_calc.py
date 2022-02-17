""" Class models that reflect resources and map to database tables for HFI Calculator.
"""
from sqlalchemy import (Column, Integer,
                        Sequence, ForeignKey, UniqueConstraint)
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.sqltypes import String, Date, JSON
from app.db.database import Base
from app.db.models.common import TZTimeStamp


class FireCentre(Base):
    """ BC Wildfire Service Fire Centre """
    __tablename__ = 'fire_centres'

    id = Column(Integer, Sequence('fire_centres_id_seq'),
                primary_key=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)

    def __str__(self):
        return (f'id:{self.id}, '
                f'name:{self.name}')


class PlanningArea(Base):
    """ Wildfire prep planning area within a fire centre """
    __tablename__ = 'planning_areas'
    __table_args__ = (UniqueConstraint('order_of_appearance_in_list', 'fire_centre_id', name='unique_list_order_for_fire_centre_constraint'), {
                      'comment': 'Only one planning area can be assigned a position in the list for a fire centre'})

    id = Column(Integer, Sequence('planning_areas_id_seq'),
                primary_key=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    fire_centre_id = Column(Integer, ForeignKey('fire_centres.id'), nullable=False, index=True)
    order_of_appearance_in_list = Column(Integer, nullable=False)

    def __str__(self):
        return (f'id:{self.id}, '
                f'name:{self.name}, '
                f'fire_centre_id:{self.fire_centre_id}')


class FuelType(Base):
    """ FBP System fuel types """
    __tablename__ = 'fuel_types'

    id = Column(Integer, Sequence('fuel_types_id_seq'), primary_key=True, nullable=False, index=True)
    abbrev = Column(String, nullable=False, index=True)
    description = Column(String)
    percentage_conifer = Column(Integer, nullable=True)
    percentage_dead_fir = Column(Integer, nullable=True)

    def __str__(self):
        return (f'id:{self.id}, '
                f'abbrev:{self.abbrev}, '
                f'description:{self.description}')


class PlanningWeatherStation(Base):
    """ Weather station within planning area selected as a representative of its associated planning area """
    __tablename__ = 'planning_weather_stations'
    __table_args__ = (
        UniqueConstraint('station_code', 'planning_area_id',
                         name='unique_station_code_for_planning_area'),
        UniqueConstraint('order_of_appearance_in_planning_area_list', 'planning_area_id', name='unique_order_for_planning_area'),
        {'comment': 'Identifies the unique code used to identify the station'}
    )

    id = Column(Integer, Sequence('planning_weather_station_id_seq'),
                primary_key=True, nullable=False, index=True)
    station_code = Column(Integer, nullable=False, index=True)
    fuel_type_id = Column(Integer, ForeignKey('fuel_types.id'), nullable=False, index=True)
    planning_area_id = Column(Integer, ForeignKey('planning_areas.id'), nullable=False, index=True)
    order_of_appearance_in_planning_area_list = Column(Integer, nullable=True)

    def __str__(self):
        return (f'id:{self.id}, '
                f'station_code:{self.station_code}, '
                f'fuel_type_id:{self.fuel_type_id}, '
                f'planning_area_id:{self.planning_area_id}')


class HFIRequest(Base):
    """ """
    __tablename__ = 'hfi_request'
    __table_args__ = (
        UniqueConstraint('fire_centre_id', 'prep_start_day', 'prep_end_day', 'create_timestamp',
                         name='unique_request_create_timestamp_for_fire_centre'),
        {'comment': 'Identifies the unique code used to identify the station'}
    )
    id = Column(Integer, primary_key=True)
    fire_centre_id = Column(Integer, ForeignKey('fire_centres.id'), nullable=False, index=True)
    # We use prep start and end date to load a planning area.
    prep_start_day = Column(Date, nullable=False, index=True)
    prep_end_day = Column(Date, nullable=False, index=True)
    # We use the create timestamp to grab the most recent request. (Old records kept for audit purposes)
    create_timestamp = Column(TZTimeStamp, nullable=False, index=True)
    # We keep track of users for auditing.
    create_user = Column(String, nullable=False)
    # NOTE: If the structure of the request changes, the stored request may not longer remain compatible.
    request = Column(JSON)
