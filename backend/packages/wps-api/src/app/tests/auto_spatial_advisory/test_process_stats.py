from collections.abc import Iterator
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime
from typing import cast
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.auto_spatial_advisory.process_hfi import RunType
from app.auto_spatial_advisory.process_stats import process_sfms_hfi_stats

RUN_DATETIME = datetime(2025, 1, 1, 12, 0, 0)
FOR_DATE = datetime(2025, 1, 1).date()

REQUIRED_PROCESSING_STEPS = [
    "validate_fire_zone_raster",
    "process_hfi",
    "process_hfi_elevation",
    "process_high_hfi_area",
    "process_fuel_type_hfi_by_shape",
    "process_hfi_min_wind_speed",
    "calculate_critical_hours",
    "process_zone_statuses",
]


@dataclass
class ProcessStatsMocks:
    validate_fire_zone_raster: AsyncMock
    process_hfi: AsyncMock
    process_hfi_elevation: AsyncMock
    process_high_hfi_area: AsyncMock
    process_fuel_type_hfi_by_shape: AsyncMock
    process_hfi_min_wind_speed: AsyncMock
    process_hfi_percent_conifer: AsyncMock
    calculate_critical_hours: AsyncMock
    process_zone_statuses: AsyncMock
    mark_run_parameter_complete: AsyncMock
    trigger_notifications: AsyncMock
    send_chatops_notification: Mock


@pytest.fixture
def mocks() -> Iterator[ProcessStatsMocks]:
    """Patch all processing steps, session scope, and notifications."""
    with ExitStack() as stack:

        def patch_async(target: str) -> AsyncMock:
            return cast(AsyncMock, stack.enter_context(patch(target, new_callable=AsyncMock)))

        base = "app.auto_spatial_advisory.process_stats."
        for scope_name in ("get_async_read_session_scope", "get_async_write_session_scope"):
            mock_scope = stack.enter_context(patch(base + scope_name))
            mock_scope.return_value.__aenter__.return_value = AsyncMock()
        process_mocks = ProcessStatsMocks(
            validate_fire_zone_raster=patch_async(base + "validate_fire_zone_raster"),
            process_hfi=patch_async(base + "process_hfi"),
            process_hfi_elevation=patch_async(base + "process_hfi_elevation"),
            process_high_hfi_area=patch_async(base + "process_high_hfi_area"),
            process_fuel_type_hfi_by_shape=patch_async(base + "process_fuel_type_hfi_by_shape"),
            process_hfi_min_wind_speed=patch_async(base + "process_hfi_min_wind_speed"),
            process_hfi_percent_conifer=patch_async(base + "process_hfi_percent_conifer"),
            calculate_critical_hours=patch_async(base + "calculate_critical_hours"),
            process_zone_statuses=patch_async(base + "process_zone_statuses"),
            mark_run_parameter_complete=patch_async(base + "mark_run_parameter_complete"),
            trigger_notifications=patch_async(base + "trigger_notifications"),
            send_chatops_notification=stack.enter_context(
                patch(base + "send_chatops_notification")
            ),
        )
        process_mocks.mark_run_parameter_complete.return_value = True
        yield process_mocks


@pytest.mark.anyio
async def test_forecast_run_marks_complete(mocks: ProcessStatsMocks):
    await process_sfms_hfi_stats(RunType.FORECAST, RUN_DATETIME, FOR_DATE)
    mocks.validate_fire_zone_raster.assert_awaited_once()
    mocks.mark_run_parameter_complete.assert_awaited_once()
    mocks.trigger_notifications.assert_awaited_once()


@pytest.mark.anyio
async def test_marks_run_complete_on_success(mocks: ProcessStatsMocks):
    await process_sfms_hfi_stats(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)
    mocks.mark_run_parameter_complete.assert_awaited_once()


@pytest.mark.anyio
async def test_calls_trigger_notifications_after_completion(mocks: ProcessStatsMocks):
    await process_sfms_hfi_stats(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)
    mocks.trigger_notifications.assert_awaited_once()
    assert mocks.trigger_notifications.call_args.kwargs == {"completed_now": True}


@pytest.mark.anyio
async def test_passes_existing_completion_state_to_notifications(
    mocks: ProcessStatsMocks,
):
    mocks.mark_run_parameter_complete.return_value = False

    await process_sfms_hfi_stats(RunType.FORECAST, RUN_DATETIME, FOR_DATE)

    mocks.trigger_notifications.assert_awaited_once()
    assert mocks.trigger_notifications.call_args.kwargs == {"completed_now": False}


@pytest.mark.anyio
async def test_notification_failure_does_not_prevent_completion(mocks: ProcessStatsMocks):
    """A Firebase error in trigger_notifications is swallowed — run is still marked complete."""
    mocks.trigger_notifications.side_effect = Exception("Firebase down")

    await process_sfms_hfi_stats(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)

    mocks.mark_run_parameter_complete.assert_awaited_once()
    mocks.send_chatops_notification.assert_called_once()
    message, exception = mocks.send_chatops_notification.call_args.args
    assert "ASA FCM notifications failed" in message
    assert str(exception) == "Firebase down"
    assert mocks.send_chatops_notification.call_args.kwargs == {"severity": "critical"}


@pytest.mark.anyio
async def test_percent_conifer_failure_alerts_and_allows_processing_to_complete(
    mocks: ProcessStatsMocks,
):
    mocks.process_hfi_percent_conifer.side_effect = RuntimeError("percent-conifer failed")

    await process_sfms_hfi_stats(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)

    mocks.calculate_critical_hours.assert_awaited_once()
    mocks.process_zone_statuses.assert_awaited_once()
    mocks.mark_run_parameter_complete.assert_awaited_once()
    mocks.trigger_notifications.assert_awaited_once()
    mocks.send_chatops_notification.assert_called_once()
    message, exception = mocks.send_chatops_notification.call_args.args
    assert "ASA percent-conifer statistics failed" in message
    assert str(exception) == "percent-conifer failed"
    assert mocks.send_chatops_notification.call_args.kwargs == {"severity": "critical"}


@pytest.mark.anyio
@pytest.mark.parametrize("fail_step", REQUIRED_PROCESSING_STEPS)
async def test_processing_failure_prevents_completion(mocks: ProcessStatsMocks, fail_step: str):
    """A failure in any processing step propagates and prevents marking the run complete."""
    getattr(mocks, fail_step).side_effect = Exception("fail")

    with pytest.raises(Exception):
        await process_sfms_hfi_stats(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)

    mocks.mark_run_parameter_complete.assert_not_called()
    if fail_step == "validate_fire_zone_raster":
        mocks.process_hfi.assert_not_awaited()
