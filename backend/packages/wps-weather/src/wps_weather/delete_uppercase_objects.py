"""
One-off cleanup: delete the uppercase 4-panel charts and GRIBs left in the WX bucket now that
everything reads and writes lowercase keys for GeoDrive. An uppercase key is only deleted when its
lowercase copy exists, so nothing is lost if the copy step missed a file. Safe to re-run. A dry run
reports how many objects would be deleted.

    python -m wps_weather.delete_uppercase_objects --dry-run
    python -m wps_weather.delete_uppercase_objects --prefixes wx_4panel_charts/20260407/
    python -m wps_weather.delete_uppercase_objects
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
MAX_CONCURRENT_DELETES = 10


async def delete_uppercase(
    s3_client: S3Client, prefix: str, dry_run: bool = False
) -> tuple[int, int, int]:
    """
    Delete every uppercase key under the prefix that has a lowercase copy.

    :param s3_client: Client for the bucket to clean up.
    :param prefix: Only keys under this prefix are deleted.
    :param dry_run: If True, only report what would be deleted.
    :return: The number of objects deleted (or to delete, for a dry run), the number that failed,
        and the number of uppercase keys kept because they have no lowercase copy.
    """
    existing_keys = {key async for key in s3_client.iter_keys(prefix)}
    uppercase_keys = [key for key in existing_keys if key != key.lower()]
    keys_to_delete = sorted(key for key in uppercase_keys if key.lower() in existing_keys)
    kept = len(uppercase_keys) - len(keys_to_delete)
    logger.info("Found %d keys to delete under %s", len(keys_to_delete), prefix)
    for key in sorted(set(uppercase_keys) - set(keys_to_delete)):
        logger.warning("Keeping %s: no lowercase copy", key)

    if dry_run:
        return len(keys_to_delete), 0, kept

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DELETES)

    async def delete(key: str):
        async with semaphore:
            await s3_client.delete_object(key)

    results = await asyncio.gather(*(delete(key) for key in keys_to_delete), return_exceptions=True)

    failures = 0
    for key, result in zip(keys_to_delete, results):
        if isinstance(result, Exception):
            failures += 1
            logger.error("Failed to delete %s: %s", key, result)
    return len(keys_to_delete) - failures, failures, kept


def parse_args():
    parser = argparse.ArgumentParser(description="Delete uppercase WX bucket objects.")
    parser.add_argument("--dry-run", action="store_true", help="Report without deleting anything.")
    parser.add_argument(
        "--prefixes",
        nargs="+",
        default=[f"{FOUR_PANEL_PREFIX}/", f"{WEATHER_MODEL_PREFIX}/"],
        help="Key prefixes to clean up.",
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    configure_logging()

    total_deleted = 0
    total_failed = 0
    total_kept = 0
    async with S3Client(
        user_id=config.get("WX_OBJECT_STORE_USER_ID"),
        secret_key=config.get("WX_OBJECT_STORE_SECRET"),
        bucket=config.get("WX_OBJECT_STORE_BUCKET"),
    ) as s3_client:
        for prefix in args.prefixes:
            deleted, failed, kept = await delete_uppercase(s3_client, prefix, args.dry_run)
            total_deleted += deleted
            total_failed += failed
            total_kept += kept

    logger.info(
        "Deleted: %d, failed: %d, kept without lowercase copy: %d, dry run: %s",
        total_deleted,
        total_failed,
        total_kept,
        args.dry_run,
    )
    if total_failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
