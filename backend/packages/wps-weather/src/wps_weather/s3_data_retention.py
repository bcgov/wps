import asyncio
import argparse
import logging
from datetime import datetime, timezone

from wps_shared.utils.s3 import apply_retention_policy_on_date_folders
from wps_shared.utils.s3_client import S3Client
from wps_shared.wps_logging import configure_logging
from wps_shared import config


logger = logging.getLogger(__name__)

GRIB_RETENTION_THRESHOLD = int(config.get("GRIB_RETENTION_THRESHOLD"))

S3_PREFIX = "weather_models/prod"
S3_BUCKET = config.get("WX_OBJECT_STORE_BUCKET")
S3_USER_ID = config.get("WX_OBJECT_STORE_USER_ID")
S3_SECRET = config.get("WX_OBJECT_STORE_SECRET")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Apply retention policy to S3 weather model data")

    parser.add_argument(
        "--dry-run", action="store_true", help="Run without actually deleting (for testing)"
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()

    configure_logging()

    logger.info("Starting GRIB S3 Retention Policy Job")
    logger.info(f"Days to retain: {GRIB_RETENTION_THRESHOLD}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(f"Start time: {datetime.now(timezone.utc).isoformat()}")
    logger.info("=" * 60)

    try:
        async with S3Client(
            user_id=S3_USER_ID, secret_key=S3_SECRET, bucket=S3_BUCKET
        ) as s3_client:
            client = s3_client.client

            logger.info("Starting retention policy application...")

            await apply_retention_policy_on_date_folders(
                client=client,
                bucket=S3_BUCKET,
                prefix=S3_PREFIX,
                days_to_retain=GRIB_RETENTION_THRESHOLD,
                dry_run=args.dry_run,
            )

            logger.info("✅ Retention policy completed successfully")
            logger.info(f"End time: {datetime.now(timezone.utc).isoformat()}")

    except Exception as e:
        logger.error(f"Retention policy failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
