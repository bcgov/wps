"""Order planning areas in KFC; modify order_of_appearance_in_list column
in planning_areas table to be non-nullable

Revision ID: 274bec360d8c
Revises: 6d2f4d058ebc
Create Date: 2022-01-24 16:36:51.978303

"""
from alembic import op
import sqlalchemy as sa
import json


# revision identifiers, used by Alembic.
revision = '274bec360d8c'
down_revision = '6d2f4d058ebc'
branch_labels = None
depends_on = None


def upgrade():
    # Load json file with planning areas order data
    with open('alembic/versions/274bec360d8c_order_planning_areas_in_kfc.json') as json_file:
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

    op.alter_column('planning_areas', 'order_of_appearance_in_list',
                    existing_type=sa.INTEGER(),
                    nullable=False)


def downgrade():
    op.alter_column('planning_areas', 'order_of_appearance_in_list',
                    existing_type=sa.INTEGER(),
                    nullable=True)

    conn = op.get_bind()
    res = conn.execute('SELECT id FROM fire_centres WHERE name LIKE \'Kamloops Fire Centre\'')
    kfc_id = int(str(res.fetchall()[0]).replace('(', '').replace(',', '').replace(')', ''))
    op.execute('UPDATE planning_areas SET order_of_appearance_in_list = NULL WHERE fire_centre_id = {}'.format(kfc_id))
