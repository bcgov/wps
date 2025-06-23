"""Add combustible area table

Revision ID: e40076a1b002
Revises: 945a5d8e55b6
Create Date: 2025-06-23 12:11:51.397272

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
from wps_shared import config

# revision identifiers, used by Alembic.
revision = 'e40076a1b002'
down_revision = '945a5d8e55b6'
branch_labels = None
depends_on = None


advisory_shapes_table = sa.Table(
    "advisory_shapes", sa.MetaData(),
    sa.Column("id", sa.Integer()),
    sa.Column("combustible_area", sa.Float()),
)

combustible_area_table = sa.Table(
    "combustible_area", sa.MetaData(),
    sa.Column("id", sa.Integer()),
    sa.Column("advisory_shape_id", sa.Integer()),
    sa.Column("combustible_area", sa.Float()),
    sa.Column("fuel_type_raster_id", sa.Integer()),
)

fuel_type_raster_table = sa.Table(
    "fuel_type_raster", sa.MetaData(),
    sa.Column("id", sa.Integer()),
    sa.Column("version", sa.Integer()),
    sa.Column("object_store_path", sa.String()),
)

def get_advisory_shapes(session: Session): 
    stmt = advisory_shapes_table.select()
    result = session.execute(stmt)
    return result.all()

def create_combustible_area(session: Session, advisory_shape_id: int, combustible_area: float, fuel_type_raster_id: int):
    stmt = combustible_area_table.insert().values({"advisory_shape_id": advisory_shape_id, "combustible_area": combustible_area, "fuel_type_raster_id": fuel_type_raster_id})
    session.execute(stmt)

def get_current_fuel_type_raster_id(session: Session):
    name = config.get("FUEL_RASTER_NAME")
    fuel_raster_name = name.lower()[:-4]
    stmt = fuel_type_raster_table.select().where(fuel_type_raster_table.c.object_store_path.contains(fuel_raster_name)).order_by(fuel_type_raster_table.c.version.desc())
    result = session.execute(stmt)
    return result.scalars().first()

def upgrade():
    # ### start Alembic commands ###
    # Create the combustible fuel table
    op.create_table('combustible_area',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('advisory_shape_id', sa.Integer(), nullable=False),
    sa.Column('combustible_area', sa.Float(), nullable=False),
    sa.Column('fuel_type_raster_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['advisory_shape_id'], ['advisory_shapes.id'], ),
    sa.ForeignKeyConstraint(['fuel_type_raster_id'], ['fuel_type_raster.id'], ),
    sa.PrimaryKeyConstraint('id'),
    comment='The combustible area of advisory shapes for each unique fuel grid.'
    )
    op.create_index(op.f('ix_combustible_area_advisory_shape_id'), 'combustible_area', ['advisory_shape_id'], unique=False)
    op.create_index(op.f('ix_combustible_area_fuel_type_raster_id'), 'combustible_area', ['fuel_type_raster_id'], unique=False)
    op.create_index(op.f('ix_combustible_area_id'), 'combustible_area', ['id'], unique=False)

    # Populate the table with data from the current advisory_shapes table.
    session = Session(bind=op.get_bind())
    advisory_shapes = get_advisory_shapes(session)
    latest_fuel_raster_id = get_current_fuel_type_raster_id(session)
    for advisory_shape in advisory_shapes:
        create_combustible_area(session, advisory_shape.id, advisory_shape.combustible_area, latest_fuel_raster_id)
    # ### end Alembic commands ###


def downgrade():
    # ### start Alembic commands ###
    op.drop_index(op.f('ix_combustible_area_id'), table_name='combustible_area')
    op.drop_index(op.f('ix_combustible_area_fuel_type_raster_id'), table_name='combustible_area')
    op.drop_index(op.f('ix_combustible_area_advisory_shape_id'), table_name='combustible_area')
    op.drop_table('combustible_area')
    # ### end Alembic commands ###
