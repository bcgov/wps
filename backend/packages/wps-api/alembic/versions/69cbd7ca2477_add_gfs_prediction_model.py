"""Add GFS prediction model

Revision ID: 69cbd7ca2477
Revises: de8355996f8e
Create Date: 2023-02-09 14:30:49.597571

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '69cbd7ca2477'
down_revision = 'de8355996f8e'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('INSERT INTO prediction_models(name, abbreviation, projection)\
        VALUES(\'Global Forecast System\', \'GFS\', \'lonlat.0.5deg\')')


def downgrade():
    op.execute('DELETE FROM prediction_models WHERE abbreviation = \'GFS\'')
