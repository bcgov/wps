"""Initial HFI data import

Revision ID: 1caf3488a340
Revises: 43dce8db9afb
Create Date: 2021-06-01 15:51:27.767517

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
import json

from app.db.models.hfi_calc import FireCentre, FuelType, PlanningArea


# revision identifiers, used by Alembic.
revision = '1caf3488a340'
down_revision = '43dce8db9afb'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    meta = sa.MetaData(bind=bind)
    fuel_types_table = sa.Table('fuel_types', meta)
    fire_centres_table = sa.Table('fire_centres', meta)
    planning_areas_table = sa.Table('planning_areas', meta)
    planning_weather_stations_table = sa.Table('planning_weather_stations', meta)

    # Load fuel types data
    with open('app/data/fuel_types.json') as fuel_types_file:
        fuel_types_data = json.load(fuel_types_file)

    print(fuel_types_data['fuel_types'])

    op.bulk_insert(fuel_types_table, fuel_types_data['fuel_types'], multiinsert=False)

    # Load planning areas data
    with open('app/data/planning_areas.json') as planning_areas_file:
        planning_areas_data = json.load(planning_areas_file)

    fire_centres = planning_areas_data['fire_centres']
    op.bulk_insert(fire_centres_table, list(fire_centres.keys()), multiinsert=False)

    for centre in fire_centres:
        zones = centre['zones']

        # for each zone (planning area), need to get the fire centre id based on the fire centre name
        # insert into planning_areas table list of zone_name-fire_centre_id pairs
        zones_import_data = []
        for zone in zones:
            fire_centre_id = session.query(FireCentre.id).filter(FireCentre.name == centre)
            zones_import_data.append({'name': zone.key(), 'fire_centre_id': fire_centre_id})

        op.bulk_insert(planning_areas_table, zones_import_data, multiinsert=False)

        stations_import_data = []
        for zone in zones:
            stations = zone['stations']
            for station in stations:
                station_name = station['station_name']
                elevation = station['elevation']
                fuel_type_id = session.query(FuelType.id).filter(FuelType.abbrev == station['fuel_type'])
                planning_area_id = session.query(PlanningArea.id).filter(PlanningArea.name == zone.key())
                station_code = station.key()
                stations_import_data.append({'station_code': station_code, 'station_name': station_name,
                                            'fuel_type_id': fuel_type_id, 'planning_area_id': planning_area_id, 'elevation': elevation})

        op.bulk_insert(planning_weather_stations_table, stations_import_data, multiinsert=False)


def downgrade():
    op.delete('planning_weather_stations')
    op.delete('planning_areas')
    op.delete('fire_centres')
    op.delete('fuel_types')
