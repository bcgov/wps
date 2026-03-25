from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.auto_spatial_advisory.process_hfi import RunType
from app.auto_spatial_advisory.process_stats import process_sfms_hfi_stats

ALL_PROCESSING_STEPS = [
    ("app.auto_spatial_advisory.process_stats.process_hfi", AsyncMock),
    ("app.auto_spatial_advisory.process_stats.process_hfi_elevation", AsyncMock),
    ("app.auto_spatial_advisory.process_stats.process_high_hfi_area", AsyncMock),
    ("app.auto_spatial_advisory.process_stats.process_fuel_type_hfi_by_shape", AsyncMock),
    ("app.auto_spatial_advisory.process_stats.process_hfi_min_wind_speed", AsyncMock),
    ("app.auto_spatial_advisory.process_stats.process_hfi_percent_conifer", AsyncMock),
    ("app.auto_spatial_advisory.process_stats.calculate_critical_hours", AsyncMock),
    ("app.auto_spatial_advisory.process_stats.process_zone_statuses", AsyncMock),
]

RUN_DATETIME = datetime(2025, 1, 1, 12, 0, 0)
FOR_DATE = datetime(2025, 1, 1).date()


def patch_all_steps(extra_patches=None):
    """Decorator stack that mocks all processing steps plus session scope and notifications."""
    patches = [
        patch("app.auto_spatial_advisory.process_stats.get_async_write_session_scope"),
        patch(
            "app.auto_spatial_advisory.process_stats.mark_run_parameter_complete",
            new_callable=AsyncMock,
        ),
        patch(
            "app.auto_spatial_advisory.process_stats.trigger_notifications", new_callable=AsyncMock
        ),
        *[patch(target, new_callable=klass) for target, klass in ALL_PROCESSING_STEPS],
    ]
    if extra_patches:
        patches.extend(extra_patches)

    def decorator(func):
        for p in reversed(patches):
            func = p(func)
        return func

    return decorator


@pytest.mark.anyio
@patch_all_steps()
async def test_process_stats_marks_complete(
    mock_zone_statuses,
    mock_critical_hours,
    mock_percent_conifer,
    mock_min_wind_speed,
    mock_fuel_type,
    mock_high_hfi_area,
    mock_hfi_elevation,
    mock_hfi,
    mock_trigger_notifications,
    mock_mark_complete,
    mock_session_scope,
):
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session

    await process_sfms_hfi_stats(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)

    mock_mark_complete.assert_awaited_once()


@pytest.mark.anyio
@patch_all_steps()
async def test_process_stats_calls_trigger_notifications(
    mock_zone_statuses,
    mock_critical_hours,
    mock_percent_conifer,
    mock_min_wind_speed,
    mock_fuel_type,
    mock_high_hfi_area,
    mock_hfi_elevation,
    mock_hfi,
    mock_trigger_notifications,
    mock_mark_complete,
    mock_session_scope,
):
    """trigger_notifications is called after mark_run_parameter_complete."""
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session

    await process_sfms_hfi_stats(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)

    mock_trigger_notifications.assert_awaited_once()


@pytest.mark.anyio
@patch_all_steps()
async def test_trigger_notifications_failure_does_not_propagate(
    mock_zone_statuses,
    mock_critical_hours,
    mock_percent_conifer,
    mock_min_wind_speed,
    mock_fuel_type,
    mock_high_hfi_area,
    mock_hfi_elevation,
    mock_hfi,
    mock_trigger_notifications,
    mock_mark_complete,
    mock_session_scope,
):
    """A Firebase failure in trigger_notifications does not raise and does not prevent completion."""
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session
    mock_trigger_notifications.side_effect = Exception("Firebase down")

    # Should not raise
    await process_sfms_hfi_stats(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)

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
        "trigger_notifications",
    ],
)
@patch_all_steps()
async def test_process_stats_does_not_mark_complete_on_processing_failure(
    mock_zone_statuses,
    mock_critical_hours,
    mock_percent_conifer,
    mock_min_wind_speed,
    mock_fuel_type,
    mock_high_hfi_area,
    mock_hfi_elevation,
    mock_hfi,
    mock_trigger_notifications,
    mock_mark_complete,
    mock_session_scope,
    fail_step,
):
    """A failure in any processing step prevents mark_run_parameter_complete from being called."""
    mock_session = AsyncMock()
    mock_session_scope.return_value.__aenter__.return_value = mock_session

    step_mocks = {
        "process_hfi": mock_hfi,
        "process_hfi_elevation": mock_hfi_elevation,
        "process_high_hfi_area": mock_high_hfi_area,
        "process_fuel_type_hfi_by_shape": mock_fuel_type,
        "process_hfi_min_wind_speed": mock_min_wind_speed,
        "process_hfi_percent_conifer": mock_percent_conifer,
        "calculate_critical_hours": mock_critical_hours,
        "process_zone_statuses": mock_zone_statuses,
        # trigger_notifications failure should NOT prevent completion — tested separately
    }

    if fail_step == "trigger_notifications":
        # notifications failure is swallowed — mark_complete should still be called
        mock_trigger_notifications.side_effect = Exception("fail")
        await process_sfms_hfi_stats(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)
        mock_mark_complete.assert_awaited_once()
    else:
        step_mocks[fail_step].side_effect = Exception("fail")
        with pytest.raises(Exception):
            await process_sfms_hfi_stats(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)
        mock_mark_complete.assert_not_called()
