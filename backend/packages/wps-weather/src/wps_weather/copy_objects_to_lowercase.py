"""
One-off migration: copy 4-panel charts and retained GRIBs in the WX bucket to lowercase keys, because
GeoDrive expects lowercase. Originals are left in place, so this is safe while anything still reads
them, and it's safe to re-run. A dry run reports how many objects still need copying.

    python -m wps_weather.copy_objects_to_lowercase --dry-run
    python -m wps_weather.copy_objects_to_lowercase --prefixes wx_4panel_charts/20260407/
    python -m wps_weather.copy_objects_to_lowercase
"""

import argparse
import asyncio
import logging
import sys

from wps_shared import config
from wps_shared.utils.s3_client import S3Client
from wps_shared.wps_logging import configure_logging

from wps_weather.wx_4panel_charts.wx_4panel_chart_addresser import (
    FOUR_PANEL_PREFIX,
    WEATHER_MODEL_PREFIX,
)

logger = logging.getLogger(__name__)

# Matches the default connection pool size of the S3 client.
MAX_CONCURRENT_COPIES = 10


async def copy_to_lowercase(
    s3_client: S3Client, prefix: str, dry_run: bool = False
) -> tuple[int, int]:
    """
    Copy every object under the prefix that has no lowercase copy yet.

    :param s3_client: Client for the bucket to migrate.
    :param prefix: Only keys under this prefix are copied.
    :param dry_run: If True, only report what would be copied.
    :return: The number of objects copied (or to copy, for a dry run), and the number that failed.
    """
    existing_keys = {key async for key in s3_client.iter_keys(prefix)}
    keys_to_copy = sorted(key for key in existing_keys if key.lower() not in existing_keys)
    logger.info("Found %d keys to copy under %s", len(keys_to_copy), prefix)

    if dry_run:
        return len(keys_to_copy), 0

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_COPIES)

    async def copy(key: str):
        async with semaphore:
            await s3_client.copy_object(key, key.lower())

    results = await asyncio.gather(*(copy(key) for key in keys_to_copy), return_exceptions=True)

    failures = 0
    for key, result in zip(keys_to_copy, results):
        if isinstance(result, Exception):
            failures += 1
            logger.error("Failed to copy %s: %s", key, result)
    return len(keys_to_copy) - failures, failures


def parse_args():
    parser = argparse.ArgumentParser(description="Copy WX bucket objects to lowercase keys.")
    parser.add_argument("--dry-run", action="store_true", help="Report without copying anything.")
    parser.add_argument(
        "--prefixes",
        nargs="+",
        default=[f"{FOUR_PANEL_PREFIX}/", f"{WEATHER_MODEL_PREFIX}/"],
        help="Key prefixes to migrate.",
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    configure_logging()

    total_copied = 0
    total_failed = 0
    async with S3Client(
        user_id=config.get("WX_OBJECT_STORE_USER_ID"),
        secret_key=config.get("WX_OBJECT_STORE_SECRET"),
        bucket=config.get("WX_OBJECT_STORE_BUCKET"),
    ) as s3_client:
        for prefix in args.prefixes:
            copied, failed = await copy_to_lowercase(s3_client, prefix, args.dry_run)
            total_copied += copied
            total_failed += failed

    logger.info("Copied: %d, failed: %d, dry run: %s", total_copied, total_failed, args.dry_run)
    if total_failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
