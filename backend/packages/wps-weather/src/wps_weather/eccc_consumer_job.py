import asyncio
import logging
import signal
import argparse

from wps_weather.eccc_grib_consumer import ECCCGribConsumer

from wps_shared.utils.s3_client import S3Client
from wps_shared.wps_logging import configure_logging


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Download Environment Canada weather model data to S3"
    )

    parser.add_argument(
        "--models",
        nargs="+",
        choices=["RDPS", "GDPS", "HRDPS"],
        default=["RDPS", "GDPS", "HRDPS"],
        help="Models to download",
    )

    parser.add_argument(
        "--run-hours",
        nargs="+",
        choices=["00", "06", "12", "18"],
        default=["00", "06", "12", "18"],
        help="Filter by run hours (e.g., --run-hours 00 12)",
    )

    parser.add_argument(
        "--s3-prefix", default="weather_models/prod", help="S3 prefix for storing files"
    )

    parser.add_argument(
        "--max-concurrent-downloads", type=int, default=10, help="Maximum concurrent downloads"
    )

    parser.add_argument(
        "--max-retries", type=int, default=5, help="Maximum retry attempts per file"
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()

    configure_logging()

    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Environment Canada GRIB Consumer")
    logger.info("=" * 60)
    logger.info(f"Models: {', '.join(args.models)}")
    logger.info(f"Run hours: {', '.join(args.run_hours) if args.run_hours else 'All'}")
    logger.info(f"S3 prefix: {args.s3_prefix}")
    logger.info(f"Max downloads: {args.max_concurrent_downloads}")
    logger.info("=" * 60)

    logger.info("Initializing S3 client...")

    async with S3Client() as s3_client:
        try:
            run_hours = set(args.run_hours) if args.run_hours else None

            consumer = ECCCGribConsumer(
                s3_client=s3_client,
                s3_prefix=args.s3_prefix,
                models=args.models,
                run_hours=run_hours,
                max_concurrent_downloads=args.max_concurrent_downloads,
                max_retries=args.max_retries,
            )

            # Setup signal handlers
            def signal_handler(sig, _):
                logger.info(f"Received signal {sig}")
                asyncio.create_task(consumer.shutdown())

            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)

            # Start and run
            await consumer.start()
            await consumer.run()

        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            await consumer.shutdown()
            raise


if __name__ == "__main__":
    asyncio.run(main())
