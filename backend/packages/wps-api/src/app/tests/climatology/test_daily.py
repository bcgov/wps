from datetime import UTC, date, datetime

import pyarrow as pa
import pytest
from wps_shared.schemas.climatology import ClimatologyMethod, ClimatologyVariable
from wps_weather_data.by_station import STATIONS_ROWS_SCHEMA
from wps_weather_data.by_time import ACTUALS, FWI_COLUMNS

from app.climatology.daily import daily_climatology

TEMPERATURE = ClimatologyVariable.TEMPERATURE


def rows(values: list[tuple[int, date, float | None]], column: str = "temperature") -> pa.Table:
    """Daily ACTUALS rows of (station, date, value), as ByStationTable.read_stations returns them."""
    columns = {name: [None] * len(values) for name in STATIONS_ROWS_SCHEMA.names}
    columns["source"] = [ACTUALS] * len(values)
    columns["station_code"] = [station for station, _, _ in values]
    columns["timestamp"] = [
        datetime(day.year, day.month, day.day, 20, tzinfo=UTC) for _, day, _ in values
    ]
    columns[column] = [value for _, _, value in values]
    return pa.table(columns, schema=STATIONS_ROWS_SCHEMA)


def july_first(station: int, years_and_values: dict[int, float]) -> list:
    return [(station, date(year, 7, 1), value) for year, value in years_and_values.items()]


def single(table: pa.Table, year: int = 2026, column=TEMPERATURE):
    (series,) = daily_climatology(table, [322], column, year).series
    return series


class TestOneStation:
    def test_a_days_distribution_comes_from_every_other_year(self):
        table = rows(
            july_first(
                322, {2021: 10.0, 2022: 20.0, 2023: 30.0, 2024: 40.0, 2025: 50.0, 2026: 99.0}
            )
        )

        series = single(table)

        (day,) = series.days
        assert (day.month, day.day, day.count, day.station_count) == (7, 1, 5, 1)
        assert (day.minimum, day.p25, day.median, day.p75, day.maximum) == (10, 20, 30, 40, 50)
        # Interpolated between the two highest values.
        assert day.p90 == pytest.approx(46.0)
        assert (series.first_reference_year, series.last_reference_year) == (2021, 2025)
        assert series.station_codes == [322]

    def test_the_compared_year_is_returned_as_observations_and_left_out_of_the_distribution(self):
        table = rows(
            [
                (322, date(2026, 7, 2), 31.0),
                (322, date(2026, 7, 1), 30.0),
                (322, date(2025, 7, 1), 10.0),
            ]
        )

        series = single(table)

        assert [(o.date, o.value, o.station_count) for o in series.observations] == [
            (date(2026, 7, 1), 30.0, 1),
            (date(2026, 7, 2), 31.0, 1),
        ]
        assert [(day.month, day.day, day.maximum) for day in series.days] == [(7, 1, 10.0)]

    def test_a_past_year_can_be_compared_against_the_rest(self):
        series = single(rows(july_first(322, {2024: 10.0, 2025: 20.0, 2026: 30.0})), year=2025)

        assert [o.value for o in series.observations] == [20.0]
        assert (series.days[0].minimum, series.days[0].maximum) == (10.0, 30.0)
        assert (series.first_reference_year, series.last_reference_year) == (2024, 2026)

    def test_compared_years_are_returned_in_the_order_asked_for(self):
        table = rows(
            [
                (322, date(2024, 7, 2), 11.0),
                (322, date(2024, 7, 1), 10.0),
                (322, date(2025, 7, 1), 20.0),
                (322, date(2026, 7, 1), 30.0),
            ]
        )

        (series,) = daily_climatology(
            table, [322], TEMPERATURE, 2026, compare_years=[2025, 2024, 2025, 2026]
        ).series

        # Asked for twice counts once, and the selected year is not compared with itself.
        assert [
            (each.year, [(o.date, o.value) for o in each.observations])
            for each in series.compared_years
        ] == [
            (2025, [(date(2025, 7, 1), 20.0)]),
            (2024, [(date(2024, 7, 1), 10.0), (date(2024, 7, 2), 11.0)]),
        ]
        assert [o.value for o in series.observations] == [30.0]

    def test_comparing_years_does_not_change_the_distribution(self):
        table = rows(july_first(322, {2024: 10.0, 2025: 20.0, 2026: 30.0}))

        (compared,) = daily_climatology(
            table, [322], TEMPERATURE, 2026, compare_years=[2025]
        ).series

        assert compared.days == single(table).days
        assert (compared.first_reference_year, compared.last_reference_year) == (2024, 2025)

    def test_a_compared_year_with_no_values_is_empty(self):
        (series,) = daily_climatology(
            rows(july_first(322, {2025: 20.0})), [322], TEMPERATURE, 2026, compare_years=[1987]
        ).series

        assert [(each.year, each.observations) for each in series.compared_years] == [(1987, [])]

    def test_days_are_in_calendar_order(self):
        table = rows(
            [
                (322, date(2025, 12, 31), 1.0),
                (322, date(2024, 1, 1), 2.0),
                (322, date(2025, 6, 15), 3.0),
            ]
        )

        assert [(day.month, day.day) for day in single(table).days] == [(1, 1), (6, 15), (12, 31)]

    def test_missing_values_are_left_out(self):
        table = rows(
            [
                (322, date(2024, 7, 1), None),
                (322, date(2025, 7, 1), 20.0),
                (322, date(2026, 7, 1), None),
            ]
        )

        series = single(table)

        assert series.days[0].count == 1
        assert series.observations == []

    def test_a_leap_day_is_not_part_of_the_distribution(self):
        table = rows([(322, date(2024, 2, 29), 5.0), (322, date(2024, 2, 28), 4.0)])

        assert [(day.month, day.day) for day in single(table).days] == [(2, 28)]

    def test_the_variable_selects_the_column(self):
        table = rows([(322, date(2025, 7, 1), 12.5)], column="precipitation")

        assert single(table, column=ClimatologyVariable.PRECIPITATION).days[0].median == 12.5
        assert single(table).days == []

    def test_a_station_with_no_rows_has_no_climatology(self):
        series = single(STATIONS_ROWS_SCHEMA.empty_table())

        assert series.days == []
        assert series.observations == []
        assert (series.first_reference_year, series.last_reference_year) == (None, None)


# Two stations on 1 July: a valley at 20 and 30, a mountain at 10 and 12, and 2026 to compare.
GROUP = rows(
    july_first(1, {2024: 20.0, 2025: 30.0, 2026: 26.0})
    + july_first(2, {2024: 10.0, 2025: 12.0, 2026: 14.0})
)


class TestGroups:
    def test_the_average_is_of_each_years_mean_across_stations(self):
        response = daily_climatology(GROUP, [1, 2], TEMPERATURE, 2026, ClimatologyMethod.AVERAGE)

        (series,) = response.series
        (day,) = series.days
        # 2024: (20 + 10) / 2 = 15, 2025: (30 + 12) / 2 = 21
        assert (day.minimum, day.maximum, day.count, day.station_count) == (15.0, 21.0, 2, 2)
        assert [(o.value, o.station_count) for o in series.observations] == [(20.0, 2)]
        assert series.station_codes == [1, 2]
        assert response.method == ClimatologyMethod.AVERAGE

    def test_pooled_draws_on_every_stations_value_and_compares_the_years_mean(self):
        response = daily_climatology(GROUP, [1, 2], TEMPERATURE, 2026, ClimatologyMethod.POOLED)

        (series,) = response.series
        (day,) = series.days
        assert (day.minimum, day.maximum, day.count, day.station_count) == (10.0, 30.0, 4, 2)
        assert day.median == pytest.approx(16.0)
        assert [o.value for o in series.observations] == [20.0]

    @pytest.mark.parametrize("method", [ClimatologyMethod.AVERAGE, ClimatologyMethod.POOLED])
    def test_a_compared_year_is_the_mean_of_the_stations(self, method):
        (series,) = daily_climatology(GROUP, [1, 2], TEMPERATURE, 2026, method, [2025]).series

        (compared,) = series.compared_years
        assert [(o.value, o.station_count) for o in compared.observations] == [(21.0, 2)]

    def test_each_station_has_its_own_compared_years(self):
        response = daily_climatology(
            GROUP, [1, 2], TEMPERATURE, 2026, ClimatologyMethod.EACH, [2025]
        )

        assert [
            [o.value for o in series.compared_years[0].observations] for series in response.series
        ] == [[30.0], [12.0]]

    def test_each_station_has_its_own_series_in_the_order_asked_for(self):
        response = daily_climatology(GROUP, [2, 1, 999], TEMPERATURE, 2026, ClimatologyMethod.EACH)

        assert [series.station_codes for series in response.series] == [[2], [1], [999]]
        mountain, valley, missing = response.series
        assert (mountain.days[0].minimum, mountain.days[0].maximum) == (10.0, 12.0)
        assert [o.value for o in valley.observations] == [26.0]
        assert missing.days == []

    def test_a_day_only_some_stations_reported_averages_those_that_did(self):
        table = rows(
            july_first(1, {2024: 20.0, 2026: 26.0}) + july_first(2, {2024: 10.0, 2025: 12.0})
        )

        (series,) = daily_climatology(table, [1, 2], TEMPERATURE, 2026).series

        (day,) = series.days
        assert (day.minimum, day.maximum) == (12.0, 15.0)
        assert [(o.value, o.station_count) for o in series.observations] == [(26.0, 1)]

    def test_stations_asked_for_twice_count_once(self):
        response = daily_climatology(GROUP, [1, 1, 2], TEMPERATURE, 2026, ClimatologyMethod.EACH)

        assert [series.station_codes for series in response.series] == [[1], [2]]

    def test_every_method_agrees_for_one_station(self):
        table = rows(july_first(1, {2024: 20.0, 2025: 30.0, 2026: 26.0}))

        results = [
            daily_climatology(table, [1], TEMPERATURE, 2026, method).series[0]
            for method in ClimatologyMethod
        ]

        assert all(result == results[0] for result in results)


@pytest.mark.parametrize(
    "variable", [variable for variable in ClimatologyVariable if variable.value in FWI_COLUMNS]
)
def test_each_fwi_index_is_read_from_its_own_column(variable):
    table = rows(july_first(322, {2024: 80.0, 2025: 90.0, 2026: 85.0}), column=variable.value)

    series = single(table, column=variable)

    (day,) = series.days
    assert (day.minimum, day.maximum) == (80.0, 90.0)
    assert [observation.value for observation in series.observations] == [85.0]


def test_a_record_wf1_marked_invalid_is_left_out():
    table = rows(july_first(322, {2023: 10.0, 2024: 20.0, 2025: 99.0, 2026: 15.0}))
    table = table.set_column(
        table.schema.get_field_index("observation_valid"),
        "observation_valid",
        pa.array([None, True, False, True], pa.bool_()),
    )

    (day,) = single(table).days

    assert (day.count, day.minimum, day.maximum) == (2, 10.0, 20.0)
