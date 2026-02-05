import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, Mock, patch

from wps_weather.eccc_grib_consumer import (
    ECCCGribConsumer,
    DownloadTask,
    parse_message,
    should_download_file,
)


class TestParseMessage:
    """Tests for parse_message function"""

    def test_valid_message(self):
        """Should parse valid message correctly"""
        message = b"20260204120000.123 https://dd.weather.gc.ca/ path/to/file.grib2"

        result = parse_message(message)

        assert result is not None
        timestamp, base_url, rel_path = result
        assert timestamp == "20260204120000.123"
        assert base_url == "https://dd.weather.gc.ca/"
        assert rel_path == "path/to/file.grib2"

    def test_invalid_message_too_few_parts(self):
        """Should return None when message has too few parts"""
        message = b"two parts"

        result = parse_message(message)

        assert result is None

    def test_empty_message(self):
        """Should return None for empty message"""
        result = parse_message(b"")
        assert result is None

    def test_message_with_spaces_in_path(self):
        """Should handle paths with spaces correctly"""
        message = b"123 https://example.com/ path/with multiple/spaces/file.grib2"

        result = parse_message(message)

        assert result is not None
        _, _, rel_path = result
        assert rel_path == "path/with multiple/spaces/file.grib2"


class TestShouldDownloadFile:
    """Tests for should_download_file function"""

    def test_accept_matching_variable(self):
        """Should accept file with matching variable"""
        result = should_download_file(
            filename="20260205T00Z_MSC_RDPS_Pressure_MSL_RLatLon0.09_PT001H.grib2",
            variables=["Pressure_MSL", "HGT"],
        )

        assert result is True

    def test_reject_non_matching_variable(self):
        """Should reject file without matching variable"""
        result = should_download_file(
            filename="20260205T00Z_MSC_RDPS_Pressure_MSL_RLatLon0.09_PT001H.grib2",
            variables=["TMP", "HGT"],
        )

        assert result is False

    def test_case_insensitive_variable_matching(self):
        """Should match variables case-insensitively"""
        result = should_download_file(
            filename="20260205T00Z_MSC_RDPS_AbsoluteVorticity_IsbL-0500_RLatLon0.09_PT001H.grib2",
            variables=["absolutevorticity"],
        )

        assert result is True

    def test_accept_matching_run_hour(self):
        """Should accept file with matching run hour"""
        result = should_download_file(
            filename="20260205T00Z_MSC_RDPS_AbsoluteVorticity_IsbL-0500_RLatLon0.09_PT001H.grib2",
            variables=["AbsoluteVorticity"],
            run_hours={"00", "12"},
        )

        assert result is True

    def test_reject_non_matching_run_hour(self):
        """Should reject file with non-matching run hour"""
        result = should_download_file(
            filename="20260205T06Z_MSC_RDPS_Pressure_MSL_RLatLon0.09_PT001H.grib2",
            variables=["Pressure_MSL"],
            run_hours={"00", "12"},
        )

        assert result is False

    def test_accept_all_run_hours_when_none_specified(self):
        """Should accept any run hour when filter is None"""
        for hour in ["00", "06", "12", "18"]:
            result = should_download_file(
                filename=f"20260205T{hour}Z_MSC_RDPS_Pressure_MSL_RLatLon0.09_PT001H.grib2",
                variables=["Pressure_msl"],
                run_hours=None,
            )
            assert result is True


class TestDownloadTask:
    """Tests for DownloadTask dataclass"""

    def test_next_retry_delay_exponential_backoff(self):
        """Should calculate exponential backoff correctly"""
        task = DownloadTask(url="https://test", s3_key="test/key")

        # First retry
        task.attempt = 0
        assert task.next_retry_delay == 30

        # Second retry
        task.attempt = 1
        assert task.next_retry_delay == 60

        # Third retry
        task.attempt = 2
        assert task.next_retry_delay == 120

    def test_next_retry_delay_caps_at_480(self):
        """Should cap retry delay at 480 seconds"""
        task = DownloadTask(url="https://test", s3_key="test/key")

        task.attempt = 10
        assert task.next_retry_delay == 480

    def test_should_retry_when_under_max_attempts(self):
        """Should retry when under max attempts"""
        task = DownloadTask(url="https://test", s3_key="test/key", max_attempts=5)

        task.attempt = 3
        assert task.should_retry is True

    def test_should_not_retry_when_at_max_attempts(self):
        """Should not retry when at max attempts"""
        task = DownloadTask(url="https://test", s3_key="test/key", max_attempts=5)

        task.attempt = 5
        assert task.should_retry is False

    def test_is_expired_when_old(self):
        """Should be expired when older than 4 hours"""
        task = DownloadTask(url="https://test", s3_key="test/key")

        # Simulate old task
        task.first_attempt_time = datetime.now(timezone.utc) - timedelta(hours=5)

        assert task.is_expired is True

    def test_is_not_expired_when_recent(self):
        """Should not be expired when recent"""
        task = DownloadTask(url="https://test", s3_key="test/key")

        # Recent task
        task.first_attempt_time = datetime.now(timezone.utc) - timedelta(hours=1)

        assert task.is_expired is False


class TestECCCGribConsumer:
    """Tests for ECCCGribConsumer class"""

    @pytest.fixture
    def mock_s3_client(self):
        """Create mock S3 client"""
        mock = AsyncMock()
        mock.object_exists = AsyncMock(return_value=False)
        mock.put_object = AsyncMock()
        return mock

    @pytest.fixture
    def consumer(self, mock_s3_client):
        """Create consumer instance with mocked dependencies"""
        return ECCCGribConsumer(
            s3_client=mock_s3_client,
            s3_prefix="test-prefix",
            models=["RDPS"],
            run_hours=None,
            max_concurrent_downloads=2,
            max_retries=3,
        )

    def test_initialization(self, consumer):
        """Should initialize with correct default values"""
        assert consumer.s3_prefix == "test-prefix"
        assert consumer.models == ["RDPS"]
        assert consumer.max_concurrent_downloads == 2
        assert consumer.max_retries == 3
        assert consumer.running is True
        assert consumer.stats["messages_received"] == 0

    @pytest.mark.anyio
    async def test_file_already_exists_skipped(self, consumer, mock_s3_client):
        """Should skip download if file already exists in S3"""
        # Mock S3 to say file exists
        mock_s3_client.object_exists.return_value = True

        # Create and queue task
        task = DownloadTask(url="https://test.com/file.grib2", s3_key="test/file.grib2")
        await consumer.download_queue.put(task)

        # Process task with worker
        worker = asyncio.create_task(consumer._download_worker(0))

        try:
            await consumer.download_queue.join()
            mock_s3_client.object_exists.assert_called_once()
            mock_s3_client.put_object.assert_not_called()
        finally:
            consumer.running = False
            await worker

    @pytest.mark.anyio
    async def test_successful_download_and_upload(self, consumer, mock_s3_client):
        """ """
        with patch(
            "wps_weather.eccc_grib_consumer.download_file", AsyncMock(return_value=b"test data")
        ):
            # Add task to queue
            task = DownloadTask(url="https://test.com/file.grib2", s3_key="test/file.grib2")
            await consumer.download_queue.put(task)

            # Start worker (it runs in background)
            worker_task = asyncio.create_task(consumer._download_worker(0))

            try:
                # Wait for queue to be empty
                await consumer.download_queue.join()

                mock_s3_client.put_object.assert_called_once_with(
                    key="test/file.grib2", body=b"test data"
                )

            finally:
                # Clean shutdown
                consumer.running = False
                await worker_task

    @pytest.mark.anyio
    async def test_failed_download_added_to_retry_queue(self, consumer):
        """Should add failed download to retry queue"""
        # Mock failed download
        with patch("wps_weather.eccc_grib_consumer.download_file", AsyncMock(return_value=None)):
            task = DownloadTask(url="https://test.com/file.grib2", s3_key="test/file.grib2")
            await consumer.download_queue.put(task)

            # Process
            worker_task = asyncio.create_task(consumer._download_worker(0))

            try:
                # Wait for queue to be empty
                await consumer.download_queue.join()
                assert "test/file.grib2" in consumer.retry_queue
            finally:
                # Clean shutdown
                consumer.running = False
                await worker_task

    @pytest.mark.anyio
    async def test_retry_worker_retries_expired_tasks(self, consumer):
        """Should retry tasks after delay expires"""
        # Create task that's ready for retry
        task = DownloadTask(url="https://test.com/file.grib2", s3_key="test/file.grib2")
        task.attempt = 1
        task.last_attempt_time = datetime.now(timezone.utc) - timedelta(seconds=100)

        # Add to retry queue
        consumer.retry_queue["test/file.grib2"] = task

        # Run retry worker briefly
        retry_worker = asyncio.create_task(consumer._retry_worker())

        try:
            await consumer.download_queue.join()
            assert "test/file.grib2" in consumer.retry_queue
        finally:
            # Clean shutdown
            consumer.running = False
            await retry_worker

    @pytest.mark.anyio
    async def test_callback_filters_by_variables(self, consumer, mock_s3_client):
        """Should filter messages based on variable list"""
        # Create callback for RDPS
        callback = consumer._create_callback("RDPS")

        # Mock message with non-matching variable
        mock_message = Mock()
        mock_message.body = b"123 https://dd.weather.gc.ca/ path/CMC_reg_WIND_file.grib2"

        await callback(mock_message)

        # Should be filtered
        assert consumer.download_queue.empty()

    @pytest.mark.anyio
    async def test_callback_queues_matching_files(self, consumer):
        """Should queue files that match filters"""
        callback = consumer._create_callback("RDPS")

        # Mock message with matching variable
        mock_message = Mock()
        mock_message.body = b"123 https://dd.weather.gc.ca/ path/20260205T00Z_RDPS_AbsoluteVorticity_IsbL-0500.grib2"

        with patch(
            "wps_weather.eccc_grib_consumer.build_s3_key",
            return_value="path/20260205T00Z_RDPS_AbsoluteVorticity_IsbL-0500.grib2",
        ):
            await callback(mock_message)

        # Should be queued
        assert consumer.stats["messages_received"] == 1
        assert consumer.stats["messages_filtered"] == 0
        assert not consumer.download_queue.empty()

    @pytest.mark.anyio
    async def test_health_file_updated(self, consumer, tmp_path):
        """Should update health file periodically
        tmp_path is a built in pytest fixture
        """

        consumer.health_file = tmp_path / "health_check"

        # Start health update task
        health_task = asyncio.create_task(consumer._update_health())
        await asyncio.sleep(0.1)

        # Stop task
        consumer.running = False
        await health_task

        # Verify file was created
        assert consumer.health_file.exists()


class TestConsumerWorkflow:
    """Integration-style tests for complete workflows"""

    @pytest.mark.anyio
    async def test_complete_download_workflow(self):
        """Test complete workflow from message to S3 upload"""
        # Setup
        mock_s3 = AsyncMock()
        mock_s3.object_exists = AsyncMock(return_value=False)
        mock_s3.put_object = AsyncMock()

        consumer = ECCCGribConsumer(
            s3_client=mock_s3, s3_prefix="test", models=["RDPS"], max_concurrent_downloads=1
        )

        # Mock download function
        with patch(
            "wps_weather.eccc_grib_consumer.download_file", AsyncMock(return_value=b"grib data")
        ):
            # Simulate receiving a message
            callback = consumer._create_callback("RDPS")
            message = Mock()
            message.body = b"123 https://dd.weather.gc.ca/ path/20260205T00Z_MSC_GDPS_AbsoluteVorticity_IsbL-0500_LatLon0.15_PT000H.grib2"

            with patch(
                "wps_weather.eccc_grib_consumer.build_s3_key",
                return_value="test/2026-02-02/rdps/00/file.grib2",
            ):
                await callback(message)

            # Start worker to process
            worker = asyncio.create_task(consumer._download_worker(0))
            await consumer.download_queue.join()
            consumer.running = False
            await worker

            mock_s3.put_object.assert_called_once()

    @pytest.mark.anyio
    async def test_retry_mechanism_eventually_succeeds(self):
        """Test that retry mechanism works when download eventually succeeds"""
        mock_s3 = AsyncMock()
        mock_s3.object_exists = AsyncMock(return_value=False)
        mock_s3.put_object = AsyncMock()

        consumer = ECCCGribConsumer(
            s3_client=mock_s3, s3_prefix="test", models=["RDPS"], max_concurrent_downloads=1
        )

        # Mock download to fail first time, succeed second time
        download_results = [None, b"success"]
        with patch(
            "wps_weather.eccc_grib_consumer.download_file", AsyncMock(side_effect=download_results)
        ):
            # First attempt - should fail
            task = DownloadTask(url="https://test.com/file.grib2", s3_key="test/file.grib2")
            await consumer.download_queue.put(task)

            worker = asyncio.create_task(consumer._download_worker(0))
            await consumer.download_queue.join()

            # Task should be in retry queue
            assert "test/file.grib2" in consumer.retry_queue

            # Manually trigger retry
            retry_task = consumer.retry_queue.pop("test/file.grib2")
            retry_task.last_attempt_time = datetime.now(timezone.utc) - timedelta(seconds=100)
            await consumer.download_queue.put(retry_task)

            await consumer.download_queue.join()
            consumer.running = False
            await worker

            mock_s3.put_object.assert_called_once()
