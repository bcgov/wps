import asyncio
import os
from pathlib import Path
from urllib.parse import urljoin
import aiohttp
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Set, Tuple
from dataclasses import dataclass, field
from aio_pika import connect_robust, IncomingMessage
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel

from wps_weather.model_variables import RDPS_VARIABLES, GDPS_VARIABLES, HRDPS_VARIABLES
from wps_weather.utils import parse_date_and_run, s3_key_from_eccc_path
from wps_shared.utils.s3_client import S3Client


logger = logging.getLogger(__name__)


MODEL_CONFIGS = {
    "RDPS": {
        "routing_key": "v02.post.#.WXO-DD.model_rdps.10km.#",
        "description": "Regional Deterministic Prediction System (10km)",
        "variables": RDPS_VARIABLES,
    },
    "GDPS": {
        "routing_key": "v02.post.#.WXO-DD.model_gdps.15km.#",
        "description": "Global Deterministic Prediction System",
        "variables": GDPS_VARIABLES,
    },
    "HRDPS": {
        "routing_key": "v02.post.#.WXO-DD.model_hrdps.continental.#",
        "description": "High Resolution Deterministic Prediction System (2.5km)",
        "variables": HRDPS_VARIABLES,
    },
}


@dataclass
class DownloadTask:
    """Represents a file download task with retry logic"""

    url: str
    s3_key: str
    attempt: int = 0
    max_attempts: int = 5
    first_attempt_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_attempt_time: Optional[datetime] = None
    last_error: Optional[str] = None

    @property
    def next_retry_delay(self) -> int:
        """Calculate exponential backoff delay in seconds"""
        return min(30 * (2**self.attempt), 480)

    @property
    def is_expired(self) -> bool:
        """Check if task has been retrying for too long"""
        return datetime.now(timezone.utc) - self.first_attempt_time > timedelta(hours=4)

    @property
    def should_retry(self) -> bool:
        """Check if task should be retried"""
        return self.attempt < self.max_attempts and not self.is_expired


def parse_message(body: bytes) -> Optional[Tuple[str, str, str]]:
    """
    Parse Environment Canada AMQP message

    Format: <timestamp> <base_url> <rel_path>

    Returns:
        (timestamp, base_url, rel_path) or None if parse fails
    """
    try:
        message_str = body.decode("utf-8").strip()
        parts = message_str.split(" ", 2)
        return tuple(parts) if len(parts) == 3 else None
    except Exception as e:
        logger.debug(f"Failed to parse message: {e}")
        return None


def should_download_file(
    rel_path: str, filename: str, variables: List[str], run_hours: Optional[Set[str]] = None
) -> bool:
    """
    Check if file should be downloaded based on filters

    Args:
        rel_path: Relative path from message
        filename: Filename from path
        variables: List of variable names to accept
        run_hours: Set of run hours to accept (e.g., {'00', '12'}), None for all

    Returns:
        True if file matches filters
    """
    # Check variable filter
    if not any(var.upper() in rel_path.upper() for var in variables):
        return False

    # Check run hour filter
    if run_hours:
        try:
            _, run_hour = parse_date_and_run(filename)
            if run_hour not in run_hours:
                return False
        except Exception:
            return False

    return True


def build_s3_key(s3_prefix: str, url: str) -> str:
    """
    Build S3 key from components

    Args:
        s3_prefix: Base S3 prefix
        url: Full URL from message

    Returns:
        Full S3 key path
    """
    try:
        key = s3_key_from_eccc_path(s3_prefix, url)
        return key
    except Exception as e:
        logger.warning(f"Could not parse key from {url}: {e}")
        return os.path.join(s3_prefix, url)


async def download_file(url: str, timeout: int = 300) -> Optional[bytes]:
    """
    Download file from URL

    Args:
        url: URL to download from
        timeout: Timeout in seconds

    Returns:
        File data or None if failed
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                if response.status != 200:
                    logger.error(f"Download failed: HTTP {response.status}")
                    return None
                return await response.read()
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None


class ECCCGribConsumer:
    """
    Downloads Environment Canada GRIB files via AMQP and stores to S3
    """

    AMQP_HOST = "dd.weather.gc.ca"
    AMQP_USER = "anonymous"
    AMQP_PASSWORD = "anonymous"
    AMQP_EXCHANGE = "xpublic"

    def __init__(
        self,
        s3_client: S3Client,
        s3_prefix: str,
        models: List[str],
        run_hours: Optional[Set[str]] = None,
        max_concurrent_downloads: int = 10,
        max_retries: int = 5,
    ):
        """
        Initialize consumer

        Args:
            s3_client: S3Client instance (dependency injection for testing)
            s3_prefix: Base S3 prefix for storing files
            models: List of model names to download
            run_hours: Set of run hours to download (e.g., {'00', '12'}), None for all
            max_concurrent_downloads: Max concurrent download workers
            max_retries: Max retry attempts per file
        """
        self.s3_client = s3_client
        self.s3_prefix = s3_prefix.rstrip("/")
        self.models = models
        self.run_hours = run_hours
        self.max_concurrent_downloads = max_concurrent_downloads
        self.max_retries = max_retries

        self.running = True
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None

        # Work queues
        self.download_queue = asyncio.Queue()
        self.retry_queue: Dict[str, DownloadTask] = {}
        self.failed_tasks: List[DownloadTask] = []

        # Background tasks
        self.workers = []
        self.retry_task = None
        self.monitor_task = None

        # Statistics
        self.stats = {
            "messages_received": 0,
            "messages_filtered": 0,
            "files_uploaded": 0,
            "files_skipped": 0,
            "upload_errors": 0,
            "retry_attempts": 0,
            "permanent_failures": 0,
            "reconnections": 0,
            "last_message_time": None,
            "start_time": None,
        }

        # for openshift to monitor liveness of the pod
        self.health_file = Path("/tmp/health_check")
        self.health_task = None

    async def _update_health(self):
        """
        Update health file with current timestamp
        """
        while self.running:
            try:
                self.health_file.write_text(datetime.now(timezone.utc).isoformat())
            except Exception as e:
                logger.error(f"Failed to update health file: {e}")
            await asyncio.sleep(30)

    async def _monitor_connection(self):
        """Monitor connection and reconnect if needed"""
        while self.running:
            await asyncio.sleep(30)

            if self.connection and self.connection.is_closed:
                logger.warning("Connection closed, reconnecting...")
                await self._reconnect()

    async def _reconnect(self):
        """Reconnect to AMQP and re-setup consumers"""
        try:
            logger.info("Reconnecting...")
            self.stats["reconnections"] += 1

            if self.connection and not self.connection.is_closed:
                await self.connection.close()

            await asyncio.sleep(5)

            if await self._connect_amqp():
                await self._setup_consumers()
                logger.info("✅ Reconnected successfully")
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")

    async def _connect_amqp(self) -> bool:
        """Connect to AMQP server"""
        try:
            url = f"amqps://{self.AMQP_USER}:{self.AMQP_PASSWORD}@{self.AMQP_HOST}:5671/"

            self.connection = await asyncio.wait_for(
                connect_robust(url=url, timeout=30), timeout=35
            )

            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=100)

            logger.info("✅ AMQP connected")
            return True
        except Exception as e:
            logger.error(f"AMQP connection failed: {e}")
            return False

    def _create_callback(self, model_name: str):
        """Create message callback for a model"""
        config = MODEL_CONFIGS[model_name]

        async def callback(message: IncomingMessage):
            try:
                self.stats["messages_received"] += 1
                self.stats["last_message_time"] = datetime.now(timezone.utc)

                parsed = parse_message(message.body)
                if not parsed:
                    return

                _, base_url, rel_path = parsed
                filename = rel_path.split("/")[-1]

                # determine if it's a grib file that we want
                if not should_download_file(
                    rel_path, filename, config["variables"], self.run_hours
                ):
                    self.stats["messages_filtered"] += 1
                    logger.debug(f"Filtered [{model_name}]: {filename}")
                    return

                url = urljoin(base_url.rstrip("/") + "/", rel_path)
                s3_key = build_s3_key(self.s3_prefix, url)

                if s3_key in self.retry_queue:
                    return

                # create a download task and add to queue
                task = DownloadTask(url=url, s3_key=s3_key, max_attempts=self.max_retries)
                await self.download_queue.put(task)
                logger.debug(f"Queued [{model_name}]: {filename}")

            except Exception as e:
                logger.error(f"Callback error: {e}", exc_info=True)

        return callback

    async def _setup_consumers(self):
        """Setup AMQP consumers for all models"""
        exchange = await self.channel.get_exchange(self.AMQP_EXCHANGE)

        for model_name in self.models:
            if model_name not in MODEL_CONFIGS:
                logger.warning(f"Unknown model: {model_name}")
                continue

            config = MODEL_CONFIGS[model_name]

            queue_name = f"q_anonymous.subscribe.{model_name}.bcgov"
            queue = await self.channel.declare_queue(queue_name, exclusive=False)

            await queue.bind(exchange, routing_key=config["routing_key"])
            await queue.consume(self._create_callback(model_name), no_ack=True)

            logger.info(f"✅ Subscribed to {model_name}")
            logger.debug(f"   Routing key: {config['routing_key']}")
            logger.debug(f"   Queue: {queue.name}")

    async def _download_worker(self, worker_id: int):
        """Worker that processes downloads"""
        logger.debug(f"Worker {worker_id} started")

        while self.running:
            try:
                task: DownloadTask = await asyncio.wait_for(self.download_queue.get(), timeout=1.0)

                task.attempt += 1
                task.last_attempt_time = datetime.now(timezone.utc)

                # Check if exists
                if await self.s3_client.object_exists(task.s3_key):
                    self.stats["files_skipped"] += 1
                    logger.debug(f"Already exists: {task.s3_key}")
                    self.download_queue.task_done()
                    continue

                # Download
                logger.info(f"Downloading (attempt {task.attempt}): {task.url}")
                data = await download_file(task.url)

                if data:
                    # Upload to S3
                    await self.s3_client.put_object(key=task.s3_key, body=data)
                    self.stats["files_uploaded"] += 1
                    logger.info(f"✅ Uploaded: {task.s3_key} ({len(data) / 1024 / 1024:.2f} MB)")
                else:
                    # Failed - retry or give up
                    if task.should_retry:
                        self.retry_queue[task.s3_key] = task
                        self.stats["upload_errors"] += 1
                    else:
                        self.failed_tasks.append(task)
                        self.stats["permanent_failures"] += 1

                self.download_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")

        logger.debug(f"Worker {worker_id} stopped")

    async def _retry_worker(self):
        """Worker that processes retry queue"""
        logger.debug("Retry worker started")

        while self.running:
            try:
                current_time = datetime.now(timezone.utc)

                for s3_key, task in list(self.retry_queue.items()):
                    if task.is_expired:
                        self.failed_tasks.append(task)
                        self.stats["permanent_failures"] += 1
                        del self.retry_queue[s3_key]
                        continue

                    if task.last_attempt_time:
                        elapsed = (current_time - task.last_attempt_time).total_seconds()
                        if elapsed >= task.next_retry_delay:
                            task_to_retry = self.retry_queue.pop(s3_key)
                            await self.download_queue.put(task_to_retry)
                            self.stats["retry_attempts"] += 1

                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Retry worker error: {e}")
                await asyncio.sleep(10)

        logger.debug("Retry worker stopped")

    async def start(self):
        """Start the consumer"""
        logger.info("Starting consumer...")

        if not await self._connect_amqp():
            raise ConnectionError("Failed to connect to AMQP")

        # start a task to monitor the connection
        self.health_task = asyncio.create_task(self._update_health())

        # start a task to monitor the connection
        self.monitor_task = asyncio.create_task(self._monitor_connection())

        # Start workers
        for i in range(self.max_concurrent_downloads):
            worker = asyncio.create_task(self._download_worker(i))
            self.workers.append(worker)

        self.retry_task = asyncio.create_task(self._retry_worker())

        # Setup consumers
        await self._setup_consumers()

        self.stats["start_time"] = datetime.now(timezone.utc)
        logger.info("✅ Consumer started")
        self.log_stats()

    async def run(self):
        """Run until stopped"""
        try:
            while self.running:
                await asyncio.sleep(300)
                self.log_stats()
        except KeyboardInterrupt:
            await self.shutdown()

    async def shutdown(self):
        """Gracefully shutdown"""
        logger.info("Shutting down...")
        self.running = False

        # Wait for downloads
        if not self.download_queue.empty():
            logger.info(f"Waiting for {self.download_queue.qsize()} downloads...")
            await self.download_queue.join()

        # Cancel tasks
        all_tasks = self.workers + [self.retry_task, self.monitor_task, self.health_task]
        for task in all_tasks:
            if task:
                task.cancel()

        await asyncio.gather(*[t for t in all_tasks if t], return_exceptions=True)

        if self.connection and not self.connection.is_closed:
            await self.connection.close()

        logger.info("Shutdown complete")
        self.log_stats()

    def log_stats(self):
        """Log statistics"""
        logger.info("=" * 60)
        logger.info("STATISTICS")
        logger.info("=" * 60)
        logger.info(f"  Messages received: {self.stats['messages_received']}")
        logger.info(f"  Messages filtered: {self.stats['messages_filtered']}")
        logger.info(f"  Files uploaded: {self.stats['files_uploaded']}")
        logger.info(f"  Files skipped: {self.stats['files_skipped']}")
        logger.info(f"  Upload errors: {self.stats['upload_errors']}")
        logger.info(f"  Retry attempts: {self.stats['retry_attempts']}")
        logger.info(f"  Permanent failures: {self.stats['permanent_failures']}")
        logger.info(f"  In retry queue: {len(self.retry_queue)}")
        logger.info(f"  Reconnections: {self.stats['reconnections']}")

        if self.stats["last_message_time"]:
            mins = (
                datetime.now(timezone.utc) - self.stats["last_message_time"]
            ).total_seconds() / 60
            logger.info(f"  Last message: {mins:.1f} min ago")

        if self.stats["start_time"]:
            uptime = datetime.now(timezone.utc) - self.stats["start_time"]
            logger.info(f"  Uptime: {uptime}")

        logger.info("=" * 60)
