"""Populate missing fuel type raster ids

Revision ID: 9298059a1912
Revises: 305e64ecce19
Create Date: 2025-07-03 11:20:23.050042

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session


# revision identifiers, used by Alembic.
revision = '9298059a1912'
down_revision = '305e64ecce19'
branch_labels = None
depends_on = None


FUEL_GRID_2021 = 2021
FUEL_GRID_2024 = 2024
FUEL_GRID_2021_YEARS = [2022, 2023]
FUEL_GRID_2024_YEARS = [2024, 2025]

fuel_type_raster_table = sa.Table(
    "fuel_type_raster",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("version", sa.Integer),
    sa.Column("year", sa.Integer),
)

run_parameters_table = sa.Table(
    "run_parameters", sa.MetaData(), sa.Column("id", sa.Integer), sa.Column("for_date", sa.Date)
)

advisory_fuel_stats_table = sa.Table(
    "advisory_fuel_stats",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("run_parameters", sa.Integer),
    sa.Column("fuel_type_raster_id", sa.Integer),
)


advisory_hfi_percent_conifer_table = sa.Table(
    "advisory_hfi_percent_conifer",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("run_parameters", sa.Integer),
    sa.Column("fuel_type_raster_id", sa.Integer),
)


critical_hours_table = sa.Table(
    "critical_hours",
    sa.MetaData(),
    sa.Column("id", sa.Integer),
    sa.Column("run_parameters", sa.Integer),
    sa.Column("fuel_type_raster_id", sa.Integer),
)


def get_fuel_type_raster(session: Session, year: int):
    stmt = (
        fuel_type_raster_table.select()
        .where(fuel_type_raster_table.c.year == year)
        .order_by(fuel_type_raster_table.c.version.desc())
    )
    result = session.execute(stmt)
    return result.first()


def get_run_parameter_ids(session: Session, years: list[int]) -> list[int]:
    stmt = (
        run_parameters_table.select()
        .where(sa.func.date_part("year", run_parameters_table.c.for_date).in_(years))
        .order_by(run_parameters_table.c.id)
    )
    rows = session.execute(stmt).fetchall()
    ids = [row.id for row in rows]
    return ids


def update_fk_for_advisory_fuel_stats_table(
    session: Session, fuel_type_raster_id: int, run_parameter_ids: list[int]
) -> None:
    stmt = (
        advisory_fuel_stats_table.update()
        .where(advisory_fuel_stats_table.c.run_parameters.in_(run_parameter_ids))
        .values(fuel_type_raster_id=fuel_type_raster_id)
    )
    session.execute(stmt)


def update_fk_for_advisory_hfi_percent_conifer(
    session: Session, fuel_type_raster_id: int, run_parameter_ids: list[int]
) -> None:
    stmt = (
        advisory_hfi_percent_conifer_table.update()
        .where(advisory_hfi_percent_conifer_table.c.run_parameters.in_(run_parameter_ids))
        .values(fuel_type_raster_id=fuel_type_raster_id)
    )
    session.execute(stmt)


def update_fk_for_critical_hours_table(
    session: Session, fuel_type_raster_id: int, run_parameter_ids: list[int]
) -> None:
    stmt = (
        critical_hours_table.update()
        .where(critical_hours_table.c.run_parameters.in_(run_parameter_ids))
        .values(fuel_type_raster_id=fuel_type_raster_id)
    )
    session.execute(stmt)


def populate_for_years_and_fuel_grid(
    session: Session, fuel_grid_year: int, years: list[int]
) -> None:
    fuel_type_raster = get_fuel_type_raster(session, fuel_grid_year)
    fuel_type_raster_id = fuel_type_raster.id
    run_parameter_ids = get_run_parameter_ids(session, years)
    update_fk_for_advisory_fuel_stats_table(session, fuel_type_raster_id, run_parameter_ids)
    update_fk_for_advisory_hfi_percent_conifer(session, fuel_type_raster_id, run_parameter_ids)
    update_fk_for_critical_hours_table(session, fuel_type_raster_id, run_parameter_ids)


def depopulate_for_years(session: Session, years: list[int]) -> None:
    fuel_type_raster_id = None
    run_parameter_ids = get_run_parameter_ids(session, years)
    update_fk_for_advisory_fuel_stats_table(session, fuel_type_raster_id, run_parameter_ids)
    update_fk_for_advisory_hfi_percent_conifer(session, fuel_type_raster_id, run_parameter_ids)
    update_fk_for_critical_hours_table(session, fuel_type_raster_id, run_parameter_ids)


def upgrade():
    session = Session(bind=op.get_bind())
    # Data processed in 2022 and 2023 used the fbp2021.tif fuel grid.
    populate_for_years_and_fuel_grid(session, FUEL_GRID_2021, FUEL_GRID_2021_YEARS)
    # Data processed in 2024 and 2025 used the fbp2024.tif fuel grid.
    populate_for_years_and_fuel_grid(session, FUEL_GRID_2024, FUEL_GRID_2024_YEARS)


def downgrade():
    session = Session(bind=op.get_bind())
    # Data processed in 2022 and 2023 used the fbp2021.tif fuel grid.
    depopulate_for_years(session, FUEL_GRID_2021_YEARS)
    # Data processed in 2024 and 2025 used the fbp2024.tif fuel grid.
    depopulate_for_years(session, FUEL_GRID_2024_YEARS)
