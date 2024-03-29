"""Update Kamloops stations

Revision ID: 82cc8ffa75ce
Revises: c525dbd0c37e
Create Date: 2022-04-14 13:30:21.139779

"""
from typing import List, Optional
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session

# revision identifiers, used by Alembic.
revision = '82cc8ffa75ce'
down_revision = 'c525dbd0c37e'
branch_labels = None
depends_on = None

# New station, pentiction
west_kelowna_station_code = 1277

# New station, vernon
station_bay_2_station_code = 1359

# Pentiction station, order to be adjusted
mccuddy_station_code = 334

# Vernon stations, order to be adjusted
seymour_arm = 344
salmon_arm = 346
kettle_2 = 388

# Ad-hoc tables to use for adding/updating rows for our current schema.

planning_weather_stations_table = sa.Table('planning_weather_stations', sa.MetaData(),
                                           sa.Column('id', sa.Integer),
                                           sa.Column('fuel_type_id', sa.Integer),
                                           sa.Column('planning_area_id', sa.Integer),
                                           sa.Column('station_code', sa.Integer),
                                           sa.Column('order_of_appearance_in_planning_area_list', sa.Integer))

planning_areas_table = sa.Table('planning_areas', sa.MetaData(),
                                sa.Column('id', sa.Integer),
                                sa.Column('name', sa.String),
                                sa.Column('fire_centre_id', sa.Integer),
                                sa.Column('order_of_appearance_in_list', sa.Integer))


fuel_types_table = sa.Table('fuel_types', sa.MetaData(),
                            sa.Column('id', sa.Integer),
                            sa.Column('abbrev', sa.String),
                            sa.Column('fuel_type_code', sa.String),
                            sa.Column('description', sa.String),
                            sa.Column('percentage_conifer', sa.Integer),
                            sa.Column('percentage_dead_fir', sa.Integer))

fire_centres_table = sa.Table('fire_centres', sa.MetaData(),
                              sa.Column('id', sa.Integer),
                              sa.Column('name', sa.String))


def get_fuel_type_id(session: Session, fuel_type_abbrev: str):
    res = session.query(fuel_types_table) \
        .filter(fuel_types_table.c.abbrev.ilike(f'{fuel_type_abbrev}%%'))
    return int(res.first().id)


def get_fire_centre_id(session: Session, fire_centre_name: str):
    res = session.query(fire_centres_table).filter(fire_centres_table.c.name.ilike(f'%{fire_centre_name}%'))
    return int(res.first().id)


def get_planning_area_id_for_fire_centre(session: Session, fc_id: int, planning_area_name: str):
    res = session.query(planning_areas_table) \
        .filter(planning_areas_table.c.fire_centre_id ==
                fc_id) \
        .filter(planning_areas_table.c.name.ilike(f'{planning_area_name}%%'))
    return int(res.first().id)


def update_order_to(station_codes: List[int], order: Optional[int]):
    """ Add the optional ordering value from station """
    return planning_weather_stations_table\
        .update()\
        .values(order_of_appearance_in_planning_area_list=order)\
        .where(planning_weather_stations_table.c.station_code.in_(station_codes))


def upgrade():
    # ### commands auto generated by Alembic ###
    session = Session(bind=op.get_bind())
    kfc_id = get_fire_centre_id(session, 'Kamloops Fire Centre')
    penticton_id = get_planning_area_id_for_fire_centre(session, kfc_id, 'Penticton')
    vernon_id = get_planning_area_id_for_fire_centre(session, kfc_id, 'Vernon')

    # Remove order until new stations are added
    remove_existing_orders_stmt = update_order_to(
        [mccuddy_station_code, seymour_arm, salmon_arm, kettle_2], None)
    session.execute(remove_existing_orders_stmt)

    # Now add the new station with orders
    c7_id = get_fuel_type_id(session, 'c7')
    c5_id = get_fuel_type_id(session, 'c5')
    op.bulk_insert(planning_weather_stations_table, [{
        'station_code': west_kelowna_station_code,
        'fuel_type_id': c7_id,
        'planning_area_id': penticton_id,
        'order_of_appearance_in_planning_area_list': 2
    },
        {'station_code': station_bay_2_station_code,
         'fuel_type_id': c5_id,
         'planning_area_id': vernon_id,
         'order_of_appearance_in_planning_area_list': 3}
    ])

    # Pentiction order update
    update_mccuddy_station_stmt = update_order_to([mccuddy_station_code], 4)

    # Vernon order update
    update_seymour_arm_station_stmt = update_order_to([seymour_arm], 4)
    update_salmon_arm_station_stmt = update_order_to([salmon_arm], 5)
    update_kettle_2_station_stmt = update_order_to([kettle_2], 6)

    session.execute(update_mccuddy_station_stmt)
    session.execute(update_seymour_arm_station_stmt)
    session.execute(update_salmon_arm_station_stmt)
    session.execute(update_kettle_2_station_stmt)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic  ###
    session = Session(bind=op.get_bind())

    delete_stmt = planning_weather_stations_table\
        .delete()\
        .where(planning_weather_stations_table.c.station_code.in_([west_kelowna_station_code, station_bay_2_station_code]))
    session.execute(delete_stmt)

    # Pentiction order update
    update_mccuddy_station_stmt = update_order_to([mccuddy_station_code], 2)

    # Vernon order update
    update_seymour_arm_station_stmt = update_order_to([seymour_arm], 3)
    update_salmon_arm_station_stmt = update_order_to([salmon_arm], 4)
    update_kettle_2_station_stmt = update_order_to([kettle_2], 5)

    session.execute(update_mccuddy_station_stmt)
    session.execute(update_seymour_arm_station_stmt)
    session.execute(update_salmon_arm_station_stmt)
    session.execute(update_kettle_2_station_stmt)

    session.execute(update_mccuddy_station_stmt)

    # ### end Alembic commands ###
