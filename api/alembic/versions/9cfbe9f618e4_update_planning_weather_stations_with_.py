"""Update planning_weather_stations with audit info

At this point, the columns
is_deleted, create_user, create_timestamp, update_user, update_timestamp
in planning_weather_stations are set to nullable.
We don't want them to be nullable, but first we have to fill in the existing
records with default values for these columns.
The next Alembic migration will then make those columns non-nullable.

Revision ID: 9cfbe9f618e4
Revises: 41ec381bf3ee
Create Date: 2022-06-20 10:36:49.172370

"""
from alembic import op

from app.utils.time import get_utc_now

# revision identifiers, used by Alembic.
revision = '9cfbe9f618e4'
down_revision = '41ec381bf3ee'
branch_labels = None
depends_on = None


def upgrade():
    # set all existing station records to have is_deleted = False
    op.execute('UPDATE planning_weather_stations SET is_deleted = False')

    # set create_user and update_user columns to default username "system"
    op.execute('UPDATE planning_weather_stations SET create_user = \'system\'')
    op.execute('UPDATE planning_weather_stations SET update_user = \'system\'')

    # set create_timestamp and update_timestamp to the current time, which isn't strictly accurate
    # but it's the best we can do.
    now = get_utc_now()
    op.execute(f'UPDATE planning_weather_stations SET create_timestamp = \'{now}\'')
    op.execute(f'UPDATE planning_weather_stations SET update_timestamp = \'{now}\'')


def downgrade():
    op.execute('UPDATE planning_weather_stations SET is_deleted = NULL')

    op.execute('UPDATE planning_weather_stations SET create_user = NULL')
    op.execute('UPDATE planning_weather_stations SET update_user = NULL')

    op.execute('UPDATE planning_weather_stations SET create_timestamp = NULL')
    op.execute('UPDATE planning_weather_stations SET update_timestamp = NULL')
