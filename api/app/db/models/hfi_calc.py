""" Class models that reflect resources and map to database tables for HFI Calculator.
"""
from sqlalchemy import (Column, Integer,
                        Sequence, ForeignKey, UniqueConstraint, null)
from sqlalchemy.sql.sqltypes import String, Date, Boolean
from app.db.database import Base


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
    __table_args__ = (UniqueConstraint('order_of_appearance_in_list', 'fire_centre_id',
                                       name='unique_list_order_for_fire_centre_constraint'), {
                      'comment':
                      'Only one planning area can be assigned a position in the list for a fire centre'})

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
    # The abbreviation should be unique - we don't want duplicate fuel types.
    abbrev = Column(String, nullable=False, index=True, unique=True)
    description = Column(String)

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
        {'comment': 'Identifies the unique code used to identify the station'}
    )

    id = Column(Integer, Sequence('planning_weather_station_id_seq'),
                primary_key=True, nullable=False, index=True)
    station_code = Column(Integer, nullable=False, index=True)
    fuel_type_id = Column(Integer, ForeignKey('fuel_types.id'), nullable=False, index=True)
    planning_area_id = Column(Integer, ForeignKey('planning_areas.id'), nullable=False, index=True)

    def __str__(self):
        return (f'id:{self.id}, '
                f'station_code:{self.station_code}, '
                f'fuel_type_id:{self.fuel_type_id}, '
                f'planning_area_id:{self.planning_area_id}')


class PlanningAreaSelectionOverrideForDay(Base):
    """ For a given day, in a given planning area, we may override the fire starts. """
    __tablename__ = 'hfi_calc_planning_area_selection_override_for_day'
    __table_args__ = (UniqueConstraint('planning_area_id', 'day',
                                       name='unique_planning_area_day_constraint'),
                      {'comment': 'Identifies the unique planning area + day combo to identify overrides'})
    id = Column(Integer, Sequence('hfi_calc_planning_area_selection_override_for_day_id_seq'),
                primary_key=True, nullable=False, index=True)
    planning_area_id = Column(Integer, ForeignKey('planning_areas.id'), nullable=False, index=True)
    day = Column(Date, nullable=False, index=True)
    fire_starts_min = Column(Integer, nullable=False)
    fire_starts_max = Column(Integer, nullable=False)


class PlanningAreaSelectionOverride(Base):
    """ For a given station, in a given planning area, we may override the fuel type, and station selected
    status. """
    __tablename__ = 'hfi_calc_planning_area_selection_override'
    __table_args__ = (UniqueConstraint('planning_area_id', 'station_id',
                                       name='unique_planning_area_station_code_constraint'),
                      {'comment': ("Identifies the unique planning area + station code combo to identify"
                                   " overrides")})
    id = Column(Integer, Sequence('hfi_calc_planning_area_selection_override_id_seq'),
                primary_key=True, nullable=False, index=True)
    planning_area_id = Column(Integer, ForeignKey('planning_areas.id'), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey('planning_weather_stations.id'), nullable=False, index=True)
    fuel_type_id = Column(Integer, ForeignKey('fuel_types.id'), nullable=False, index=True)
    station_selected = Column(Boolean, nullable=False)


class FireCentrePrepPeriod(Base):
    """ For a given Fire Centre, for a given prep start date, we may override the prep period. """
    __tablename__ = 'hfi_calc_fire_centre_prep_period'
    __table_args__ = (UniqueConstraint('fire_centre_id', 'prep_start_day',
                                       name='unique_fire_centre_prep_period'),
                      {'comment': 'Identifies the unique prep period for a fire centre'})
    id = Column(Integer, Sequence('hfi_calc_fire_centre_prep_period_id_seq'),
                primary_key=True, nullable=False, index=True)
    fire_centre_id = Column(Integer, ForeignKey('fire_centres.id'), nullable=False, index=True)
    prep_start_day = Column(Date, nullable=False, index=True)
    prep_end_day = Column(Date, nullable=False)
