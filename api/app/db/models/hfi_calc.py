""" Class models that reflect resources and map to database tables for HFI Calculator.
"""
from sqlalchemy import (Column, Integer,
                        Sequence, ForeignKey, UniqueConstraint)
from sqlalchemy.sql.sqltypes import String
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

    id = Column(Integer, Sequence('planning_areas_id_seq'),
                primary_key=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    fire_centre_id = Column(Integer, ForeignKey('fire_centres.id'), nullable=False, index=True)

    def __str__(self):
        return (f'id:{self.id}, '
                f'name:{self.name}, '
                f'fire_centre_id:{self.fire_centre_id}')


class FuelType(Base):
    """ FBP System fuel types """
    __tablename__ = 'fuel_types'

    id = Column(Integer, Sequence('fuel_types_id_seq'), primary_key=True, nullable=False, index=True)
    abbrev = Column(String, nullable=False)
    description = Column(String)

    def __str__(self):
        return (f'id:{self.id}, '
                f'abbrev:{self.abbrev}, '
                f'description:{self.description}')


class PlanningWeatherStation(Base):
    """ Weather station within planning area selected as a representative of its associated planning area """
    __tablename__ = 'planning_weather_stations'
    __table_args__ = (
        UniqueConstraint('station_code'),
        {'comment': 'Identifies the unique code used to identify the station'}
    )

    id = Column(Integer, Sequence('planning_weather_station_id_seq'),
                primary_key=True, nullable=False, index=True)
    station_code = Column(Integer, nullable=False, index=True)
    station_name = Column(String, nullable=False)
    fuel_type_id = Column(Integer, ForeignKey('fuel_types.id'), nullable=False, index=True)
    planning_area_id = Column(Integer, ForeignKey('planning_areas.id'), nullable=False, index=True)
    elevation = Column(Integer, nullable=False)

    def __str__(self):
        return (f'id:{self.id}, '
                f'station_code:{self.station_code}, '
                f'station_name:{self.station_name}, '
                f'elevation:{self.elevation}, '
                f'fuel_type_id:{self.fuel_type_id}, '
                f'planning_area_id:{self.planning_area_id}')
