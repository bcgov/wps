import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Optional, Set, TypedDict
from urllib.parse import urljoin

import aiohttp
from aio_pika import IncomingMessage, connect_robust
from aio_pika.abc import AbstractRobustConnection
from wps_shared.utils.s3_client import S3Client
from wps_shared.utils.time import get_utc_now

from wps_weather.model_variables import GDPS_VARIABLES, HRDPS_VARIABLES, RDPS_VARIABLES
from wps_weather.utils import parse_date_and_run, s3_key_from_eccc_path

logger = logging.getLogger(__name__)

ModelName = Literal["RDPS", "GDPS", "HRDPS"]


class ModelConfig(TypedDict):
    routing_key: str
    description: str
    variables: list[str]


MODEL_CONFIGS: dict[ModelName, ModelConfig] = {
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
class FileToDownload:
    url: str
    s3_key: str


class GribDownloader:
    """
    Downloads and retries failed downloads using aiohttp

    """

    def __init__(self, s3_client: S3Client, max_retries: int = 5):
        """
        Initialize downloader

        :param s3_client: S3Client instance
        :param max_retries: Maximum number of retry attempts per file, defaults to 5
        """
        self.s3_client = s3_client
        self.max_retries = max_retries
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        # reuse session
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def download_and_upload(self, file: FileToDownload) -> bool:
        """
        Download file and upload to S3, and handle retry

        :param file: FileToDownload with URL and S3 key
        :return: True if success, False otherwise
        """
        # skip if already exists
        if await self.s3_client.object_exists(file.s3_key):
            logger.debug(f"Skipping existing file: {file.s3_key}")
            return True

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Downloading {file.url} (attempt {attempt}/{self.max_retries})")

                async with self.session.get(
                    file.url, timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    response.raise_for_status()
                    data = await response.read()

                await self.s3_client.put_object(key=file.s3_key, body=data)
                logger.info(f"✅ Uploaded {file.s3_key}")
                return True

            except Exception as e:
                logger.warning(f"Download attempt {attempt} failed for {file.url}: {e}")

                if attempt < self.max_retries:
                    await asyncio.sleep(10)  # try every 10 seconds
                else:
                    logger.error(
                        f"Failed permanently after {self.max_retries} attempts: {file.url}"
                    )
                    return False


class MessageFilter:
    """
    Filters AMQP messages to only download files we want
    """

    def __init__(self, variables: List[str], run_hours: Optional[Set[str]] = None):
        """
        Initialize filter

        :param variables: Grib variable names to match (case-insensitive)
        :param run_hours: set of run hours to accept, None will accept all run hours
        """
        self.variables = [v.upper() for v in variables]
        self.run_hours = run_hours

    def should_download(self, filename: str) -> bool:
        """
        Check if file matches our filters

        :param filename: GRIB filename to check
        :return: True if file should be downloaded
        """
        # check grib variables
        if not any(var in filename.upper() for var in self.variables):
            return False

        # check run hours
        if self.run_hours:
            try:
                _, run_hour = parse_date_and_run(filename)
                if run_hour not in self.run_hours:
                    return False
            except Exception:
                # false if we can't parse run hours
                return False

        return True


class ECCCGribConsumer:
    """
    Listens to ECCC AMQP feed and downloads GRIB files to S3

    The overall flow is:

    1. AMQP message arrives -> handler puts (FileToDownload, IncomingMessage) into work_queue
    2. Worker gets the tuple from work_queue
    3. After download/upload, worker acks (acknowledges) the AMQP message
    4. If it's a message that we don't want, it will be acknowledged or rejected (ack'd/nack'd)
    """

    AMQP_HOST = "dd.weather.gc.ca"
    AMQP_USER_PASS = "anonymous"
    # connect as anonymous as described here: https://eccc-msc.github.io/open-data/msc-datamart/amqp_en/
    AMQP_URL = f"amqps://{AMQP_USER_PASS}:{AMQP_USER_PASS}@{AMQP_HOST}:5671/"
    EXCHANGE = "xpublic"

    def __init__(
        self,
        s3_client: S3Client,
        s3_prefix: str,
        models: List[str],
        model_configs: dict[ModelName, ModelConfig] = MODEL_CONFIGS,
        run_hours: Optional[Set[str]] = None,
        num_workers: int = 10,
        health_file_path: str = "/tmp/health_check",
    ):
        """
        Initialize consumer

        :param s3_client: S3Client instance for uploading files
        :param s3_prefix: Base S3 prefix for storing files
        :param models: List of model names to consume ex, ['RDPS', 'GDPS']
        :param model_configs: Model config which contains routing key, description, and grib variables
        :param run_hours: set of run hours to accept, None will accept all run hours
        :param num_workers: Number of concurrent download workers, defaults to 5
        :param health_file_path: Path to health check file for openshift, defaults to "/tmp/health_check"
        """
        self.s3_client = s3_client
        self.s3_prefix = s3_prefix.rstrip("/")
        self.models = models
        self.model_configs = model_configs
        self.run_hours = run_hours
        self.num_workers = num_workers
        self.health_file = Path(health_file_path)

        # messages go here, workers consume
        self.work_queue: asyncio.Queue[tuple[FileToDownload, IncomingMessage]] = asyncio.Queue()

        self.stats = {
            "received": 0,
            "filtered": 0,
            "uploaded": 0,
            "failed": 0,
            "start_time": None,
        }

        self._connection: Optional[AbstractRobustConnection] = None
        self._running = False
        self._tasks: List[asyncio.Task] = []

        # filters per model
        self._filters: Dict[str, MessageFilter] = {}
        for model in models:
            config = model_configs.get(model)
            self._filters[model] = MessageFilter(config["variables"], run_hours)

    def _parse_message(self, body: bytes, model_name: str) -> Optional[FileToDownload]:
        """
        Parse AMQP message and return FileToDownload if we want it

        :param body: AMQP message body
        :param model_name: Name of the model this message is from
        :return: FileToDownload if we want this file, None if filtered out
        """
        try:
            # parse message: "{timestamp} {base_url} {rel_path}"
            parts = body.decode("utf-8").strip().split(" ", 2)
            if len(parts) != 3:
                return None

            _, base_url, rel_path = parts
            filename = rel_path.split("/")[-1]

            # filter based on model config
            filter_obj = self._filters.get(model_name)
            if not filter_obj or not filter_obj.should_download(filename):
                self.stats["filtered"] += 1
                logger.debug(f"Filtered [{model_name}]: {filename}")
                return None

            url = urljoin(base_url.rstrip("/") + "/", rel_path)

            # build S3 key
            try:
                s3_key = s3_key_from_eccc_path(self.s3_prefix, url)
            except Exception as e:
                logger.warning(f"Could not parse S3 key from {url}: {e}")
                # simple fallback
                s3_key = f"{self.s3_prefix}/{rel_path}"

            return FileToDownload(url=url, s3_key=s3_key)

        except Exception as e:
            logger.debug(f"Failed to parse message: {e}")
            return None

    def _create_message_handler(self, model_name: ModelName):
        """
        Create message handler for a specific model

        :param model_name: Name of the model
        """

        async def handler(message: IncomingMessage):
            """
            Handle incoming AMQP message, parse and add to work queue

            """
            try:
                self.stats["received"] += 1

                file = self._parse_message(message.body, model_name)
                if not file:
                    # need to acknowledge the message even if we don't want it
                    await message.ack()
                    return

                # add the file and message to the work queue so we can ack the message after download/upload
                await self.work_queue.put((file, message))
                logger.debug(f"Queued [{model_name}]: {file.s3_key}")

            except Exception as e:
                logger.error(f"Handler error for {model_name}: {e}", exc_info=True)
                # reject on unexpected errors
                await message.reject(requeue=False)

        return handler

    async def _worker(self, worker_id: int):
        """
        Worker that processes downloads from queue
        """
        logger.debug(f"Worker {worker_id} started")

        async with GribDownloader(self.s3_client) as downloader:
            while self._running:
                try:
                    # Get work with timeout so we can check _running flag
                    # Get the amqp message from the queue so we can ack after download/upload
                    file, message = await asyncio.wait_for(self.work_queue.get(), timeout=1.0)

                    success = await downloader.download_and_upload(file)

                    if success:
                        # upload successful - acknowledge amqp message
                        await message.ack()
                        self.stats["uploaded"] += 1
                        logger.debug(f"ACKed: {file.s3_key}")
                    else:
                        # upload failed after retries - reject but don't requeue
                        # (requeuing would cause infinite retries)
                        await message.reject(requeue=False)
                        self.stats["failed"] += 1
                        logger.warning(f"Rejected message: {file.s3_key}")

                    self.work_queue.task_done()

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Worker {worker_id} error: {e}", exc_info=True)

        logger.info(f"Worker {worker_id} stopped")

    async def _health_check_worker(self, interval: int = 30):
        """
        Update health file periodically for openshift liveness probe which will check
        if the file has been modified in the last 2 minutes

        Creates/touches the health file every 30 seconds to indicate process is alive
        """
        logger.debug("Health check worker started")

        while self._running:
            try:
                self.health_file.touch()
                logger.debug("Health check file updated")
            except Exception as e:
                logger.error(f"Failed to update health file: {e}")

            await asyncio.sleep(interval)

        logger.info("Health check worker stopped")

    async def _stats_logger(self):
        """
        Log statistics periodically

        """
        while self._running:
            await asyncio.sleep(300)  # 5 minutes
            self._log_stats()

    async def _setup_amqp(self):
        """
        Connect to AMQP and setup subscriptions

        Uses auto-reconnect from aio_pika for resilience
        """
        # connect to amqp  (auto-reconnect built in)
        self._connection = await connect_robust(self.AMQP_URL, timeout=30)

        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=200)

        exchange = await channel.get_exchange(self.EXCHANGE)

        # setup queue for each model
        for model in self.models:
            config = self.model_configs[model]

            # must match pattern specified by: https://eccc-msc.github.io/open-data/msc-datamart/amqp_en/
            # q_anonymous.subscribe.{config_name}.{company_name}
            queue_name = f"q_anonymous.subscribe.{model}.bcgov"

            # don't set exclusive queue, so we can have multiple consumers if needed
            # auto_delete=False so queue persists if consumer disconnects
            queue = await channel.declare_queue(queue_name, exclusive=False, auto_delete=False)

            await queue.bind(exchange, routing_key=config["routing_key"])
            # no_ack=False so we can manually ack (acknowledge) messages after processing
            # we want this so that if something happens to the pod before download/upload, the message will be requeued
            await queue.consume(self._create_message_handler(model), no_ack=False)

            logger.info(f"✅ Subscribed to {model}: {config['routing_key']}")

    async def start(self):
        """Start the consumer"""
        logger.info("Starting consumer...")
        self._running = True
        self.stats["start_time"] = get_utc_now()

        # Connect to AMQP
        await self._setup_amqp()

        # Start worker pool
        for i in range(self.num_workers):
            task = asyncio.create_task(self._worker(i))
            self._tasks.append(task)

        # Start health check worker
        health_task = asyncio.create_task(self._health_check_worker())
        self._tasks.append(health_task)

        # Start stats logger
        stats_task = asyncio.create_task(self._stats_logger())
        self._tasks.append(stats_task)

        logger.info("✅ Consumer started")
        self._log_stats()

    async def run(self):
        """Run until interrupted"""
        try:
            while self._running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupted")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Gracefully shutdown"""
        logger.info("Shutting down...")
        self._running = False

        # Wait for queue to drain (with timeout)
        if not self.work_queue.empty():
            logger.info(f"Waiting for {self.work_queue.qsize()} files to download...")
            try:
                await asyncio.wait_for(self.work_queue.join(), timeout=60)
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for queue to drain")

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Close connection
        if self._connection and not self._connection.is_closed:
            try:
                await asyncio.wait_for(self._connection.close(), timeout=5)
            except asyncio.TimeoutError:
                logger.warning("Timeout closing AMQP connection")

        self._log_stats()
        logger.info("Shutdown complete")

    def _log_stats(self):
        """Simple stats logging"""
        uptime = ""
        if self.stats["start_time"]:
            uptime_delta = get_utc_now() - self.stats["start_time"]
            uptime = f"Uptime: {uptime_delta}"

        logger.info("")
        logger.info("STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Received: {self.stats['received']}")
        logger.info(f"Filtered: {self.stats['filtered']}")
        logger.info(f"Uploaded: {self.stats['uploaded']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Queue Size: {self.work_queue.qsize()}")
        logger.info(f"{uptime}")
        logger.info("=" * 60)
        logger.info("")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.shutdown()
