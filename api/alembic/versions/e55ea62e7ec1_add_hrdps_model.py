"""add_hrdps_model

Revision ID: e55ea62e7ec1
Revises: 7bedf64b703c
Create Date: 2020-10-16 13:11:54.743540

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e55ea62e7ec1'
down_revision = '7bedf64b703c'
branch_labels = None
depends_on = None


def upgrade():
    """ Insert HRDPS model data into prediction_models table """
    op.execute(
        'INSERT INTO prediction_models (abbreviation, name, projection) VALUES (\'HRDPS\', \'High Resolution Deterministic Prediction System\', \'ps2.5km\')')


def downgrade():
    """ Delete the HRDPS model from prediction_models """
    op.execute('DELETE from prediction_models WHERE projection = \'ps2.5km\'')
