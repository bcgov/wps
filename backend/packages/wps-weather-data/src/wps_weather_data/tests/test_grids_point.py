from datetime import timedelta

import icechunk
import numpy as np
import pytest

from wps_weather_data.grids.models import MODELS, VariableRun
from wps_weather_data.grids.point import (
    TO_MM,
    read_point_forecast,
    relative_humidity,
    wind_from_components,
)
from wps_weather_data.grids.store import GridStore
from wps_weather_data.tests.grid_helpers import RUN, small_crop, variable_run


def model_store(tmp_path, model: str, values: dict[str, float], precipitation) -> GridStore:
    """A store with one run of a model, the same at every cell: constant but for the
    precipitation, which starts with the totals given and then stays at the last."""
    store = GridStore(model, "recent", icechunk.local_filesystem_storage(str(tmp_path / model)))
    hours = len(store.model.forecast_hours(RUN))
    totals = np.full(hours, precipitation[-1], float)
    totals[: len(precipitation)] = precipitation
    runs: list[VariableRun] = [
        variable_run(
            variable,
            totals if variable.name == "precipitation" else np.full(hours, values[variable.name]),
        )
        for variable in store.model.variables
    ]
    store.write_run(RUN, small_crop(), runs)
    return store


def first_rows(store: GridStore, count: int) -> list[dict]:
    return read_point_forecast(store, RUN, 0, 0).slice(0, count).to_pylist()


def test_a_canadian_models_forecast(tmp_path):
    values = {
        "temperature": 283.15,
        "relative_humidity": 40.0,
        "wind_speed": 10.0,
        "wind_direction": 270.0,
    }
    rows = first_rows(model_store(tmp_path, "HRDPS", values, [0.0, 1.5, 4.0]), 4)

    assert [row["timestamp"] for row in rows] == [RUN + timedelta(hours=h) for h in range(4)]
    assert {row["run_timestamp"] for row in rows} == {RUN}
    assert [row["forecast_hour"] for row in rows] == [0, 1, 2, 3]
    assert [row["precipitation"] for row in rows] == [0.0, 1.5, 2.5, 0.0]
    assert rows[0]["temperature"] == pytest.approx(10.0, abs=1e-4)
    assert rows[0]["relative_humidity"] == 40.0
    assert rows[0]["wind_speed"] == pytest.approx(36.0)
    assert rows[0]["wind_direction"] == 270.0


def test_gfs_wind_comes_from_its_components(tmp_path):
    values = {"temperature": 273.15, "relative_humidity": 50.0, "wind_u": 0.0, "wind_v": -10.0}
    rows = first_rows(model_store(tmp_path, "GFS", values, [0.0, 3.0]), 2)

    assert rows[0]["wind_speed"] == pytest.approx(36.0)
    assert rows[0]["wind_direction"] == 0.0
    # Its rows are 3 hours apart, so the precipitation is the 3 hours'.
    assert [row["forecast_hour"] for row in rows] == [0, 3]
    assert rows[1]["precipitation"] == 3.0


def test_ecmwf_is_in_the_other_models_units(tmp_path):
    values = {"temperature": 293.15, "dewpoint": 293.15, "wind_u": 10.0, "wind_v": 0.0}
    rows = first_rows(model_store(tmp_path, "ECMWF", values, [0.0, 0.002]), 2)

    assert rows[1]["precipitation"] == pytest.approx(2.0)
    assert rows[0]["relative_humidity"] == pytest.approx(100.0)
    assert rows[0]["wind_direction"] == 270.0


def test_a_total_that_falls_is_no_precipitation(tmp_path):
    values = {
        "temperature": 283.15,
        "relative_humidity": 40.0,
        "wind_speed": 1.0,
        "wind_direction": 0.0,
    }
    rows = first_rows(model_store(tmp_path, "HRDPS", values, [0.0, 2.0, 1.9, 3.0]), 4)

    assert [row["precipitation"] for row in rows] == pytest.approx([0.0, 2.0, 0.0, 1.1])


@pytest.mark.parametrize(
    "u, v, direction", [(0, -1, 0), (-1, 0, 90), (0, 1, 180), (1, 0, 270), (-1, -1, 45)]
)
def test_wind_direction_is_where_it_blows_from(u, v, direction):
    assert wind_from_components(np.array(u), np.array(v))[1] == pytest.approx(direction)


def test_relative_humidity_falls_as_the_dew_point_does():
    # 20 °C over a dew point of 10 °C is about 52 to 53 %.
    assert relative_humidity(np.array(20.0), np.array(10.0)) == pytest.approx(52.5, abs=0.5)


def test_every_models_precipitation_units_are_known():
    units = {v.units for m in MODELS.values() for v in m.variables if v.name == "precipitation"}
    assert units == set(TO_MM)
