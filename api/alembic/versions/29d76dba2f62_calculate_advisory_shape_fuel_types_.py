"""Calculate advisory shape fuel types areas

Revision ID: 29d76dba2f62
Revises: d1d57c17e40e
Create Date: 2024-09-13 13:28:14.962795

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
import geoalchemy2
from app.auto_spatial_advisory.process_fuel_type_areas_per_zone import calculate_fuel_type_areas_per_zone


# revision identifiers, used by Alembic.
revision = "29d76dba2f62"
down_revision = "d1d57c17e40e"
branch_labels = None
depends_on = None


shape_type_table = sa.Table("advisory_shape_types", sa.MetaData(), sa.Column("id", sa.Integer), sa.Column("name", sa.String))

shape_table = sa.Table(
    "advisory_shapes",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("source_identifier", sa.String),
    sa.Column("shape_type", sa.Integer),
    sa.Column("geom", geoalchemy2.Geometry),
)

advisory_fuel_types = sa.Table(
    "advisory_fuel_types", sa.MetaData(), sa.Column("id", sa.Integer(), nullable=False), sa.Column("fuel_type_id", sa.Integer(), nullable=False), sa.Column("geom", geoalchemy2.Geometry)
)

sfms_fuel_types = sa.Table("sfms_fuel_types", sa.MetaData(), sa.Column("id", sa.Integer), sa.Column("fuel_type_id", sa.Integer), sa.Column("fuel_type_code", sa.String))

advisory_shape_fuels = sa.Table("advisory_shape_fuels", sa.MetaData(), sa.Column("advisory_shape_id", sa.Integer), sa.Column("fuel_type", sa.Integer), sa.Column("fuel_area", sa.Float))


def get_fire_zone_unit_shape_type_id(session: Session):
    statement = shape_type_table.select().where(shape_type_table.c.name == "fire_zone_unit")
    result = session.execute(statement).fetchone()
    return result.id


def get_fire_zone_units(session: Session, fire_zone_type_id: int):
    statement = shape_table.select().where(shape_table.c.shape_type == fire_zone_type_id)
    result = session.execute(statement).fetchall()
    return result

def get_sfms_fuel_types(session: Session):
    statement = sa.select(sfms_fuel_types.c.id, sfms_fuel_types.c.fuel_type_id).where(sfms_fuel_types.c.fuel_type_id > 0, sfms_fuel_types.c.fuel_type_id < 99)
    results = session.execute(statement)
    lookup = {}
    for item in results:
        lookup[item[1]] = item[0]
    return lookup


def upgrade():
    session = Session(bind=op.get_bind())
    fire_zone_shape_type_id = get_fire_zone_unit_shape_type_id(session)
    zone_units = get_fire_zone_units(session, fire_zone_shape_type_id)
    sfms_fuel_type_lookup = get_sfms_fuel_types(session)
    fuel_areas = calculate_fuel_type_areas_per_zone(zone_units, sfms_fuel_type_lookup)
    for advisory_shape_id, sfms_fuel_type, fuel_area in fuel_areas:
        stmt = sa.insert(advisory_shape_fuels).values(advisory_shape_id=advisory_shape_id, fuel_type=sfms_fuel_type, fuel_area=fuel_area.item())
        session.execute(stmt)


def downgrade():
    session = Session(bind=op.get_bind())
    delete_statement = advisory_shape_fuels.delete()
    session.execute(delete_statement)

