"""Revise some fuel types

Revision ID: 1161fab52ef5
Revises: 4e9664f4962e
Create Date: 2022-02-10 15:37:40.727458

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1161fab52ef5'
down_revision = '4e9664f4962e'
branch_labels = None
depends_on = None

def get_fuel_type_id(fuel_type):
    # Helper function to get fuel_types.id
    conn = op.get_bind()
    cursor = conn.execute(f"SELECT id FROM fuel_types WHERE abbrev = '{fuel_type}'")
    result = cursor.fetchall()
    return result[0][0]

def upgrade():
    # Replace simple "M1" fuel type record in database with the 3 variations
    m1_id = get_fuel_type_id("M1")
    op.execute(f"DELETE FROM fuel_types WHERE id = {m1_id}")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M1_25', 'Boreal mixedwood - leafless - 25% conifer')")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M1_50', 'Boreal mixedwood - leafless - 50% conifer')")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M1_75', 'Boreal mixedwood - leafless - 75% conifer')")

    # Replace simple "M2" fuel type record in database with the 3 variations
    m2_id = get_fuel_type_id("M2")
    op.execute(f"DELETE FROM fuel_types WHERE id = {m2_id}")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M2_25', 'Boreal mixedwood - green - 25% conifer')")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M2_50', 'Boreal mixedwood - green - 50% conifer')")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M2_75', 'Boreal mixedwood - green - 75% conifer')")

    # Replace simple "M3" fuel type record in database with the 3 variations
    m3_id = get_fuel_type_id("M3")
    op.execute(f"DELETE FROM fuel_types WHERE id = {m3_id}")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M3_30', 'Dead balsam fir mixedwood - leafless - 30% dead fir')")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M3_60', 'Dead balsam fir mixedwood - leafless - 60% dead fir')")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M3_100', 'Dead balsam fir mixedwood - leafless - 100% dead fir')")

    # Replace simple "M4" fuel type record in database with the 3 variations
    m4_id = get_fuel_type_id("M4")
    op.execute(f"DELETE FROM fuel_types WHERE id = {m4_id}")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M4_30', 'Dead balsam fir mixedwood - green - 30% dead fir')")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M4_60', 'Dead balsam fir mixedwood - green - 60% dead fir')")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M4_100', 'Dead balsam fir mixedwood - green - 100% dead fir')")


def downgrade():
    # Delete the "M1_x" variants, replace with simple "M1"
    op.execute(f"DELETE FROM fuel_types WHERE abbrev LIKE 'M1_%'")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M1', 'Boreal mixedwood - leafless')")

    # Delete the "M2_x" variants, replace with simple "M2"
    op.execute(f"DELETE FROM fuel_types WHERE abbrev LIKE 'M2_%'")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M2', 'Boreal mixedwood - green')")

    # Delete the "M3_x" variants, replace with simple "M3"
    op.execute(f"DELETE FROM fuel_types WHERE abbrev LIKE 'M3_%'")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M3', 'Dead balsam fir mixedwood - leafless')")

    # Delete the "M4_x" variants, replace with simple "M4"
    op.execute(f"DELETE FROM fuel_types WHERE abbrev LIKE 'M4_%'")
    op.execute(f"INSERT INTO fuel_types (abbrev, description) VALUES ('M4', 'Dead balsam fir mixedwood - green')")
