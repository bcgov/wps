"""Merge heads

Revision ID: 481905f1dfe8
Revises: 8efe0e7b9712, 39806f02cdec
Create Date: 2022-01-17 12:40:01.613726

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '481905f1dfe8'
down_revision = ('8efe0e7b9712', '39806f02cdec')
branch_labels = None
depends_on = None


def upgrade():
    # No action necessary, just merging 2 Alembic version HEADs into one
    pass


def downgrade():
    # No action necessary, just merging 2 Alembic version HEADs into one
    pass
