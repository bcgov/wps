"""Load forecast model definitions

Revision ID: 891900abdb6b
Revises: b29cbd0bb078
Create Date: 2020-07-27 11:29:07.708780

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '891900abdb6b'
down_revision = 'b29cbd0bb078'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        'INSERT INTO prediction_models (abbreviation, name, projection) VALUES (\'GDPS\', \'Global Deterministic Prediction System\', \'latlon.15x.15\')')
    op.execute(
        'INSERT INTO prediction_models (abbreviation, name, projection) VALUES (\'RDPS\', \'Regional Deterministic Prediction System\', \'ps10km\')')


def downgrade():
    # Downgrade will likely fail, given that there may be records referencing these.
    op.execute(
        'DELETE from prediction_models WHERE projection = \'latlon.15x.15\'')
    op.execute('DELETE from prediction_models WHERE projection = \'ps10km\'')
