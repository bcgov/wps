from datetime import UTC, datetime
from unittest.mock import MagicMock

from wps_shared.db.crud.weather_models import get_station_run_rows

AT_1800 = datetime(2026, 11, 12, 18, tzinfo=UTC)
AT_2000 = datetime(2026, 11, 12, 20, tzinfo=UTC)


def session_returning(model_times, station_rows):
    """A session whose first query returns the model's own prediction times, and whose second
    returns the station prediction rows."""
    times_result = MagicMock()
    times_result.scalars.return_value = model_times
    rows_result = MagicMock()
    rows_result.mappings.return_value = station_rows
    session = MagicMock()
    session.execute.side_effect = [times_result, rows_result]
    return session


def station_rows():
    return [
        {"station_code": 322, "prediction_timestamp": AT_1800, "tmp_tgl_2": 10.0},
        {"station_code": 322, "prediction_timestamp": AT_2000, "tmp_tgl_2": 11.0},
    ]


def test_row_is_interpolated_when_the_model_has_no_prediction_at_that_time():
    session = session_returning([AT_1800], station_rows())

    rows = get_station_run_rows(session, 42)

    assert [row["is_interpolated"] for row in rows] == [False, True]
    assert rows[0]["station_code"] == 322
    assert rows[1]["tmp_tgl_2"] == 11.0


def test_is_interpolated_is_unknown_once_the_model_predictions_are_deleted():
    session = session_returning([], station_rows())

    rows = get_station_run_rows(session, 42)

    assert [row["is_interpolated"] for row in rows] == [None, None]
