"""Insert C7B

Revision ID: 839f18e0ecc4
Revises: 871c39cf6c26
Create Date: 2022-02-01 13:54:20.342071

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '839f18e0ecc4'
down_revision = '871c39cf6c26'
branch_labels = None
depends_on = None


c7b = 'C7B'
stations_with_c7b = (305, 346, 286, 298, 328, 334, 1399, 836, 280, 1055, 1029, 309, 306)
station_code_list_string = ','.join(str(x) for x in stations_with_c7b)


def get_fuel_type_id(fuel_type):
    # Helper function to get fuel_types.id
    conn = op.get_bind()
    cursor = conn.execute(f"SELECT id FROM fuel_types WHERE abbrev = '{fuel_type}'")
    result = cursor.fetchall()
    return result[0][0]


def upgrade():
    # INSERT C7B fuel type.
    op.execute(
        f"INSERT INTO fuel_types (abbrev, description) values ('{c7b}', 'Proposed C7 model with curing: {c7b}')")
    # Point stations to C7B
    fuel_type_id = get_fuel_type_id(c7b)
    command = f'UPDATE planning_weather_stations SET fuel_type_id = {fuel_type_id} WHERE station_code IN ({station_code_list_string})'
    op.execute(command)


def downgrade():
    # Point stations back to C7
    fuel_type_id = get_fuel_type_id('C7')
    command = f'UPDATE planning_weather_stations SET fuel_type_id = {fuel_type_id} WHERE station_code IN ({station_code_list_string})'
    op.execute(command)
    # DELETE C7B fuel type.
    op.execute(f"DELETE FROM fuel_types WHERE abbrev = '{c7b}'")
