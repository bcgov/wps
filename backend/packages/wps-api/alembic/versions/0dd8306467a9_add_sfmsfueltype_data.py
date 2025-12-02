"""Add SFMSFuelType data

Revision ID: 0dd8306467a9
Revises: fdbf57102d06
Create Date: 2023-01-31 16:56:22.323537

"""
from alembic import op
import json


# revision identifiers, used by Alembic.
revision = '0dd8306467a9'
down_revision = 'fdbf57102d06'
branch_labels = None
depends_on = None


def upgrade():
    # Load fuel types data
    with open('app/data/bc_fbp_fuel_type_lookup_table_sfms.json') as fuel_types_file:
        fuel_types_data = json.load(fuel_types_file)

    for fuel_type in fuel_types_data:
        fuel_type_id = fuel_type.get('grid_value')
        fuel_type_code = '\'' + fuel_type.get('fuel_type') + '\''
        description = '\'' + fuel_type.get('descriptive_name') + '\''

        op.execute('INSERT INTO sfms_fuel_types (fuel_type_id, fuel_type_code, description) VALUES ({}, {}, {})'.format(
            fuel_type_id, fuel_type_code, description))


def downgrade():
    op.execute('DELETE FROM sfms_fuel_types')
