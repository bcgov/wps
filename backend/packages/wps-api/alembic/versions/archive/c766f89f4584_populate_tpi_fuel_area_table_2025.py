"""Populate tpi_fuel_area_table 2025

Revision ID: c766f89f4584
Revises: e94f982e723c
Create Date: 2025-06-24 10:45:29.516545

"""

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from app.auto_spatial_advisory.process_tpi_fuel_area import calculate_masked_tpi_areas
from sqlalchemy.orm.session import Session

# revision identifiers, used by Alembic.
revision = "c766f89f4584"
down_revision = "e94f982e723c"
branch_labels = None
depends_on = None


fuel_type_raster_table = sa.Table(
    "fuel_type_raster",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("version", sa.Integer),
    sa.Column("year", sa.Integer),
)

shape_type_table = sa.Table(
    "advisory_shape_types",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column(
        "name",
        sa.Enum("fire_centre", "fire_zone", "fire_zone_unit", name="shapetypeenum"),
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
    sa.Column("fuel_type_raster_id", sa.Integer),
)


def get_fire_zone_unit_shape_type_id(session: Session):
    statement = shape_type_table.select().where(shape_type_table.c.name == "fire_zone_unit")
    result = session.execute(statement).fetchone()
    return result.id


def get_fire_zone_units(session: Session, fire_zone_type_id: int):
    statement = shape_table.select().where(shape_table.c.shape_type == fire_zone_type_id)
    result = session.execute(statement).fetchall()
    return result


def get_fuel_type_raster(session: Session, year: int) -> int:
    stmt = (
        fuel_type_raster_table.select()
        .where(fuel_type_raster_table.c.year == year)
        .order_by(fuel_type_raster_table.c.version.desc())
    )
    result = session.execute(stmt)
    return result.first()


def upgrade():
    session = Session(bind=op.get_bind())
    fuel_type_raster = get_fuel_type_raster(session, 2025)
    fire_zone_shape_type_id = get_fire_zone_unit_shape_type_id(session)
    zone_units = get_fire_zone_units(session, fire_zone_shape_type_id)
    fuel_masked_tpi_filename_2025 = "bc_dem_50m_tpi_win100_classified_fuel_masked_2025.tif"
    tpi_area = calculate_masked_tpi_areas(zone_units, fuel_masked_tpi_filename_2025)
    for advisory_shape_id, tpi_class, fuel_area in tpi_area:
        stmt = sa.insert(tpi_area_table).values(
            advisory_shape_id=advisory_shape_id,
            tpi_class=tpi_class.name,
            fuel_area=fuel_area.item(),
            fuel_type_raster_id=fuel_type_raster.id,
        )
        session.execute(stmt)


def downgrade():
    session = Session(bind=op.get_bind())
    fuel_type_raster = get_fuel_type_raster(session, 2025)
    stmt = sa.delete(tpi_area_table).where(
        tpi_area_table.c.fuel_type_raster_id == fuel_type_raster.id
    )
    session.execute(stmt)
