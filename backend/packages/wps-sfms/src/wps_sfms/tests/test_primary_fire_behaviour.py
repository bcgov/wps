from datetime import datetime, timezone

import cffdrs.fire_behaviour_prediction
import cffdrs.models
import numpy as np
import pytest

from wps_sfms.interpolation.common import SFMS_NO_DATA
from wps_sfms.processors.primary_fire_behaviour import (
    PrimaryFireBehaviourDatasets,
    calculate_primary_fire_behaviour,
)
from wps_sfms.tests.raster_test_utils import TEST_INPUT_NODATA, create_test_wps_dataset

TEST_DATETIME = datetime(2024, 7, 4, 20, tzinfo=timezone.utc)


def make_datasets(fuel: np.ndarray, **overrides: np.ndarray) -> PrimaryFireBehaviourDatasets:
    shape = fuel.shape
    defaults = {
        "ffmc": np.full(shape, 90.0),
        "bui": np.full(shape, 60.0),
        "wind_speed": np.full(shape, 10.0),
        "wind_direction": np.full(shape, 0.0),
        "slope": np.full(shape, 5.0),
        "aspect": np.full(shape, 50.0),
        "percent_conifer": np.full(shape, 50.0),
        "fmc": np.full(shape, 100.0),
        "isi": np.full(shape, 20.0),
    }
    defaults.update(overrides)
    return PrimaryFireBehaviourDatasets(
        fuel=create_test_wps_dataset("fuel.tif", fuel.astype(np.float32)),
        **{
            name: create_test_wps_dataset(f"{name}.tif", array.astype(np.float32))
            for name, array in defaults.items()
        },
    )


def test_calculation_matches_cffdrs_reference():
    """Regression test for the accel/buieff dtype bug (numba requires int64, not float)."""
    datasets = make_datasets(np.array([[6.0]]))

    result = calculate_primary_fire_behaviour(datasets)

    expected = cffdrs.fire_behaviour_prediction.fire_behaviour_prediction(
        cffdrs.models.FBPInput(
            fuel_type="C6",
            ffmc=90.0,
            bui=60.0,
            ws=10.0,
            wd=0.0,
            gs=5.0,
            aspect=50.0,
            pc=50.0,
            fmc=100.0,
            isi=20.0,
            lat=0.0,
            lon=0.0,
            elv=0.0,
        ),
        "Primary",
    )
    assert result.values[0, 0] == pytest.approx(expected.hfi, rel=1e-3)


def test_non_fuel_becomes_zero_and_source_nodata_remains_sfms_nodata():
    fuel = np.array([[99, 102, TEST_INPUT_NODATA]])
    datasets = make_datasets(fuel)

    result = calculate_primary_fire_behaviour(datasets)

    np.testing.assert_array_equal(result.values, np.array([[0, 0, SFMS_NO_DATA]], dtype=np.float32))


@pytest.mark.parametrize("fmc", [TEST_INPUT_NODATA, np.nan, 0.0, -1.0, 120.1])
def test_invalid_fmc_becomes_sfms_nodata(fmc: float):
    datasets = make_datasets(np.array([[6.0]]), fmc=np.array([[fmc]]))

    result = calculate_primary_fire_behaviour(datasets)

    assert result.values[0, 0] == SFMS_NO_DATA


@pytest.mark.parametrize("fmc", [0.1, 120.0])
def test_valid_fmc_boundaries_are_calculated(fmc: float):
    datasets = make_datasets(np.array([[6.0]]), fmc=np.array([[fmc]]))

    result = calculate_primary_fire_behaviour(datasets)

    assert np.isfinite(result.values[0, 0])
    assert result.values[0, 0] != SFMS_NO_DATA
