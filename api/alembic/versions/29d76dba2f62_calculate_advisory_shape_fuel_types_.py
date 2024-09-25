"""Calculate advisory shape fuel types areas

Revision ID: 29d76dba2f62
Revises: d1d57c17e40e
Create Date: 2024-09-13 13:28:14.962795

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
import geoalchemy2
import pdb

from app.db.crud.auto_spatial_advisory import get_fuel_info_by_zone_unit


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
    statement = sa.select(shape_table.c.id).where(shape_table.c.shape_type == fire_zone_type_id).order_by(shape_table.c.id)
    result = session.execute(statement).scalars().all()
    return result


def upgrade():
    session = Session(bind=op.get_bind())
    fire_zone_shape_type_id = get_fire_zone_unit_shape_type_id(session)
    zone_unit_ids = get_fire_zone_units(session, fire_zone_shape_type_id)

    for zone_id in zone_unit_ids:
        print(f"Processing zone: {zone_id}")
        stmt = (
            sa.select(sfms_fuel_types.c.fuel_type_id, advisory_fuel_types.c.geom.ST_Union().ST_Intersection(shape_table.c.geom.ST_Union()).ST_Area())
            .join_from(advisory_fuel_types, shape_table, sa.func.ST_INTERSECTS(advisory_fuel_types.c.geom, shape_table.c.geom))
            .join(sfms_fuel_types, sfms_fuel_types.c.fuel_type_id == advisory_fuel_types.c.fuel_type_id)
            .where(shape_table.c.id == zone_id, advisory_fuel_types.c.fuel_type_id > 0, advisory_fuel_types.c.fuel_type_id < 99)
            .group_by(sfms_fuel_types.c.fuel_type_id)
        )
        results = session.execute(stmt)

        for result in results:
            print(f"Saving result for fuel_type: {result[0]}")
            values = {"advisory_shape_id": zone_id, "fuel_type": result[0], "fuel_area": result[1]}
            insert_statement = advisory_shape_fuels.insert().values(values)
            session.execute(insert_statement)
        session.commit()

    # for item in result:
    #     pdb.set_trace()
    #     print(item)

    #     result = get_fuel_info_by_zone_unit(session, 67)
    #     pdb.set_trace()
    #     for item in result:
    #         pdb.set_trace()
    #         print(item)
    #     # pdb.set_trace()
    #     # # statement = advisory_shape_fuels.select(advisory_shape_fuels.c.fuel_type_id, sfms_fuel_types.c.fuel_type_)
    #     # print("Something")
    # pdb.set_trace()


def downgrade():
    session = Session(bind=op.get_bind())
    delete_statement = advisory_shape_fuels.delete()
    session.execute(delete_statement)
