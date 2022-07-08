"""Make planning_weather_stations cols non-nullable

Revision ID: 35acf3b96d8a
Revises: 9cfbe9f618e4
Create Date: 2022-06-20 12:19:51.924208

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '35acf3b96d8a'
down_revision = '9cfbe9f618e4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('planning_weather_stations') as batch_op:
        batch_op.alter_column('create_user', nullable=False)
        batch_op.alter_column('update_user', nullable=False)
        batch_op.alter_column('create_timestamp', nullable=False)
        batch_op.alter_column('update_timestamp', nullable=False)
        batch_op.alter_column('is_deleted', nullable=False)


def downgrade():
    with op.batch_alter_table('planning_weather_stations') as batch_op:
        batch_op.alter_column('create_user', nullable=True)
        batch_op.alter_column('update_user', nullable=True)
        batch_op.alter_column('create_timestamp', nullable=True)
        batch_op.alter_column('update_timestamp', nullable=True)
        batch_op.alter_column('is_deleted', nullable=True)
