"""2024 fuel grid update

Revision ID: f9ab4e6a7eeb
Revises: 2b3755392ad8
Create Date: 2024-05-08 10:25:04.121562

"""
from alembic import op
import sqlalchemy as sa
from app.db.models.auto_spatial_advisory import SFMSFuelType, FuelType
from app.auto_spatial_advisory.fuel_type_layer import fuel_type_iterator

# revision identifiers, used by Alembic.
revision = 'f9ab4e6a7eeb'
down_revision = '2b3755392ad8'
branch_labels = None
depends_on = None

m3_fuel_type = {
    'fuel_type_id': 13,
    'fuel_type_code': 'M-3',
    'description': 'Dead Balsam Fir Mixedwood'
}

def upgrade():
    # add missing fuel type to SFMSFuelType table
    stmt = sa.insert(SFMSFuelType).values(fuel_type_id=m3_fuel_type['fuel_type_id'], fuel_type_code=m3_fuel_type['fuel_type_code'], description=m3_fuel_type['description'])
    op.execute(stmt)

    # Delete all the fuel types.
    op.execute(sa.delete(FuelType))

    # Iterate through the fuel types and insert them.
    for fuel_type_id, geom in fuel_type_iterator('fbp2024.tif'):
        statement = sa.insert(FuelType).values(fuel_type_id=fuel_type_id, geom=geom)
        op.execute(statement)


def downgrade():
    stmt = sa.delete(SFMSFuelType).where(SFMSFuelType.fuel_type_id == m3_fuel_type['fuel_type_id'])
    op.execute(stmt)

    # Delete all the fuel types.
    op.execute(sa.delete(FuelType))

    for fuel_type_id, geom in fuel_type_iterator('fbp2021.tif'):
        statement = sa.insert(FuelType).values(fuel_type_id=fuel_type_id, geom=geom)
        op.execute(statement)