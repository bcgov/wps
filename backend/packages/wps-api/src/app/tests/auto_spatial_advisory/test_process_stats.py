from collections.abc import Iterator
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest

from app.auto_spatial_advisory.process_hfi import RunType
from app.auto_spatial_advisory.process_stats import process_sfms_hfi_stats

RUN_DATETIME = datetime(2025, 1, 1, 12, 0, 0)
FOR_DATE = datetime(2025, 1, 1).date()

PROCESSING_STEPS = [
    "process_hfi",
    "process_hfi_elevation",
    "process_high_hfi_area",
    "process_fuel_type_hfi_by_shape",
    "process_hfi_min_wind_speed",
    "process_hfi_percent_conifer",
    "calculate_critical_hours",
    "process_zone_statuses",
]


@dataclass
class ProcessStatsMocks:
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


@pytest.fixture
def mocks() -> Iterator[ProcessStatsMocks]:
    """Patch all processing steps, session scope, and notifications."""
    with ExitStack() as stack:

        def patch_async(target: str) -> AsyncMock:
            return cast(AsyncMock, stack.enter_context(patch(target, new_callable=AsyncMock)))

        base = "app.auto_spatial_advisory.process_stats."
        mock_scope = stack.enter_context(patch(base + "get_async_write_session_scope"))
        mock_scope.return_value.__aenter__.return_value = AsyncMock()
        yield ProcessStatsMocks(
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
        )


@pytest.mark.anyio
async def test_forecast_run_marks_complete(mocks: ProcessStatsMocks):
    await process_sfms_hfi_stats(RunType.FORECAST, RUN_DATETIME, FOR_DATE)
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


@pytest.mark.anyio
async def test_notification_failure_does_not_prevent_completion(mocks: ProcessStatsMocks):
    """A Firebase error in trigger_notifications is swallowed — run is still marked complete."""
    mocks.trigger_notifications.side_effect = Exception("Firebase down")

    await process_sfms_hfi_stats(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)

    mocks.mark_run_parameter_complete.assert_awaited_once()


@pytest.mark.anyio
@pytest.mark.parametrize("fail_step", PROCESSING_STEPS)
async def test_processing_failure_prevents_completion(mocks: ProcessStatsMocks, fail_step: str):
    """A failure in any processing step propagates and prevents marking the run complete."""
    getattr(mocks, fail_step).side_effect = Exception("fail")

    with pytest.raises(Exception):
        await process_sfms_hfi_stats(RunType.ACTUAL, RUN_DATETIME, FOR_DATE)

    mocks.mark_run_parameter_complete.assert_not_called()
