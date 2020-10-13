"""merge 2 heads

Revision ID: 3ef3ed4c5a32
Revises: bcd30e84cda0, 7bedf64b703c
Create Date: 2020-10-13 10:53:07.638746

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ef3ed4c5a32'
down_revision = ('bcd30e84cda0', '7bedf64b703c')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
