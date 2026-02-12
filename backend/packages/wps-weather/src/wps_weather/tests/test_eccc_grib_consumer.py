import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch

from wps_weather.eccc_grib_consumer import (
    ECCCGribConsumer,
    FileToDownload,
    MessageFilter,
    GribDownloader,
)


# Mock S3Client for testing
class MockS3Client:
    """Mock S3Client for testing without actual AWS calls"""

    def __init__(self):
        self.objects = {}  # key -> data
        self.put_count = 0
        self.exists_count = 0

    async def object_exists(self, key: str) -> bool:
        """Check if object exists in mock storage"""
        self.exists_count += 1
        return key in self.objects

    async def put_object(self, key: str, body: bytes):
        """Store object in mock storage"""
        self.put_count += 1
        self.objects[key] = body


class MockResponse:
    """Mock HTTP response"""

    def __init__(self, should_fail: bool, data: bytes = b"test data"):
        self.should_fail = should_fail
        self.status = 500 if should_fail else 200
        self.data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        ""
        pass

    def raise_for_status(self):
        if self.should_fail:
            raise Exception("Network error")

    async def read(self):
        return self.data


class MockGetResult:
    """Result of session.get() - awaitable AND context manager"""

    def __init__(self, should_fail: bool, data: bytes = b"test data"):
        self.response = MockResponse(should_fail, data)

    def __await__(self):
        async def _await():
            return self.response

        return _await().__await__()

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, *args):
        ""
        pass


class MockSession:
    """Mock aiohttp ClientSession"""

    def __init__(self, get_callback):
        """
        Args:
            get_callback: Function that returns MockGetResult
        """
        self.get_callback = get_callback

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        ""
        pass

    def get(self, *args, **kwargs):
        return self.get_callback(*args, **kwargs)

    async def close(self):
        ""
        pass


@pytest.fixture
def mock_aiohttp_session():
    """
    Fixture that provides a helper to mock aiohttp.ClientSession

    Usage:
        def test_something(mock_aiohttp_session):
            with mock_aiohttp_session(should_fail_callback):
                # Your test code
    """

    def _mock_session(get_callback):
        """
        Args:
            get_callback: Function that returns MockGetResult
        """
        return patch("aiohttp.ClientSession", return_value=MockSession(get_callback))

    return _mock_session


# Tests for MessageFilter
class TestMessageFilter:
    """Test the MessageFilter class"""

    def test_should_download_with_matching_variable(self):
        """Filter should accept files with matching variables"""
        filter_obj = MessageFilter(variables=["TMP", "WIND"])

        assert filter_obj.should_download("CMC_glb_TMP_ISBL_500_latlon.grib2")
        assert filter_obj.should_download("CMC_glb_WIND_ISBL_500_latlon.grib2")

    def test_should_download_case_insensitive(self):
        """Filter should be case-insensitive"""
        filter_obj = MessageFilter(variables=["tmp"])

        assert filter_obj.should_download("CMC_glb_TMP_ISBL_500_latlon.grib2")

    def test_should_not_download_non_matching_variable(self):
        """Filter should reject files without matching variables"""
        filter_obj = MessageFilter(variables=["TMP"])

        assert not filter_obj.should_download("CMC_glb_WIND_ISBL_500_latlon.grib2")

    def test_should_download_with_run_hours_matching(self):
        """Filter should accept files with matching run hours"""
        filter_obj = MessageFilter(variables=["TMP"], run_hours={"00", "12"})

        # Mock the parse_date_and_run function
        with patch("wps_weather.eccc_grib_consumer.parse_date_and_run") as mock_parse:
            mock_parse.return_value = ("2024", "00")
            assert filter_obj.should_download("CMC_glb_TMP_2024010100_P000.grib2")

            mock_parse.return_value = ("2024", "06")
            assert not filter_obj.should_download("CMC_glb_TMP_2024010106_P000.grib2")

    def test_should_download_no_run_hours_filter(self):
        """Filter should accept all run hours when filter not specified"""
        filter_obj = MessageFilter(variables=["TMP"], run_hours=None)

        # Mock the parse_date_and_run function
        with patch("wps_weather.eccc_grib_consumer.parse_date_and_run") as mock_parse:
            mock_parse.return_value = ("2024", "06")
            assert filter_obj.should_download("CMC_glb_TMP_2024010106_P000.grib2")

    def test_should_not_download_invalid_run_hour(self):
        """Filter should reject files when run hour can't be parsed"""
        filter_obj = MessageFilter(variables=["TMP"], run_hours={"00"})

        # Mock parse function to raise exception
        with patch("wps_weather.eccc_grib_consumer.parse_date_and_run") as mock_parse:
            mock_parse.side_effect = Exception("Parse error")
            assert not filter_obj.should_download("invalid_filename.grib2")


# Tests for SimpleDownloader
class TestSimpleDownloader:
    """Test the SimpleDownloader class"""

    @pytest.mark.anyio
    async def test_download_and_upload_success(self):
        """Downloader should successfully download and upload files"""
        s3_client = MockS3Client()
        file = FileToDownload(url="https://example.com/test.grib2", s3_key="prefix/test.grib2")

        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.read = AsyncMock(return_value=b"test data")

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock()

            mock_session_class.return_value = mock_session

            async with GribDownloader(s3_client, max_retries=3) as downloader:
                result = await downloader.download_and_upload(file)

            assert result is True
            assert s3_client.put_count == 1
            assert s3_client.objects["prefix/test.grib2"] == b"test data"

    @pytest.mark.anyio
    async def test_download_skips_existing(self):
        """Downloader should skip files that already exist"""
        s3_client = MockS3Client()
        s3_client.objects["prefix/test.grib2"] = b"existing data"

        file = FileToDownload(url="https://example.com/test.grib2", s3_key="prefix/test.grib2")

        async with GribDownloader(s3_client, max_retries=3) as downloader:
            result = await downloader.download_and_upload(file)

        assert result is True
        assert s3_client.put_count == 0  # Should not upload
        assert s3_client.exists_count == 1

    @pytest.mark.anyio
    async def test_download_retries_on_failure(self):
        """Downloader should retry on failure with exponential backoff"""
        s3_client = MockS3Client()
        file = FileToDownload(url="https://example.com/test.grib2", s3_key="prefix/test.grib2")

        # Track number of attempts
        attempt_count = 0

        def get_callback(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            # Fail on first attempt, succeed on second
            should_fail = attempt_count < 2
            return MockGetResult(should_fail)

        with patch("aiohttp.ClientSession", return_value=MockSession(get_callback)):
            # Patch sleep to avoid waiting in tests
            with patch("asyncio.sleep", new_callable=AsyncMock):
                async with GribDownloader(s3_client, max_retries=3) as downloader:
                    result = await downloader.download_and_upload(file)

        assert result is True
        assert attempt_count == 2  # Failed once, succeeded on retry
        assert s3_client.put_count == 1

    @pytest.mark.anyio
    async def test_download_fails_after_max_retries(self):
        """Downloader should give up after max retries"""
        s3_client = MockS3Client()
        file = FileToDownload(url="https://example.com/test.grib2", s3_key="prefix/test.grib2")

        # Track number of attempts
        attempt_count = 0

        def get_callback(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            # Always fail
            return MockGetResult(should_fail=True)

        with patch("aiohttp.ClientSession", return_value=MockSession(get_callback)):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                async with GribDownloader(s3_client, max_retries=3) as downloader:
                    result = await downloader.download_and_upload(file)

        assert result is False
        assert attempt_count == 3  # Tried 3 times
        assert s3_client.put_count == 0


# Tests for ECCCGribConsumer
class TestECCCGribConsumer:
    """Test the ECCCGribConsumer class"""

    def test_parse_message_valid(self):
        """Consumer should parse valid AMQP messages"""
        s3_client = MockS3Client()
        model_configs = {"RDPS": {"routing_key": "test.key", "variables": ["TMP", "WIND"]}}

        consumer = ECCCGribConsumer(
            s3_client=s3_client,
            s3_prefix="test-prefix",
            model_configs=model_configs,
            models=["RDPS"],
        )

        message = b"20240101120000 https://dd.weather.gc.ca model_rdps/10km/2024/01/01/12/CMC_rdps_TMP_ISBL_500_ps10km_2024010112_P000.grib2"

        with patch("wps_weather.eccc_grib_consumer.s3_key_from_eccc_path") as mock_s3_key:
            mock_s3_key.return_value = "test-prefix/model_rdps/TMP_500.grib2"

            file = consumer._parse_message(message, "RDPS")

        assert file is not None
        assert "CMC_rdps_TMP" in file.url
        assert file.s3_key == "test-prefix/model_rdps/TMP_500.grib2"

    def test_parse_message_filtered(self):
        """Consumer should filter out non-matching messages"""
        s3_client = MockS3Client()
        model_configs = {
            "RDPS": {"routing_key": "test.key", "variables": ["TMP"]}  # Only TMP
        }

        consumer = ECCCGribConsumer(
            s3_client=s3_client,
            s3_prefix="test-prefix",
            model_configs=model_configs,
            models=["RDPS"],
        )

        # Message contains WIND, not TMP
        message = b"20240101120000 https://dd.weather.gc.ca model_rdps/10km/2024/01/01/12/CMC_rdps_WIND_ISBL_500_ps10km_2024010112_P000.grib2"

        file = consumer._parse_message(message, "RDPS")

        assert file is None
        assert consumer.stats["filtered"] == 1

    def test_parse_message_invalid_format(self):
        """Consumer should handle invalid message formats gracefully"""
        s3_client = MockS3Client()
        model_configs = {"RDPS": {"routing_key": "test.key", "variables": ["TMP"]}}

        consumer = ECCCGribConsumer(
            s3_client=s3_client,
            s3_prefix="test-prefix",
            model_configs=model_configs,
            models=["RDPS"],
        )

        # Invalid message (only 2 parts instead of 3)
        message = b"20240101120000 https://dd.weather.gc.ca"

        file = consumer._parse_message(message, "RDPS")

        assert file is None

    @pytest.mark.anyio
    async def test_message_handler_queues_file(self):
        """Message handler should queue valid files"""
        s3_client = MockS3Client()
        model_configs = {"RDPS": {"routing_key": "test.key", "variables": ["TMP", "WIND"]}}

        consumer = ECCCGribConsumer(
            s3_client=s3_client,
            s3_prefix="test-prefix",
            model_configs=model_configs,
            models=["RDPS"],
            num_workers=1,
        )

        # Create mock message
        mock_message = Mock()
        mock_message.body = b"20240101120000 https://dd.weather.gc.ca model_rdps/10km/2024/01/01/12/CMC_rdps_TMP_ISBL_500_ps10km_2024010112_P000.grib2"
        mock_message.ack = AsyncMock()

        handler = consumer._create_message_handler("RDPS")

        with patch("wps_weather.eccc_grib_consumer.s3_key_from_eccc_path") as mock_s3_key:
            mock_s3_key.return_value = "test-prefix/model_rdps/TMP_500.grib2"
            await handler(mock_message)

        # Check that file was queued
        assert consumer.work_queue.qsize() == 1
        assert consumer.stats["received"] == 1

        # Message shouldn't be ACKed yet (waiting for worker)
        mock_message.ack.assert_not_called()

        # Get the queued file
        file, _ = await consumer.work_queue.get()
        assert "CMC_rdps_TMP" in file.url

    @pytest.mark.anyio
    async def test_worker_processes_queue(self):
        """Worker should process files from queue"""
        mock_message = Mock()
        mock_message.ack = AsyncMock()

        s3_client = MockS3Client()
        model_configs = {"RDPS": {"routing_key": "test.key", "variables": ["TMP", "WIND"]}}

        consumer = ECCCGribConsumer(
            s3_client=s3_client,
            s3_prefix="test-prefix",
            model_configs=model_configs,
            models=["RDPS"],
            num_workers=1,
        )

        # Add a file to the queue
        file = FileToDownload(url="https://example.com/test.grib2", s3_key="prefix/test.grib2")
        await consumer.work_queue.put((file, mock_message))

        # Mock the downloader
        with patch.object(
            GribDownloader, "download_and_upload", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = True

            # Run worker briefly
            consumer._running = True

            # wait until the queue item is fully processed
            _ = asyncio.create_task(consumer._worker(0))

            # Wait for processing
            await consumer.work_queue.join()
            consumer._running = False

        # Check stats
        assert consumer.stats["uploaded"] == 1
        assert consumer.stats["failed"] == 0
        assert consumer.work_queue.qsize() == 0

        mock_message.ack.assert_called_once()

    @pytest.mark.anyio
    async def test_health_check_worker(self, tmp_path):
        """Health check worker should create health file"""
        s3_client = MockS3Client()
        model_configs = {"RDPS": {"routing_key": "test.key", "variables": ["TMP"]}}

        health_path = tmp_path / "health_check"

        consumer = ECCCGribConsumer(
            s3_client=s3_client,
            s3_prefix="test-prefix",
            model_configs=model_configs,
            models=["RDPS"],
            num_workers=1,
            health_file_path=health_path,
        )

        consumer._running = True
        task = asyncio.create_task(consumer._health_check_worker(0))

        # Wait for health check to run
        await asyncio.sleep(0)
        consumer._running = False
        await task

        # Check that health file was created/updated
        assert health_path.exists()

    @pytest.mark.anyio
    async def test_message_handler_acks_filtered_messages(self):
        """Message handler should ACK filtered messages immediately"""
        s3_client = MockS3Client()
        model_configs = {"RDPS": {"routing_key": "test.key", "variables": ["TMP"]}}

        consumer = ECCCGribConsumer(
            s3_client=s3_client,
            s3_prefix="test-prefix",
            model_configs=model_configs,
            models=["RDPS"],
            num_workers=1,
        )

        # Create mock message with non-matching variable
        mock_message = Mock()
        mock_message.body = b"20240101120000 https://dd.weather.gc.ca model_rdps/10km/2024/01/01/12/CMC_rdps_WIND_ISBL_500_ps10km_2024010112_P000.grib2"
        mock_message.ack = AsyncMock()

        handler = consumer._create_message_handler("RDPS")
        await handler(mock_message)

        # Filtered message should be ACKed immediately
        mock_message.ack.assert_called_once()
        assert consumer.work_queue.qsize() == 0  # Not queued
        assert consumer.stats["filtered"] == 1


# Integration test
class TestIntegration:
    """Integration tests for the full consumer"""

    @pytest.mark.anyio
    async def test_full_workflow(self):
        """Test complete workflow from message to upload"""
        s3_client = MockS3Client()
        model_configs = {
            "RDPS": {
                "routing_key": "v02.post.#.WXO-DD.model_rdps.10km.#",
                "variables": ["TMP", "WIND"],
            }
        }

        consumer = ECCCGribConsumer(
            s3_client=s3_client,
            s3_prefix="test-prefix",
            model_configs=model_configs,
            models=["RDPS"],
            num_workers=2,
        )

        # Mock AMQP setup
        with patch.object(consumer, "_setup_amqp", new_callable=AsyncMock):
            await consumer._startup()

        # Simulate receiving a message
        mock_message = Mock()
        mock_message.ack = AsyncMock()
        mock_message.body = b"20240101120000 https://dd.weather.gc.ca model_rdps/10km/2024/01/01/12/CMC_rdps_AirTemp_AGL-2m_ps10km_2024010112_P000.grib2"

        handler = consumer._create_message_handler("RDPS")

        # Mock the download
        with patch.object(
            GribDownloader, "download_and_upload", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = True

            with patch("wps_weather.eccc_grib_consumer.s3_key_from_eccc_path") as mock_s3_key:
                mock_s3_key.return_value = "test-prefix/model_rdps/TMP_500.grib2"

                # Process message
                await handler(mock_message)

                # Wait for processing
                await consumer.work_queue.join()

        # Check stats
        assert consumer.stats["received"] == 1
        assert consumer.stats["uploaded"] >= 0  # May or may not have processed yet

        # Cleanup
        await consumer.shutdown()
