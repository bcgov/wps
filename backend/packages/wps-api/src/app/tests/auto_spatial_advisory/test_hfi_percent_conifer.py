from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.run_type import RunType

from app.auto_spatial_advisory.hfi_percent_conifer import (
    _resolve_percent_conifer_path,
    process_hfi_percent_conifer,
    update_minimum_percent_conifer_by_zone,
)

BASE = "app.auto_spatial_advisory.hfi_percent_conifer."


def test_update_minimum_percent_conifer_by_zone_groups_valid_pixels():
    minimums = {}

    update_minimum_percent_conifer_by_zone(
        minimums,
        zones=np.array([[1, 1, 2], [1, 2, -1]]),
        raw_hfi=np.array([[5000, 11000, 9000], [3000, 12000, 12000]]),
        percent_conifer=np.array([[30.0, 20.0, 15.0], [10.0, 0.0, 5.0]]),
        zone_nodata=-1,
    )

    assert minimums == {1: 20, 2: 15}


def test_update_minimum_percent_conifer_by_zone_ignores_invalid_values_and_hfi_boundary():
    minimums = {}

    update_minimum_percent_conifer_by_zone(
        minimums,
        zones=np.array([[1, 1, 2, 2]]),
        raw_hfi=np.array([[4000, 4001, 5000, 5000]]),
        percent_conifer=np.array([[50.0, np.nan, np.inf, 25.0]]),
        zone_nodata=-1,
    )

    assert minimums == {2: 25}


def test_update_minimum_percent_conifer_by_zone_merges_minimums_across_windows():
    minimums = {}

    update_minimum_percent_conifer_by_zone(
        minimums,
        zones=np.array([[1, 2]]),
        raw_hfi=np.array([[5000, 5000]]),
        percent_conifer=np.array([[30.0, 40.0]]),
        zone_nodata=-1,
    )
    update_minimum_percent_conifer_by_zone(
        minimums,
        zones=np.array([[1, 2]]),
        raw_hfi=np.array([[5000, 5000]]),
        percent_conifer=np.array([[20.0, 50.0]]),
        zone_nodata=-1,
    )

    assert minimums == {1: 20, 2: 40}


def test_update_minimum_percent_conifer_by_zone_leaves_empty_results_unchanged():
    minimums = {}

    update_minimum_percent_conifer_by_zone(
        minimums,
        zones=np.array([[-1, -1]]),
        raw_hfi=np.array([[4000, 3000]]),
        percent_conifer=np.array([[20.0, 30.0]]),
        zone_nodata=-1,
    )

    assert minimums == {}


@pytest.fixture
def mock_s3():
    mock = MagicMock()
    mock.object_exists = AsyncMock()
    return mock


SFMS_TEST_DATE = date(2024, 12, 15)


@pytest.mark.anyio
async def test_resolve_percent_conifer_path_uses_fuel_raster_year(mock_s3):
    addresser = MagicMock()
    addresser.get_percent_conifer_key.side_effect = lambda year: f"sfms/static/m12_{year}.tif"
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/bucket/{key}"
    mock_s3.object_exists.return_value = True

    path = await _resolve_percent_conifer_path(2023, addresser, mock_s3)

    assert path == "/vsis3/bucket/sfms/static/m12_2023.tif"
    addresser.get_percent_conifer_key.assert_called_once_with(2023)
    mock_s3.object_exists.assert_awaited_once_with("sfms/static/m12_2023.tif")


@pytest.mark.anyio
async def test_resolve_percent_conifer_path_does_not_fall_back_to_another_year(mock_s3):
    addresser = MagicMock()
    addresser.get_percent_conifer_key.side_effect = lambda year: f"sfms/static/m12_{year}.tif"
    mock_s3.object_exists.side_effect = [False, True]

    with pytest.raises(
        RuntimeError,
        match="fuel-grid year 2024: sfms/static/m12_2024.tif",
    ):
        await _resolve_percent_conifer_path(2024, addresser, mock_s3)

    addresser.get_percent_conifer_key.assert_called_once_with(2024)
    mock_s3.object_exists.assert_awaited_once_with("sfms/static/m12_2024.tif")
    addresser.gdal_path.assert_not_called()


@pytest.mark.anyio
async def test_process_hfi_percent_conifer_uses_selected_fuel_raster_year(mocker):
    session = AsyncMock()
    session.scalar.return_value = None
    session_scope = mocker.patch(BASE + "get_async_write_session_scope")
    session_scope.return_value.__aenter__.return_value = session
    mocker.patch(BASE + "get_run_parameters_id", new=AsyncMock(return_value=1))

    fuel_raster = MagicMock(spec=FuelTypeRaster)
    fuel_raster.id = 10
    fuel_raster.year = 2023
    get_fuel_raster = mocker.patch(
        BASE + "get_fuel_type_raster_by_year",
        new=AsyncMock(return_value=fuel_raster),
    )
    addresser = MagicMock()
    mocker.patch(BASE + "BaseRasterAddresser", return_value=addresser)
    s3_client = MagicMock()
    s3_client_context = mocker.patch(BASE + "S3Client")
    s3_client_context.return_value.__aenter__.return_value = s3_client
    resolve_percent_conifer = mocker.patch(
        BASE + "_resolve_percent_conifer_path",
        new=AsyncMock(side_effect=RuntimeError("missing matching percent-conifer raster")),
    )

    run_datetime = datetime(2024, 7, 1)
    with pytest.raises(RuntimeError, match="missing matching percent-conifer raster"):
        await process_hfi_percent_conifer(RunType.ACTUAL, run_datetime, SFMS_TEST_DATE)

    get_fuel_raster.assert_awaited_once_with(session, 2024)
    resolve_percent_conifer.assert_awaited_once_with(2023, addresser, s3_client)
