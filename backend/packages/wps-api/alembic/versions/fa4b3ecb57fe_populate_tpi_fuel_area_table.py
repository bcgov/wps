"""Populate tpi_fuel_area table

Revision ID: fa4b3ecb57fe
Revises: 1e6932096921
Create Date: 2025-01-21 10:04:48.838953

"""

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from app.auto_spatial_advisory.process_tpi_fuel_area import calculate_masked_tpi_areas
from sqlalchemy.orm.session import Session

# revision identifiers, used by Alembic.
revision = "fa4b3ecb57fe"
down_revision = "1e6932096921"
branch_labels = None
depends_on = None

shape_type_table = sa.Table(
    "advisory_shape_types",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column(
        "name",
        sa.Enum("fire_centre", "fire_zone", "fire_zone_unit", name="shapetypeenum_2"),
        nullable=False,
    ),
)

shape_table = sa.Table(
    "advisory_shapes",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("source_identifier", sa.String),
    sa.Column("shape_type", sa.Integer),
    sa.Column("geom", geoalchemy2.Geometry),
)

tpi_area_table = sa.Table(
    "tpi_fuel_area",
    sa.MetaData(),
    sa.Column("advisory_shape_id", sa.Integer),
    sa.Column(
        "tpi_class", sa.Enum("valley_bottom", "mid_slope", "upper_slope", name="tpiclassenum")
    ),
    sa.Column("fuel_area", sa.Float),
)


def get_fire_zone_unit_shape_type_id(session: Session):
    statement = shape_type_table.select().where(shape_type_table.c.name == "fire_zone_unit")
    result = session.execute(statement).fetchone()
    return result.id


def get_fire_zone_units(session: Session, fire_zone_type_id: int):
    statement = shape_table.select().where(shape_table.c.shape_type == fire_zone_type_id)
    result = session.execute(statement).fetchall()
    return result


def upgrade():
    session = Session(bind=op.get_bind())
    fire_zone_shape_type_id = get_fire_zone_unit_shape_type_id(session)
    zone_units = get_fire_zone_units(session, fire_zone_shape_type_id)
    tpi_area = calculate_masked_tpi_areas(zone_units)
    for advisory_shape_id, tpi_class, fuel_area in tpi_area:
        stmt = sa.insert(tpi_area_table).values(
            advisory_shape_id=advisory_shape_id,
            tpi_class=tpi_class.name,
            fuel_area=fuel_area.item(),
        )
        session.execute(stmt)


def downgrade():
    session = Session(bind=op.get_bind())
    stmt = sa.delete(tpi_area_table)
    session.execute(stmt)
