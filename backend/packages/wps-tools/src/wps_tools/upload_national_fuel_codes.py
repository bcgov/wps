"""
Upload the national fuel lookup that describes every SFMS temporal fuel raster.

The frontend labels and colours temporal fuel rasters from this JSON copy of
``wps_shared.sfms.national_fuel_lookup.NATIONAL_FUEL_CODES``; nothing in the SFMS jobs reads it. Re-run
it against every environment whenever that table changes.

Usage:
    # Upload to the object store configured in .env
    uv run python -m wps_tools.upload_national_fuel_codes

    # Print the JSON without uploading it
    uv run python -m wps_tools.upload_national_fuel_codes --dry-run
"""

import argparse
import asyncio
import logging
import sys

from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser
from wps_shared.sfms.national_fuel_lookup import NATIONAL_FUEL_CODES
from wps_shared.utils.s3_client import S3Client
from wps_shared.wps_logging import configure_logging

from wps_tools.generate_sfms_cog import confirm_production_operation, is_production_environment

logger = logging.getLogger(__name__)


def national_fuel_codes_json() -> bytes:
    return NATIONAL_FUEL_CODES.model_dump_json(indent=2).encode()


async def upload_national_fuel_codes(s3_client: S3Client) -> None:
    key = SFMSNGRasterAddresser().get_national_fuel_codes_key()
    await s3_client.put_object(key=key, body=national_fuel_codes_json())
    logger.info(
        "Uploaded %s national fuel codes to %s/%s",
        len(NATIONAL_FUEL_CODES.fuel_codes),
        s3_client.bucket,
        key,
    )


async def _upload() -> None:
    async with S3Client() as s3_client:
        await upload_national_fuel_codes(s3_client)


def main():
    parser = argparse.ArgumentParser(
        description="Upload the national fuel lookup that describes SFMS temporal fuel rasters"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print the JSON instead of uploading it"
    )
    args = parser.parse_args()

    if args.dry_run:
        print(national_fuel_codes_json().decode())
        return

    configure_logging()
    if is_production_environment() and not confirm_production_operation():
        logger.info("Operation cancelled by user")
        sys.exit(0)

    asyncio.run(_upload())


if __name__ == "__main__":
    main()
