"""Add column for order of appearance in planning_areas, with unique constraint for each fire centre

Revision ID: 6d2f4d058ebc
Revises: 8efe0e7b9712
Create Date: 2022-01-21 17:04:36.512341

"""
from alembic import op
import sqlalchemy as sa
import json


# revision identifiers, used by Alembic.
revision = '6d2f4d058ebc'
down_revision = '8efe0e7b9712'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('planning_areas', sa.Column('order_of_appearance_in_list', sa.Integer(), nullable=True))
    op.create_unique_constraint('unique_list_order_for_fire_centre_constraint', 'planning_areas', [
                                'order_of_appearance_in_list', 'fire_centre_id'])
    op.create_table_comment(
        'planning_areas',
        'Only one planning area can be assigned a position in the list for a fire centre',
        existing_comment=None,
        schema=None
    )

    # Load json file with planning areas order data
    with open('alembic/versions/6d2f4d058ebc_add_column_for_order_of_appearance_in_.json') as json_file:
        planning_areas_order_data = json.load(json_file)

    fire_centres = planning_areas_order_data['fire_centres']
    for centre in fire_centres:
        for _, values in centre.items():
            for area in values['zones']:
                for pa_key in area:
                    planning_area_name = '\'' + pa_key + '\''
                    order = area[pa_key]['order_of_appearance_in_list']

                    op.execute('UPDATE planning_areas SET order_of_appearance_in_list = {} WHERE name LIKE {}'.format(
                        order, planning_area_name))


def downgrade():
    op.drop_table_comment(
        'planning_areas',
        existing_comment='Only one planning area can be assigned a position in the list for a fire centre',
        schema=None
    )
    op.drop_constraint('unique_list_order_for_fire_centre_constraint', 'planning_areas', type_='unique')
    op.drop_column('planning_areas', 'order_of_appearance_in_list')
