"""load fuel types

Revision ID: cb626d81dec9
Revises: e71f0965f6e0
Create Date: 2022-09-13 10:34:53.098741

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from auto_spatial_advisory.fuel_type_layer import fuel_type_iterator


# revision identifiers, used by Alembic.
revision = 'cb626d81dec9'
down_revision = 'e71f0965f6e0'
branch_labels = None
depends_on = None


fuel_type_table = sa.Table('advisory_fuel_types', sa.MetaData(),
                           sa.Column('id', sa.Integer(), nullable=False),
                           sa.Column('fuel_type_id', sa.Integer(), nullable=False),
                           sa.Column('geom', geoalchemy2.Geometry))


def upgrade():
    # Iterate through the fuel types and insert them.
    for fuel_type_id, geom in fuel_type_iterator():
        statement = fuel_type_table.insert().values(fuel_type_id=fuel_type_id, geom=geom)
        op.execute(statement)


def downgrade():
    # Delete all the fuel types.
    op.execute(fuel_type_table.delete())
