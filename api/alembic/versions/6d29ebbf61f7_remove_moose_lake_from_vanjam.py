"""Remove moose lake from vanjam

Revision ID: 6d29ebbf61f7
Revises: 2dac381ad6e7
Create Date: 2022-07-27 10:36:13.488851

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
from app.utils.time import get_utc_now


# revision identifiers, used by Alembic.
revision = '6d29ebbf61f7'
down_revision = '2dac381ad6e7'
branch_labels = None
depends_on = None

planning_areas_table = sa.Table('planning_areas', sa.MetaData(),
                                sa.Column('id', sa.Integer),
                                sa.Column('name', sa.String),
                                sa.Column('fire_centre_id', sa.Integer),
                                sa.Column('order_of_appearance_in_list', sa.Integer))


planning_weather_stations_table = sa.Table('planning_weather_stations', sa.MetaData(),
                                           sa.Column('id', sa.Integer),
                                           sa.Column('fuel_type_id', sa.Integer),
                                           sa.Column('planning_area_id', sa.Integer),
                                           sa.Column('station_code', sa.Integer),
                                           sa.Column('order_of_appearance_in_planning_area_list', sa.Integer),
                                           sa.Column('create_user', sa.String),
                                           sa.Column('create_timestamp', sa.TIMESTAMP),
                                           sa.Column('update_user', sa.String),
                                           sa.Column('update_timestamp', sa.TIMESTAMP),
                                           sa.Column('is_deleted', sa.Boolean))


moose_lake = 165


def get_nadina_planning_area_id(session: Session):
    res = session.query(planning_areas_table) \
        .filter(planning_areas_table.c.name.ilike(f'VanJam%'))
    return int(res.first().id)


def upgrade():
    session = Session(bind=op.get_bind())
    vanjam_id = get_nadina_planning_area_id(session)

    stmt = planning_weather_stations_table.update().\
        where(sa.and_(planning_weather_stations_table.c.station_code == moose_lake,
              planning_weather_stations_table.c.planning_area_id == vanjam_id)).\
        values({
            'is_deleted': True,
            'update_user': 'system',
            'update_timestamp': get_utc_now()
        })

    session.execute(stmt)


def downgrade():
    # Skip downgrade, apply forward fixes
    pass
