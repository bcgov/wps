"""Add NAM weather model

Revision ID: e201ae32516e
Revises: 4e810be22ffd
Create Date: 2023-04-17 09:35:32.015484

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e201ae32516e'
down_revision = '4e810be22ffd'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('INSERT INTO prediction_models(name, abbreviation, projection)\
        VALUES(\'North American Model\', \'NAM\', \'ps32km\')')
    op.execute('UPDATE prediction_models SET projection = \'lonlat.0.25deg\' WHERE abbreviation = \'GFS\'')


def downgrade():
    op.execute('DELETE FROM prediction_models WHERE abbreviation = \'NAM\'')
    op.execute('UPDATE prediction_models SET projection = \'lonlat.0.5deg\' WHERE abbreviation = \'GFS\'')
