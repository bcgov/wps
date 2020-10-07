"""add hrdps to models table

Revision ID: bcd30e84cda0
Revises: c9f9b2849fef
Create Date: 2020-09-24 16:48:12.942342

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bcd30e84cda0'
down_revision = 'c9f9b2849fef'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        'INSERT INTO prediction_models (abbreviation, name, projection) VALUES (\'HRDPS\', \'High Resolution Deterministic Prediction System\', \'ps2.5km\')')


def downgrade():
    op.execute('DELETE from prediction_models WHERE projection = \'ps2.5km\'')
