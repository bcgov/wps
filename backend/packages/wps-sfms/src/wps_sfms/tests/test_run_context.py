"""Tests for the context every step of an SFMS run shares."""

import json
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
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


def gdal_addresser() -> MagicMock:
    """An addresser whose GDAL paths are real strings, so a written manifest serializes cleanly."""
    addresser = MagicMock()
    addresser.gdal_path.side_effect = lambda key: f"/vsis3/some bucket/{key}"
    return addresser


class TestSFMSRunContext:
    """The run context keeps a manifest describing the run it's started for."""

    def test_start_creates_a_manifest_describing_the_run(self):
        run = a_run(date(2026, 6, 1), RunType.FORECAST)

        assert run.datetime_to_process == datetime(2026, 6, 1, 20, tzinfo=timezone.utc)
        assert run.run_type == RunType.FORECAST
        assert run.sfms_run_id == 42
        # the manifest joins to the run's sfms_run row by its id
        assert run.manifest.sfms_run_id == 42
        assert run.manifest.run_type == RunType.FORECAST
        assert run.manifest.for_date == date(2026, 6, 1)
        assert run.manifest.run_datetime == RUN_DATETIME

    @pytest.mark.parametrize(
        "manifest",
        [
            SFMSRunManifest(
                MagicMock(),
                sfms_run_id=42,
                run_type=RunType.FORECAST,
                for_date=date(2025, 7, 4),
                run_datetime=RUN_DATETIME,
            ),
            SFMSRunManifest(
                MagicMock(),
                sfms_run_id=42,
                run_type=RunType.ACTUAL,
                for_date=date(2025, 7, 5),
                run_datetime=RUN_DATETIME,
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

    @pytest.mark.anyio
    async def test_write_manifest_records_the_run_error_and_uploads(self):
        s3_client = MagicMock()
        s3_client.put_object = AsyncMock()
        context = a_run(addresser=gdal_addresser(), s3_client=s3_client)

        await context.write_manifest(RuntimeError("job failed"), step="daily_actuals")

        payload = json.loads(s3_client.put_object.await_args.kwargs["body"])
        assert payload["status"] == "failed"
        assert payload["failed_step"] == "daily_actuals"
        assert payload["failure_message"] == "job failed"

    @pytest.mark.anyio
    async def test_write_manifest_reports_a_failed_upload_without_raising(
        self, mocker: MockerFixture
    ):
        chatops = mocker.patch("wps_sfms.run_context.send_chatops_notification")
        s3_client = MagicMock()
        s3_client.put_object = AsyncMock(side_effect=RuntimeError("s3 down"))
        context = a_run(addresser=gdal_addresser(), s3_client=s3_client)

        await context.write_manifest()

        message, error = chatops.call_args.args
        assert message == "Failed to write SFMS run manifest for actual 2025-07-04"
        assert str(error) == "s3 down"
