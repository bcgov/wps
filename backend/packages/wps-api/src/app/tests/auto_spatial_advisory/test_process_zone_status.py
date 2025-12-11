import pytest
from pytest import approx
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

from app.auto_spatial_advisory.process_zone_status import (
    advisory_status_already_processed,
    process_zone_statuses,
    calculate_zone_statuses,
    store_all_advisory_zone_status,
)
from wps_shared.db.models.auto_spatial_advisory import (
    AdvisoryZoneStatus,
    HfiClassificationThresholdEnum,
    RunTypeEnum,
)
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.run_type import RunType


@pytest.mark.anyio
async def test_advisory_status_already_processed_true():
    """Test that advisory_status_already_processed returns True when records exist."""
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar.return_value = True
    session.execute = AsyncMock(return_value=result_mock)
    run_param_id = 1
    fuel_id = 1

    result = await advisory_status_already_processed(session, run_param_id, fuel_id)

    assert result is True
    session.execute.assert_called_once()


@pytest.mark.anyio
async def test_advisory_status_already_processed_false():
    """Test that advisory_status_already_processed returns False when no records exist."""
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar.return_value = False
    session.execute = AsyncMock(return_value=result_mock)
    run_param_id = 1
    fuel_id = 1

    result = await advisory_status_already_processed(session, run_param_id, fuel_id)

    assert result is False
    session.execute.assert_called_once()


@pytest.mark.anyio
async def test_process_zone_statuses_already_processed(mocker):
    """Test process_zone_statuses when statuses are already processed."""
    mock_fuel_type_raster = MagicMock(spec=FuelTypeRaster)
    mock_fuel_type_raster.id = 10
    mocker.patch(
        "app.auto_spatial_advisory.process_zone_status.get_fuel_type_raster_by_year",
        return_value=mock_fuel_type_raster,
    )
    mock_session_scope = mocker.patch(
        "app.auto_spatial_advisory.process_zone_status.get_async_write_session_scope"
    )
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session

    mock_get_run_parameters_id = mocker.patch(
        "app.auto_spatial_advisory.process_zone_status.get_run_parameters_id", return_value=1
    )
    mock_advisory_status_already_processed = mocker.patch(
        "app.auto_spatial_advisory.process_zone_status.advisory_status_already_processed",
        return_value=True,
    )

    run_type = RunType.FORECAST
    run_datetime = datetime(2023, 1, 1)
    for_date = date(2023, 1, 1)

    await process_zone_statuses(run_type, run_datetime, for_date)

    mock_get_run_parameters_id.assert_called_once_with(
        mock_session, run_type, run_datetime, for_date
    )
    mock_advisory_status_already_processed.assert_called_once_with(mock_session, 1, 10)

    mock_session.add_all.assert_not_called()


@pytest.mark.anyio
async def test_process_zone_statuses_success(mocker):
    """Test process_zone_statuses full flow."""
    mock_session_scope = mocker.patch(
        "app.auto_spatial_advisory.process_zone_status.get_async_write_session_scope"
    )
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session

    mock_get_run_parameters_id = mocker.patch(
        "app.auto_spatial_advisory.process_zone_status.get_run_parameters_id", return_value=1
    )
    mock_advisory_status_already_processed = mocker.patch(
        "app.auto_spatial_advisory.process_zone_status.advisory_status_already_processed",
        return_value=False,
    )

    fuel_type_raster_mock = MagicMock(spec=FuelTypeRaster)
    fuel_type_raster_mock.id = 10
    mock_get_fuel_type_raster_by_year = mocker.patch(
        "app.auto_spatial_advisory.process_zone_status.get_fuel_type_raster_by_year",
        return_value=fuel_type_raster_mock,
    )

    zone_status = AdvisoryZoneStatus(
        run_parameters=1,
        advisory_shape_id=100,
        advisory_percentage=20.0,
        warning_percentage=10.0,
        fuel_type_raster_id=10,
    )
    mock_calculate_zone_statuses = mocker.patch(
        "app.auto_spatial_advisory.process_zone_status.calculate_zone_statuses",
        return_value=[zone_status],
    )
    mock_store_all_advisory_zone_status = mocker.patch(
        "app.auto_spatial_advisory.process_zone_status.store_all_advisory_zone_status"
    )

    run_type = RunType.FORECAST
    run_datetime = datetime(2023, 1, 1)
    for_date = date(2023, 1, 1)

    await process_zone_statuses(run_type, run_datetime, for_date)

    mock_get_run_parameters_id.assert_called_once_with(
        mock_session, run_type, run_datetime, for_date
    )
    mock_advisory_status_already_processed.assert_called_once_with(mock_session, 1, 10)
    mock_get_fuel_type_raster_by_year.assert_called_once_with(mock_session, 2023)
    mock_calculate_zone_statuses.assert_called_once_with(
        mock_session, 1, run_type, run_datetime, for_date, 10
    )
    mock_store_all_advisory_zone_status.assert_called_once_with(mock_session, [zone_status])


@pytest.mark.anyio
async def test_calculate_zone_statuses(mocker):
    """Test calculate_zone_statuses computation."""
    session = AsyncMock()

    # Mock get_hfi_threshold_ids
    mock_get_hfi_threshold_ids = mocker.patch(
        "app.auto_spatial_advisory.process_zone_status.get_hfi_threshold_ids",
        return_value={
            HfiClassificationThresholdEnum.ADVISORY.value: 1,
            HfiClassificationThresholdEnum.WARNING.value: 2,
        },
    )

    mock_hfi_area_row = MagicMock()
    mock_hfi_area_row.shape_id = 100
    mock_hfi_area_row.combustible_area = 1000.0
    mock_hfi_area_row.threshold = 1
    mock_hfi_area_row.hfi_area = 200.0

    mock_hfi_area_row2 = MagicMock()
    mock_hfi_area_row2.shape_id = 100
    mock_hfi_area_row2.combustible_area = 1000.0
    mock_hfi_area_row2.threshold = 2
    mock_hfi_area_row2.hfi_area = 100.0

    mock_get_hfi_area = mocker.patch(
        "app.auto_spatial_advisory.process_zone_status.get_hfi_area",
        return_value=[mock_hfi_area_row, mock_hfi_area_row2],
    )

    run_parameters_id = 1
    run_type = RunType.FORECAST
    run_datetime = datetime(2023, 1, 1)
    for_date = date(2023, 1, 1)
    fuel_type_raster_id = 10

    result = await calculate_zone_statuses(
        session, run_parameters_id, run_type, run_datetime, for_date, fuel_type_raster_id
    )

    assert len(result) == 1
    status = result[0]
    assert status.run_parameters == 1
    assert status.advisory_shape_id == approx(100)
    assert status.advisory_percentage == approx(20.0)  # 200 / 1000 * 100
    assert status.warning_percentage == approx(10.0)  # 100 / 1000 * 100

    mock_get_hfi_threshold_ids.assert_called_once_with(session)
    mock_get_hfi_area.assert_called_once_with(
        session, RunTypeEnum(run_type.value), run_datetime, for_date, fuel_type_raster_id
    )


@pytest.mark.anyio
async def test_store_all_advisory_zone_status():
    """Test store_all_advisory_zone_status."""
    session = AsyncMock()
    zone_statuses = [MagicMock(spec=AdvisoryZoneStatus), MagicMock(spec=AdvisoryZoneStatus)]

    await store_all_advisory_zone_status(session, zone_statuses)

    session.add_all.assert_called_once_with(zone_statuses)
