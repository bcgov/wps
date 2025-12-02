import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from app.auto_spatial_advisory.process_stats import process_sfms_hfi_stats
from app.auto_spatial_advisory.process_hfi import RunType


@pytest.mark.anyio
@patch("app.auto_spatial_advisory.process_stats.process_hfi", new_callable=AsyncMock)
@patch("app.auto_spatial_advisory.process_stats.process_hfi_elevation", new_callable=AsyncMock)
@patch("app.auto_spatial_advisory.process_stats.process_high_hfi_area", new_callable=AsyncMock)
@patch(
    "app.auto_spatial_advisory.process_stats.process_fuel_type_hfi_by_shape", new_callable=AsyncMock
)
@patch("app.auto_spatial_advisory.process_stats.process_hfi_min_wind_speed", new_callable=AsyncMock)
@patch(
    "app.auto_spatial_advisory.process_stats.process_hfi_percent_conifer", new_callable=AsyncMock
)
@patch("app.auto_spatial_advisory.process_stats.calculate_critical_hours", new_callable=AsyncMock)
@patch(
    "app.auto_spatial_advisory.process_stats.mark_run_parameter_complete", new_callable=AsyncMock
)
@patch("app.auto_spatial_advisory.process_stats.process_zone_statuses", new_callable=AsyncMock)
@patch("app.auto_spatial_advisory.process_stats.get_async_write_session_scope")
async def test_process_stats_marks_complete(
    mock_session_scope,
    mock_mark_complete,
    *_,
):
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session
    await process_sfms_hfi_stats(
        RunType.FORECAST, datetime(2025, 1, 1, 12, 0, 0), datetime(2025, 1, 1).date()
    )
    mock_mark_complete.assert_awaited_once()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "fail_step",
    [
        "process_hfi",
        "process_hfi_elevation",
        "process_high_hfi_area",
        "process_fuel_type_hfi_by_shape",
        "process_hfi_min_wind_speed",
        "process_hfi_percent_conifer",
        "calculate_critical_hours",
        "process_zone_statuses",
    ],
)
@patch(
    "app.auto_spatial_advisory.process_stats.mark_run_parameter_complete", new_callable=AsyncMock
)
@patch(
    "app.auto_spatial_advisory.process_stats.get_async_write_session_scope", new_callable=AsyncMock
)
@patch("app.auto_spatial_advisory.process_stats.process_hfi", new_callable=AsyncMock)
@patch("app.auto_spatial_advisory.process_stats.process_hfi_elevation", new_callable=AsyncMock)
@patch("app.auto_spatial_advisory.process_stats.process_high_hfi_area", new_callable=AsyncMock)
@patch(
    "app.auto_spatial_advisory.process_stats.process_fuel_type_hfi_by_shape", new_callable=AsyncMock
)
@patch("app.auto_spatial_advisory.process_stats.process_hfi_min_wind_speed", new_callable=AsyncMock)
@patch(
    "app.auto_spatial_advisory.process_stats.process_hfi_percent_conifer", new_callable=AsyncMock
)
@patch("app.auto_spatial_advisory.process_stats.calculate_critical_hours", new_callable=AsyncMock)
@patch("app.auto_spatial_advisory.process_stats.process_zone_statuses", new_callable=AsyncMock)
async def test_process_stats_does_not_mark_complete_on_failure(
    mock_zone_statuses,
    mock_critical_hours,
    mock_percent_conifer,
    mock_min_wind_speed,
    mock_fuel_type_hfi_by_shape,
    mock_high_hfi_area,
    mock_hfi_elevation,
    mock_hfi,
    mock_session_scope,
    mock_mark_complete,
    fail_step,
):
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session

    # map step names to mocks for easy access
    step_mocks = {
        "process_hfi": mock_hfi,
        "process_hfi_elevation": mock_hfi_elevation,
        "process_high_hfi_area": mock_high_hfi_area,
        "process_fuel_type_hfi_by_shape": mock_fuel_type_hfi_by_shape,
        "process_hfi_min_wind_speed": mock_min_wind_speed,
        "process_hfi_percent_conifer": mock_percent_conifer,
        "calculate_critical_hours": mock_critical_hours,
        "process_zone_statuses": mock_zone_statuses,
    }

    # simulate failure in the specified step
    step_mocks[fail_step].side_effect = Exception("fail")

    with pytest.raises(Exception):
        await process_sfms_hfi_stats(
            RunType.FORECAST, datetime(2025, 1, 1, 12, 0, 0), datetime(2025, 1, 1).date()
        )

    mock_mark_complete.assert_not_called()
