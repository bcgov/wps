from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import numpy as np
import pytest

from wps_sfms.raster_dependencies import GriddedRasterDependencies
from wps_sfms.tests.raster_test_utils import create_test_wps_dataset


@pytest.mark.anyio
async def test_assert_keys_exist_reports_all_required_keys():
    dependencies = GriddedRasterDependencies()
    s3_client = SimpleNamespace(all_objects_exist=AsyncMock(return_value=False))
    keys = ("fuel.tif", "ffmc.tif")
    action = dependencies.assert_keys_exist(s3_client, keys)

    with pytest.raises(
        RuntimeError,
        match="Missing raster dependencies: fuel.tif, ffmc.tif",
    ):
        await action

    s3_client.all_objects_exist.assert_awaited_once_with(*keys)


def test_open_by_key_indexes_datasets_independently_of_returned_order():
    dependencies = GriddedRasterDependencies()
    fuel = create_test_wps_dataset("fuel.tif", np.ones((1, 1), dtype=np.float32))
    ffmc = create_test_wps_dataset("ffmc.tif", np.ones((1, 1), dtype=np.float32))

    @contextmanager
    def reversed_dataset_context(keys):
        assert keys == ["fuel.tif", "ffmc.tif"]
        yield [ffmc, fuel]

    with dependencies.open_by_key(reversed_dataset_context, ("fuel.tif", "ffmc.tif")) as datasets:
        assert datasets == {"fuel.tif": fuel, "ffmc.tif": ffmc}


def test_validate_grids_accepts_matching_candidate():
    dependencies = GriddedRasterDependencies()
    fuel = create_test_wps_dataset("fuel.tif", np.ones((1, 1), dtype=np.float32))
    candidate = create_test_wps_dataset("candidate.tif", np.ones((1, 1), dtype=np.float32))

    dependencies.validate_grids(
        fuel,
        {"candidate": candidate},
    )


def test_validate_grids_rejects_mismatched_candidate():
    dependencies = GriddedRasterDependencies()
    fuel = create_test_wps_dataset("fuel.tif", np.ones((1, 1), dtype=np.float32))
    candidate = create_test_wps_dataset("candidate.tif", np.ones((1, 2), dtype=np.float32))

    with pytest.raises(ValueError, match="candidate raster does not match the fuel grid"):
        dependencies.validate_grids(
            fuel,
            {"candidate": candidate},
        )
