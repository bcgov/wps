""" Class models that reflect resources and map to database tables for HFI Calculator.
"""
import uuid
from sqlalchemy import (Boolean, Column, Integer,
                        Sequence, ForeignKey, UniqueConstraint, Index)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.sqltypes import String, Date, JSON
from db.database import Base
from db.models.common import TZTimeStamp


FIRE_CENTRES_ID = 'fire_centres.id'
HFI_REQUEST_ID = 'hfi_request.id'
PLANNING_AREAS_ID = 'planning_areas.id'


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
    fire_centre_id = Column(Integer, ForeignKey(FIRE_CENTRES_ID), nullable=False, index=True)
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
    fuel_type_code = Column(String, nullable=True)
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
        UniqueConstraint('order_of_appearance_in_planning_area_list',
                         'planning_area_id', name='unique_order_for_planning_area'),
        Index('unique_non_deleted_station_per_planning_area',
              'is_deleted', 'station_code', 'planning_area_id',
              unique=True,
              postgresql_where=('not is_deleted')),
        {'comment': 'Identifies the unique code used to identify the station'}
    )

    id = Column(Integer, primary_key=True)
    station_code = Column(Integer, nullable=False, index=True)
    fuel_type_id = Column(Integer, ForeignKey('fuel_types.id'), nullable=False, index=True)
    planning_area_id = Column(Integer, ForeignKey('planning_areas.id'), nullable=False, index=True)
    order_of_appearance_in_planning_area_list = Column(Integer, nullable=True)
    # Track which user created the record for auditing purposes.
    create_user = Column(String, nullable=False)
    create_timestamp = Column(TZTimeStamp, nullable=False)
    # Track which user updated/deleted the record for auditing purposes.
    update_user = Column(String, nullable=False)
    update_timestamp = Column(TZTimeStamp, nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)

    def __str__(self):
        return (f'id:{self.id}, '
                f'station_code:{self.station_code}, '
                f'fuel_type_id:{self.fuel_type_id}, '
                f'planning_area_id:{self.planning_area_id}, '
                f'is_deleted:{self.is_deleted}')


class HFIRequest(Base):
    """ HFI Request Record """
    __tablename__ = 'hfi_request'
    __table_args__ = (
        UniqueConstraint('fire_centre_id', 'prep_start_day', 'prep_end_day', 'create_timestamp',
                         name='unique_request_create_timestamp_for_fire_centre'),
        {'comment': 'Identifies the unique code used to identify the station'}
    )
    id = Column(Integer, primary_key=True)
    fire_centre_id = Column(Integer, ForeignKey(FIRE_CENTRES_ID), nullable=False, index=True)
    # We use prep start and end date to load a planning area.
    prep_start_day = Column(Date, nullable=False, index=True)
    prep_end_day = Column(Date, nullable=False, index=True)
    # We use the create timestamp to grab the most recent request. (Old records kept for audit purposes)
    create_timestamp = Column(TZTimeStamp, nullable=False, index=True)
    # We keep track of users for auditing.
    create_user = Column(String, nullable=False)
    # NOTE: If the structure of the request changes, the stored request may not longer remain compatible.
    request = Column(JSON)


class HFIReady(Base):
    """ HFI ready status of a planning area in a HFI request """
    __tablename__ = 'hfi_ready'
    __table_args__ = (
        {'comment': 'Marks whether a planning area is ready for a particular HFI Request'}
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hfi_request_id = Column(Integer, ForeignKey(HFI_REQUEST_ID), nullable=False, index=True)
    planning_area_id = Column(Integer, ForeignKey(PLANNING_AREAS_ID), nullable=False, index=True)
    ready = Column(Boolean, nullable=False, default=False, index=True)
    create_timestamp = Column(TZTimeStamp, nullable=False, index=True)
    create_user = Column(String, nullable=False)
    update_timestamp = Column(TZTimeStamp, nullable=False, index=True)
    update_user = Column(String, nullable=False)


class FireStartRange(Base):
    """ A range of fire starts, described by a label. E.g. "3-5" or "15+"
    The range need not be stored in terms of "start" and "end" - a label is sufficient, as the lower
    and upper bound aren't used in calculations.

    The fire start range is associated with a fire centre, and a mean intensity -> prep level lookup.
    """
    __tablename__ = 'hfi_fire_start_range'
    __table_args__ = (
        {'comment': 'Fire start range'}
    )
    id = Column(Integer, primary_key=True)
    label = Column(String, nullable=False)


class FireStartLookup(Base):
    """ Map mean intensity group to prep level for a fire start range.

    Given a fire start range, the mean intensity group can be used to find the prep level.
    """
    __tablename__ = 'hfi_fire_start_lookup'
    __table_args__ = (
        {'comment': 'Fire start mean intensity group prep level lookup'}
    )
    id = Column(Integer, primary_key=True)
    fire_start_range_id = Column(Integer, ForeignKey('hfi_fire_start_range.id'), nullable=False, index=True)
    mean_intensity_group = Column(Integer, nullable=False)
    prep_level = Column(Integer, nullable=False)


class FireCentreFireStartRange(Base):
    """ Associate a fire centre with n fire start ranges, in some sort order.
    """
    __tablename__ = 'hfi_fire_centre_fire_start_range'
    __table_args__ = (
        UniqueConstraint('fire_start_range_id', 'fire_centre_id',
                         name='unique_fire_start_range_for_fire_centre'),
        {'comment': 'Link table for fire centre fire start ranges'}
    )
    id = Column(Integer, primary_key=True)
    fire_start_range_id = Column(Integer, ForeignKey('hfi_fire_start_range.id'), nullable=False, index=True)
    fire_centre_id = Column(Integer, ForeignKey(FIRE_CENTRES_ID), nullable=False, index=True)
    order = Column(Integer, nullable=False)
