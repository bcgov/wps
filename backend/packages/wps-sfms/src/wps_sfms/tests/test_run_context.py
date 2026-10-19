"""Tests for the context every step of an SFMS run shares."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest
from wps_shared.db.models.sfms_run import SFMSRunLogJobName
from wps_shared.run_type import RunType

from wps_sfms.run_context import SFMSRunContext
from wps_sfms.run_manifest import SFMSRunManifest
from wps_sfms.tests.run_test_utils import (
    RUN_DATETIME,
    a_run,
    datetime_to_process_for,
)

# manifest keys strip this bucket's GDAL prefix
pytestmark = pytest.mark.usefixtures("some_bucket")


class TestSFMSRunContext:
    """The run context keeps a manifest describing the run it's started for."""

    def test_start_creates_a_manifest_describing_the_run(self):
        run = a_run(date(2026, 6, 1), RunType.FORECAST)

        assert run.datetime_to_process == datetime(2026, 6, 1, 20, tzinfo=timezone.utc)
        assert run.run_type == RunType.FORECAST
        assert run.sfms_run_id == 42
        assert run.manifest.run_type == RunType.FORECAST
        assert run.manifest.for_date == date(2026, 6, 1)
        assert run.manifest.run_datetime == RUN_DATETIME

    @pytest.mark.parametrize(
        "manifest",
        [
            SFMSRunManifest(
                MagicMock(),
                run_type=RunType.FORECAST,
                for_date=date(2025, 7, 4),
                run_datetime=RUN_DATETIME,
            ),
            SFMSRunManifest(
                MagicMock(),
                run_type=RunType.ACTUAL, for_date=date(2025, 7, 5), run_datetime=RUN_DATETIME
            ),
        ],
        ids=["another run type", "another target date"],
    )
    def test_rejects_a_manifest_describing_another_run(self, manifest: SFMSRunManifest):
        datetime_to_process = datetime_to_process_for(date(2025, 7, 4))
        s3_client, addresser, fuel_type_raster = MagicMock(), MagicMock(), MagicMock()
        seed_actual_date = date(2025, 7, 3)
        with pytest.raises(ValueError, match="the manifest must describe"):
            SFMSRunContext(
                datetime_to_process,
                RunType.ACTUAL,
                42,
                manifest,
                s3_client,
                addresser,
                fuel_type_raster,
                seed_actual_date,
            )

    @pytest.mark.anyio
    async def test_track_returns_the_action_result(self, tracked_jobs):
        context = a_run()

        async def action():
            return "output"

        assert await context.track(SFMSRunLogJobName.TEMPORAL_FUEL, action) == "output"
        assert tracked_jobs == [SFMSRunLogJobName.TEMPORAL_FUEL]
        assert context.manifest.status == "running"

    @pytest.mark.anyio
    async def test_track_records_the_failed_step(self, tracked_jobs):
        context = a_run()

        async def action():
            raise RuntimeError("step failed")

        with pytest.raises(RuntimeError, match="step failed"):
            await context.track(SFMSRunLogJobName.TEMPORAL_FUEL, action)

        assert context.manifest.failed_step == SFMSRunLogJobName.TEMPORAL_FUEL.value
