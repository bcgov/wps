"""Add data to pc and pdf cols in fuel_types

Revision ID: fb9d656fdc19
Revises: 92dad9590164
Create Date: 2022-02-16 15:35:35.035481

"""
from alembic import op
import json


# revision identifiers, used by Alembic.
revision = 'fb9d656fdc19'
down_revision = '92dad9590164'
branch_labels = None
depends_on = None

def upgrade():
    op.execute("DELETE FROM planning_weather_stations")
    op.execute("DELETE FROM fuel_types")

    with open('alembic/versions/fb9d656fdc19_add_data_to_pc_and_pdf_cols__upgrade.json') as fuel_types_data_file:
        fuel_types_data = json.load(fuel_types_data_file)

    for fuel_type in fuel_types_data['fuel_types']:
        abbrev = fuel_type['abbrev']
        fuel_type_code = fuel_type['fuel_type_code']
        description = fuel_type['description']
        percentage_conifer = fuel_type['percentage_conifer']
        percentage_dead_fir = fuel_type['percentage_dead_fir']

        op.execute(f"INSERT INTO fuel_types (abbrev, fuel_type_code, description, percentage_conifer, percentage_dead_fir)\
            VALUES (\'{abbrev}\', \'{fuel_type_code}\', \'{description}\', {percentage_conifer}, {percentage_dead_fir})")


def downgrade():
    op.execute("DELETE FROM fuel_types")

    with open('alembic/versions/fb9d656fdc19_add_data_to_pc_and_pdf_cols__downgrade.json') as fuel_types_simplified_file:
        fuel_types_data = json.load(fuel_types_simplified_file)

    for fuel_type in fuel_types_data['fuel_types']:
        abbrev = fuel_type['abbrev']
        description = fuel_type['description']

        op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES (\'{abbrev}\', \'{description}\')")

