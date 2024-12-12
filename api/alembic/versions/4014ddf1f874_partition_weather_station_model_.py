"""partition weather_station_model_predictions part 2

Revision ID: 4014ddf1f874
Revises: 362d268606f3
Create Date: 2024-11-25 09:19:43.594892

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "4014ddf1f874"
down_revision = "362d268606f3"
branch_labels = None
depends_on = None


def upgrade():
    # ### drop table that's now partitioned ###
    op.execute("DROP MATERIALIZED VIEW IF EXISTS morecast_2_materialized_view")
    op.drop_table("weather_station_model_predictions_retired", if_exists=True)


def downgrade():
    # ### restore from backup instead ###
    pass
