from datetime import UTC, datetime

from wps_weather_data.stations import StationsTable, stations_table

FETCHED = datetime(2026, 11, 19, 12, tzinfo=UTC)

AFTON = {
    "stationCode": 322,
    "displayLabel": "AFTON",
    "latitude": 50.67,
    "longitude": -120.48,
    "elevation": 780,
    "stationStatus": {"id": "ACTIVE"},
}


def test_stations_table_reads_wf1s_records():
    [row] = stations_table([AFTON], FETCHED).to_pylist()
    assert row == {
        "station_code": 322,
        "name": "AFTON",
        "latitude": 50.67,
        "longitude": -120.48,
        "elevation": 780.0,
        "status": "ACTIVE",
        "fetched_at": FETCHED,
    }


def test_missing_values_are_null():
    [row] = stations_table([{"stationCode": 1, "stationStatus": None}], FETCHED).to_pylist()
    assert (row["name"], row["latitude"], row["status"]) == (None, None, None)


def test_read_before_any_write_is_empty(tmp_path):
    assert StationsTable(str(tmp_path / "stations")).read().num_rows == 0


def test_replace_keeps_only_the_new_list(tmp_path):
    table = StationsTable(str(tmp_path / "stations"))
    table.replace(stations_table([AFTON, {**AFTON, "stationCode": 209}], FETCHED))
    table.replace(stations_table([{**AFTON, "displayLabel": "AFTON 2"}], FETCHED))

    assert table.read().select(["station_code", "name"]).to_pylist() == [
        {"station_code": 322, "name": "AFTON 2"}
    ]


def test_an_empty_list_keeps_the_stored_one(tmp_path):
    table = StationsTable(str(tmp_path / "stations"))
    table.replace(stations_table([AFTON], FETCHED))

    assert table.replace(stations_table([], FETCHED)) is False
    assert table.read().num_rows == 1
