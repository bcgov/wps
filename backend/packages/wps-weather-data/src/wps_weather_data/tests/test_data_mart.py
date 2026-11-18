from datetime import UTC, datetime, timedelta

import pyarrow as pa
import pytest

from wps_weather_data.by_time import ACTUALS, DAILY, HOURLY, ByTimeTable
from wps_weather_data.data_mart import (
    one_per_station_and_time,
    read_observations,
    read_observations_file,
    write_observations,
)
from wps_weather_data.wf1 import Wf1Table, actuals_table

HEADER = (
    '"STATION_CODE","STATION_NAME","DATE_TIME",HOURLY_PRECIPITATION,HOURLY_TEMPERATURE,'
    "HOURLY_RELATIVE_HUMIDITY,HOURLY_WIND_SPEED,HOURLY_WIND_DIRECTION,HOURLY_WIND_GUST,"
    "PRECIPITATION,RN_1_PLUVIO1,"
)
# Hours 11 and 12 Pacific Standard Time are 19:00 and 20:00 UTC.
AT_1900_UTC = datetime(2023, 7, 15, 19, tzinfo=UTC)
NOON_UTC = datetime(2023, 7, 15, 20, tzinfo=UTC)


def line(
    station_code=11,
    time="2023071511",
    precip="0.2",
    temp="15.6",
    rh="48",
    wind="5",
    wdir="327",
    daily_precip="",
):
    return (
        f'"{station_code}","SUMMIT","{time}",{precip},{temp},{rh},{wind},{wdir},,{daily_precip},,,,'
    )


def noon_line(daily_precip="7.4", **values):
    return line(time="2023071512", daily_precip=daily_precip, **values)


def read(*lines) -> pa.Table:
    return pa.concat_tables(read_observations([HEADER, *lines]))


@pytest.fixture
def tables(tmp_path):
    return Wf1Table(str(tmp_path / "wf1")), ByTimeTable(str(tmp_path / "by_time"))


def test_a_row_becomes_an_hourly_actual_at_its_utc_time():
    (row,) = read(line()).to_pylist()

    assert (row["resolution"], row["source"], row["month"]) == (HOURLY, ACTUALS, "2023-07")
    assert (row["station_code"], row["timestamp"]) == (11, AT_1900_UTC)
    assert row["temperature"] == pytest.approx(15.6)
    assert (row["relative_humidity"], row["wind_speed"], row["wind_direction"]) == (48, 5, 327)
    assert row["precipitation"] == pytest.approx(0.2)
    assert row["bias_adjusted_temperature"] is None
    assert row["run_ts"] is None
    assert row["ingested_at"] == AT_1900_UTC


def test_a_noon_row_with_a_daily_total_is_also_a_daily_actual():
    hourly, daily = read(noon_line(daily_precip="7.4")).to_pylist()

    assert (hourly["resolution"], hourly["timestamp"]) == (HOURLY, NOON_UTC)
    assert hourly["precipitation"] == pytest.approx(0.2)
    assert (daily["resolution"], daily["source"], daily["timestamp"]) == (DAILY, ACTUALS, NOON_UTC)
    assert daily["temperature"] == pytest.approx(15.6)
    # WF1's total for the 24 hours before, not the hour's precip.
    assert daily["precipitation"] == pytest.approx(7.4)


@pytest.mark.parametrize("lines", [[noon_line(daily_precip="")], [line(daily_precip="7.4")]])
def test_no_daily_actual_without_a_daily_total_at_noon(lines):
    rows = read(*lines)

    assert rows["resolution"].to_pylist() == [HOURLY]


def test_an_evening_hour_falls_on_the_next_utc_day_and_month():
    (row,) = read(line(time="2023073122")).to_pylist()

    assert row["timestamp"] == datetime(2023, 8, 1, 6, tzinfo=UTC)
    assert row["month"] == "2023-08"


@pytest.mark.parametrize(
    "values, column",
    [
        ({"rh": ""}, "relative_humidity"),
        ({"rh": "101"}, "relative_humidity"),
        ({"wind": "-1"}, "wind_speed"),
        ({"wdir": "361"}, "wind_direction"),
        ({"precip": "nan"}, "precipitation"),
        ({"temp": "M"}, "temperature"),
    ],
)
def test_a_missing_or_out_of_range_value_is_null(values, column):
    (row,) = read(line(**values)).to_pylist()

    assert row[column] is None


def test_a_row_with_no_values_is_left_out():
    rows = read(line(precip="", temp="", rh="", wind="", wdir=""), line(station_code=12))

    assert rows["station_code"].to_pylist() == [12]


def test_a_file_with_a_byte_order_mark_is_read(tmp_path):
    path = tmp_path / "2026-11-16.csv"
    path.write_text(HEADER + "\n" + line() + "\n", encoding="utf-8-sig")

    (rows,) = read_observations_file(str(path))

    assert rows["station_code"].to_pylist() == [11]


def test_a_repeated_row_is_kept_once_as_its_last_version():
    rows = read(line(temp="15.6"), line(station_code=12), line(temp="16.0"))

    rows = one_per_station_and_time(rows)

    assert rows["station_code"].to_pylist() == [12, 11]
    assert rows["temperature"].to_pylist() == [pytest.approx(15.6), 16.0]


def test_write_observations_fills_wf1_and_by_time(tables):
    wf1, by_time = tables

    written = write_observations(wf1, by_time, read(line(), noon_line()))

    assert written == {"read": 3, "daily": 1, "wf1": 3, "by_time": 3}
    assert wf1.dataset().count_rows() == 3
    assert by_time.read(HOURLY, [ACTUALS], AT_1900_UTC, NOON_UTC).num_rows == 2
    (daily,) = by_time.read(DAILY, [ACTUALS], NOON_UTC, NOON_UTC).to_pylist()
    assert daily["precipitation"] == pytest.approx(7.4)


def test_write_observations_again_changes_nothing(tables):
    wf1, by_time = tables
    write_observations(wf1, by_time, read(line(), noon_line()))

    written = write_observations(wf1, by_time, read(line(), noon_line()))

    assert written["wf1"] == 0
    assert wf1.dataset().count_rows() == 3
    assert by_time.dataset().count_rows() == 3


def test_write_observations_writes_each_month(tables):
    wf1, by_time = tables

    write_observations(wf1, by_time, read(line(time="2023073122"), line(time="2023073112")))

    months = by_time.dataset().to_table(columns=["month"])["month"].to_pylist()
    assert sorted(months) == ["2023-07", "2023-08"]


def test_write_observations_does_not_replace_a_value_fetched_from_wf1(tables):
    wf1, by_time = tables
    fetched = actuals_table(
        [
            type(
                "Record",
                (),
                {
                    "station_code": 11,
                    "weather_date": AT_1900_UTC,
                    "temperature": 20.0,
                    "relative_humidity": 48.0,
                    "wind_speed": 5.0,
                    "wind_direction": 327.0,
                    "precipitation": 0.2,
                },
            )()
        ],
        AT_1900_UTC + timedelta(minutes=15),
    )
    by_time.merge_wf1_rows(fetched)

    write_observations(wf1, by_time, read(line(temp="15.6")))

    (row,) = by_time.read(HOURLY, [ACTUALS], AT_1900_UTC, AT_1900_UTC).to_pylist()
    assert row["temperature"] == 20.0


FWI_HEADER = (
    '"STATION_CODE","STATION_NAME","DATE_TIME",HOURLY_PRECIPITATION,HOURLY_TEMPERATURE,'
    "HOURLY_RELATIVE_HUMIDITY,HOURLY_WIND_SPEED,HOURLY_WIND_DIRECTION,HOURLY_WIND_GUST,"
    "HOURLY_FINE_FUEL_MOISTURE_CODE,HOURLY_INITIAL_SPREAD_INDEX,HOURLY_FIRE_WEATHER_INDEX,"
    "PRECIPITATION,FINE_FUEL_MOISTURE_CODE,INITIAL_SPREAD_INDEX,FIRE_WEATHER_INDEX,"
    "DUFF_MOISTURE_CODE,DROUGHT_CODE,BUILDUP_INDEX,DANGER_RATING"
)


def test_the_noon_row_carries_the_daily_values_and_the_hourly_row_its_own():
    noon = (
        '"11","SUMMIT","2023071512",0,20.1,30,10,270,25,90.1,9.5,15.2,0,89.0,8.0,14.0,45,400,70,3'
    )

    hourly, daily = pa.concat_tables(read_observations([FWI_HEADER, noon])).to_pylist()

    assert (hourly["resolution"], daily["resolution"]) == (HOURLY, DAILY)
    assert [hourly[column] for column in ("ffmc", "isi", "fwi")] == pytest.approx([90.1, 9.5, 15.2])
    assert (hourly["dmc"], hourly["dc"], hourly["bui"]) == (None, None, None)
    assert [daily[column] for column in ("ffmc", "dmc", "dc", "isi", "bui", "fwi")] == (
        pytest.approx([89.0, 45, 400, 8.0, 70, 14.0])
    )
    assert (hourly["wind_gust"], hourly["danger_rating"]) == (25, None)
    assert (daily["wind_gust"], daily["danger_rating"]) == (25, 3)
    assert daily["observation_valid"] is None


def test_a_file_without_fwi_columns_has_null_indices():
    (row,) = read(line()).to_pylist()

    assert (row["ffmc"], row["isi"], row["fwi"]) == (None, None, None)
