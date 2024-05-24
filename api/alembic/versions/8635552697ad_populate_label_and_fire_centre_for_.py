"""Populate label and fire centre for advisory_shapes

Revision ID: 8635552697ad
Revises: 6ec6afd92af3
Create Date: 2024-04-30 10:31:47.462473

"""

from alembic import op
from sqlalchemy.orm.session import Session
import sqlalchemy as sa
from app.utils.zone_units import get_zone_units_geojson


# revision identifiers, used by Alembic.
revision = "8635552697ad"
down_revision = "6ec6afd92af3"
branch_labels = None
depends_on = None


shape_type_table = sa.Table("advisory_shape_types", sa.MetaData(), sa.Column("id", sa.Integer), sa.Column("name", sa.String))

shape_table = sa.Table(
    "advisory_shapes",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("source_identifier", sa.String),
    sa.Column("shape_type", sa.Integer),
    sa.Column("label", sa.String),
    sa.Column("fire_centre", sa.Integer),
)

fire_centres_table = sa.Table("fire_centres", sa.MetaData(), sa.Column("id", sa.Integer), sa.Column("name", sa.String))


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
    # Fetch fire zone unit details from geojson in S3
    fire_zone_units_geojson = get_zone_units_geojson()

    for feature in fire_zone_units_geojson.get("features", []):
        properties = feature.get("properties", {})
        # Each zone unit is uniquely identified by an OBJECTID.
        object_id = properties.get("OBJECTID")
        fire_zone_label = properties.get("FIRE_ZONE")
        fire_centre_name = properties.get("FIRE_CENTR")

        # The fire_centre field is a foreign key, so we need an id from the fire_centres table for the relationship
        statement = fire_centres_table.select().where(fire_centres_table.c.name == fire_centre_name)
        result = session.execute(statement).fetchone()
        fire_centre_id = result.id

        # Insert the label and fire centre id into the advisory_shapes table
        insert_statement = shape_table.update().where(shape_table.c.source_identifier == str(object_id)).values(label=fire_zone_label, fire_centre=fire_centre_id)
        session.execute(insert_statement)


def downgrade():
    # No need for a downgrade in this data migration.
    pass
