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
)
from wps_shared.db.models.fuel_type_raster import FuelTypeRaster
from wps_shared.run_type import RunType
from wps_shared.schemas.fba import HfiArea


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

    thresholds_lut = {
        HfiClassificationThresholdEnum.ADVISORY.value: 1,
        HfiClassificationThresholdEnum.WARNING.value: 2,
    }
    hfi_rows = [MagicMock()]  # Mock hfi rows
    mock_gather_zone_status_inputs = mocker.patch(
        "app.auto_spatial_advisory.process_zone_status.gather_zone_status_inputs",
        return_value=(thresholds_lut, hfi_rows),
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
    mock_gather_zone_status_inputs.assert_called_once_with(
        mock_session, run_type, run_datetime, for_date, 10
    )
    mock_calculate_zone_statuses.assert_called_once_with(thresholds_lut, hfi_rows, 1, 10)
    mock_store_all_advisory_zone_status.assert_called_once_with(mock_session, [zone_status])


@pytest.mark.anyio
async def test_calculate_zone_statuses():
    """Test calculate_zone_statuses computation."""
    thresholds_lut = {
        HfiClassificationThresholdEnum.ADVISORY.value: 1,
        HfiClassificationThresholdEnum.WARNING.value: 2,
    }

    hfi_area_row1 = HfiArea(
        shape_id=1,
        source_identifier="2",
        combustible_area=1000.0,
        high_hfi_area_id=11,
        threshold=1,
        hfi_area=200.0,
    )

    hfi_area_row2 = HfiArea(
        shape_id=1,
        source_identifier="2",
        combustible_area=1000.0,
        high_hfi_area_id=12,
        threshold=2,
        hfi_area=100.0,
    )

    hfi_rows = [hfi_area_row1, hfi_area_row2]

    run_parameters_id = 1
    fuel_type_raster_id = 10

    result = await calculate_zone_statuses(
        thresholds_lut, hfi_rows, run_parameters_id, fuel_type_raster_id
    )

    assert len(result) == 1
    status = result[0]
    assert status.run_parameters == 1
    assert status.advisory_shape_id == 1
    assert status.advisory_percentage == approx(20.0)  # 200 / 1000 * 100
    assert status.warning_percentage == approx(10.0)  # 100 / 1000 * 100
    assert status.fuel_type_raster_id == 10


@pytest.mark.anyio
async def test_calculate_zone_statuses_multiple_shapes():
    """Test calculate_zone_statuses with multiple shapes."""
    thresholds_lut = {
        HfiClassificationThresholdEnum.ADVISORY.value: 1,
        HfiClassificationThresholdEnum.WARNING.value: 2,
    }

    hfi_rows = [
        HfiArea(
            shape_id=100,
            combustible_area=1000.0,
            threshold=1,
            hfi_area=200.0,
            source_identifier="2",
            high_hfi_area_id=11,
        ),
        HfiArea(
            shape_id=100,
            combustible_area=1000.0,
            threshold=2,
            hfi_area=100.0,
            source_identifier="2",
            high_hfi_area_id=12,
        ),
        HfiArea(
            shape_id=200,
            combustible_area=500.0,
            threshold=1,
            hfi_area=50.0,
            source_identifier="3",
            high_hfi_area_id=13,
        ),
        HfiArea(
            shape_id=200,
            combustible_area=500.0,
            threshold=2,
            hfi_area=25.0,
            source_identifier="3",
            high_hfi_area_id=14,
        ),
    ]

    run_parameters_id = 1
    fuel_type_raster_id = 10

    result = await calculate_zone_statuses(
        thresholds_lut, hfi_rows, run_parameters_id, fuel_type_raster_id
    )

    assert len(result) == 2
    # Sort by shape_id for consistent assertion
    result.sort(key=lambda x: x.advisory_shape_id)

    status1 = result[0]
    assert status1.advisory_shape_id == 100
    assert status1.advisory_percentage == approx(20.0)
    assert status1.warning_percentage == approx(10.0)

    status2 = result[1]
    assert status2.advisory_shape_id == 200
    assert status2.advisory_percentage == approx(10.0)  # 50 / 500 * 100
    assert status2.warning_percentage == approx(5.0)  # 25 / 500 * 100


@pytest.mark.anyio
async def test_calculate_zone_statuses_zero_combustible_area():
    """Test calculate_zone_statuses with zero combustible area."""
    thresholds_lut = {
        HfiClassificationThresholdEnum.ADVISORY.value: 1,
        HfiClassificationThresholdEnum.WARNING.value: 2,
    }

    hfi_rows = [
        HfiArea(
            shape_id=100,
            combustible_area=0.0,
            threshold=1,
            hfi_area=0.0,
            source_identifier="2",
            high_hfi_area_id=11,
        ),
        HfiArea(
            shape_id=100,
            combustible_area=0.0,
            threshold=2,
            hfi_area=0.0,
            source_identifier="2",
            high_hfi_area_id=12,
        ),
    ]

    run_parameters_id = 1
    fuel_type_raster_id = 10

    result = await calculate_zone_statuses(
        thresholds_lut, hfi_rows, run_parameters_id, fuel_type_raster_id
    )

    assert len(result) == 1
    status = result[0]
    assert status.advisory_percentage == 0.0
    assert status.warning_percentage == 0.0


@pytest.mark.anyio
async def test_store_all_advisory_zone_status():
    """Test store_all_advisory_zone_status."""
    session = AsyncMock()
    zone_statuses = [MagicMock(spec=AdvisoryZoneStatus), MagicMock(spec=AdvisoryZoneStatus)]

    await store_all_advisory_zone_status(session, zone_statuses)

    session.add_all.assert_called_once_with(zone_statuses)
