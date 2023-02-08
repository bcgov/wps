"""Add extra SFMS fuel type

Revision ID: 971848399c46
Revises: 0961883640ef
Create Date: 2023-02-03 15:20:04.140023

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '971848399c46'
down_revision = '0961883640ef'
branch_labels = None
depends_on = None


def upgrade():
    """ Insert non-fuel code -10,000 into sfms_fuel_types table.
    This fuel type doesn't appear in original Excel spreadsheet for SFMS fuel types, but is used
    as a non-fuel type in some fire zones.
    """
    op.execute(
        'INSERT INTO sfms_fuel_types (fuel_type_id, fuel_type_code, description) VALUES (-10000, \'Non-fuel\', \'Non-fuel\')')


def downgrade():
    """ Delete fuel_type_id -10000 from sfms_fuel_types table. """
    op.execute(
        'DELETE FROM sfms_fuel_types WHERE fuel_type_id = -10000'
    )
