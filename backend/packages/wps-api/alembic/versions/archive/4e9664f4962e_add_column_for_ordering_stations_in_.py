"""Add column for ordering stations in planning area list; add unique constraint

Revision ID: 4e9664f4962e
Revises: 318e6887e4b0
Create Date: 2022-02-08 16:35:20.327919

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e9664f4962e'
down_revision = '318e6887e4b0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('planning_weather_stations', sa.Column('order_of_appearance_in_planning_area_list', sa.Integer(), nullable=True))
    op.create_unique_constraint('unique_order_for_planning_area', 'planning_weather_stations', ['order_of_appearance_in_planning_area_list', 'planning_area_id'])


def downgrade():
    op.drop_constraint('unique_order_for_planning_area', 'planning_weather_stations', type_='unique')
    op.drop_column('planning_weather_stations', 'order_of_appearance_in_planning_area_list')
