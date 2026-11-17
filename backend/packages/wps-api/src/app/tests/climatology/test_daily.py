from datetime import UTC, date, datetime

import pyarrow as pa
import pytest
from wps_shared.schemas.climatology import ClimatologyVariable
from wps_weather_data.by_station import STATION_ROWS_SCHEMA
from wps_weather_data.by_time import ACTUALS

from app.climatology.daily import daily_climatology


def rows(values: list[tuple[date, float | None]], column: str = "temperature") -> pa.Table:
    """Daily ACTUALS rows with a value on each date, as ByStationTable.read returns them."""
    columns = {name: [None] * len(values) for name in STATION_ROWS_SCHEMA.names}
    columns["source"] = [ACTUALS] * len(values)
    columns["timestamp"] = [
        datetime(day.year, day.month, day.day, 20, tzinfo=UTC) for day, _ in values
    ]
    columns[column] = [value for _, value in values]
    return pa.table(columns, schema=STATION_ROWS_SCHEMA)


def july_first(years_and_values: dict[int, float]) -> pa.Table:
    return rows([(date(year, 7, 1), value) for year, value in years_and_values.items()])


def test_a_days_distribution_comes_from_every_other_year():
    table = july_first({2021: 10.0, 2022: 20.0, 2023: 30.0, 2024: 40.0, 2025: 50.0, 2026: 99.0})

    result = daily_climatology(table, 322, ClimatologyVariable.TEMPERATURE, 2026)

    (day,) = result.days
    assert (day.month, day.day, day.count) == (7, 1, 5)
    assert (day.minimum, day.p25, day.median, day.p75, day.maximum) == (10, 20, 30, 40, 50)
    # Interpolated between the two highest values.
    assert day.p90 == pytest.approx(46.0)
    assert (result.first_reference_year, result.last_reference_year) == (2021, 2025)


def test_the_compared_year_is_returned_as_observations_and_left_out_of_the_distribution():
    table = rows([(date(2026, 7, 2), 31.0), (date(2026, 7, 1), 30.0), (date(2025, 7, 1), 10.0)])

    result = daily_climatology(table, 322, ClimatologyVariable.TEMPERATURE, 2026)

    assert [(o.date, o.value) for o in result.observations] == [
        (date(2026, 7, 1), 30.0),
        (date(2026, 7, 2), 31.0),
    ]
    assert [(day.month, day.day, day.maximum) for day in result.days] == [(7, 1, 10.0)]
    assert (result.station_code, result.variable, result.year) == (322, "temperature", 2026)


def test_a_past_year_can_be_compared_against_the_rest():
    table = july_first({2024: 10.0, 2025: 20.0, 2026: 30.0})

    result = daily_climatology(table, 322, ClimatologyVariable.TEMPERATURE, 2025)

    assert [o.value for o in result.observations] == [20.0]
    assert (result.days[0].minimum, result.days[0].maximum) == (10.0, 30.0)
    assert (result.first_reference_year, result.last_reference_year) == (2024, 2026)


def test_days_are_in_calendar_order():
    table = rows([(date(2025, 12, 31), 1.0), (date(2024, 1, 1), 2.0), (date(2025, 6, 15), 3.0)])

    result = daily_climatology(table, 322, ClimatologyVariable.TEMPERATURE, 2026)

    assert [(day.month, day.day) for day in result.days] == [(1, 1), (6, 15), (12, 31)]


def test_missing_values_are_left_out():
    table = rows([(date(2024, 7, 1), None), (date(2025, 7, 1), 20.0), (date(2026, 7, 1), None)])

    result = daily_climatology(table, 322, ClimatologyVariable.TEMPERATURE, 2026)

    assert result.days[0].count == 1
    assert result.observations == []


def test_a_leap_day_is_not_part_of_the_distribution():
    table = rows([(date(2024, 2, 29), 5.0), (date(2024, 2, 28), 4.0)])

    result = daily_climatology(table, 322, ClimatologyVariable.TEMPERATURE, 2026)

    assert [(day.month, day.day) for day in result.days] == [(2, 28)]


def test_the_variable_selects_the_column():
    table = rows([(date(2025, 7, 1), 12.5)], column="precipitation")

    result = daily_climatology(table, 322, ClimatologyVariable.PRECIPITATION, 2026)

    assert result.days[0].median == 12.5
    assert daily_climatology(table, 322, ClimatologyVariable.TEMPERATURE, 2026).days == []


def test_a_station_with_no_rows_has_no_climatology():
    result = daily_climatology(
        STATION_ROWS_SCHEMA.empty_table(), 322, ClimatologyVariable.TEMPERATURE, 2026
    )

    assert result.days == []
    assert result.observations == []
    assert (result.first_reference_year, result.last_reference_year) == (None, None)
