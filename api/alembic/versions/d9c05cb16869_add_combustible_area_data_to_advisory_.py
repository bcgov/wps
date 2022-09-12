"""Add combustible area data to advisory_shapes

Revision ID: d9c05cb16869
Revises: 0669994d4089
Create Date: 2022-09-09 15:52:22.162223

"""
from alembic import op
import sqlalchemy as sa
import asyncio
import geoalchemy2
from sqlalchemy.orm.session import Session
from app.auto_spatial_advisory.calculate_combustible_land_area import calculate_combustible_area_by_fire_zone


# revision identifiers, used by Alembic.
revision = 'd9c05cb16869'
down_revision = '0669994d4089'
branch_labels = None
depends_on = None

shapes_table = sa.Table(
    'advisory_shapes',
    sa.MetaData(),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('source_identifier', sa.String(), nullable=False),
    sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=3005,
                                                 spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False),
    sa.Column('combustible_area', sa.Float(), nullable=True)
)


async def get_combustible_areas():
    zones_areas = await calculate_combustible_area_by_fire_zone()
    return zones_areas


def upgrade():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    zone_areas = loop.run_until_complete(get_combustible_areas())

    for zone in zone_areas:
        op.execute('UPDATE advisory_shapes SET combustible_area = {} WHERE source_identifier LIKE \'{}\''.format(
            zone['combustible_area'], str(zone['source_identifier'])
        ))


def downgrade():
    op.execute('UPDATE advisory_shapes SET combustible_area = NULL')
