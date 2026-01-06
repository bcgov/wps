"""
Generate Web Mercator COGs for SFMS rasters.

This tool converts SFMS fire weather rasters (FWI, DMC, DC, etc.) from
BC Lambert Conformal Conic to Web Mercator COGs for efficient web delivery.

Usage:
    # Single file conversion
    uv run generate_sfms_cog --input /path/to/fwi.tif --output /path/to/fwi_cog.tif

    # From S3 to local
    uv run generate_sfms_cog --s3-input sfms/calculated/forecast/2025-11-02/fwi20251102.tif --output ./fwi_cog.tif

    # From S3 to S3
    uv run generate_sfms_cog --s3-input sfms/calculated/forecast/2025-11-02/fwi20251102.tif --s3-output sfms/cog/forecast/2025-11-02/fwi20251102_cog.tif

    # Batch process to local directory
    uv run generate_sfms_cog --batch-date 20251102 --batch-output-dir ./cogs/

    # Batch S3 → S3 (output files get _3857_cog.tif suffix)
    uv run generate_sfms_cog --batch-date 20251102 --batch-s3-input-prefix sfms/calculated/forecast --batch-s3-output-prefix sfms/cog/forecast
"""

import argparse
import logging
import os
import sys

from osgeo import gdal

from wps_shared import config
from wps_shared.geospatial.cog import generate_web_optimized_cog
from wps_shared.geospatial.geospatial import SpatialReferenceSystem
from wps_shared.utils.s3 import set_s3_gdal_config
from wps_shared.wps_logging import configure_logging

logger = logging.getLogger(__name__)

bucket = config.get("OBJECT_STORE_BUCKET")


def is_production_environment() -> bool:
    """
    Check if object store configuration points to production.

    Returns True if any production indicators are found:
    - Bucket name contains 'prod' or 'production'
    - Server/endpoint contains production domains
    - Environment variable indicates production
    """
    user = config.get("OBJECT_STORE_USER_ID", "")
    indicators = ["prd"]

    # Check server/endpoint
    if user and any(indicator in user.lower() for indicator in indicators):
        return True

    # Check environment variable
    env = os.environ.get("ENVIRONMENT", "").lower()
    if env in ["prod", "production"]:
        return True

    return False


def confirm_production_operation() -> bool:
    """
    Prompt user to confirm operation in production environment.

    Returns True if user confirms, False otherwise.
    """
    print("\n" + "=" * 70)
    print("⚠️  WARNING: PRODUCTION ENVIRONMENT DETECTED")
    print("=" * 70)
    print(f"Bucket: {bucket}")
    print(f"Server: {config.get('OBJECT_STORE_SERVER', 'N/A')}")
    print("\nThis operation will modify data in the production object store.")
    print("=" * 70)

    response = input("\nType 'y' to continue, or anything else to abort: ").strip().lower()

    if response == "y":
        print("✓ Confirmed. Proceeding with operation...\n")
        return True
    else:
        print("✗ Operation cancelled by user.\n")
        return False


def generate_sfms_cog(input_path: str, output_path: str) -> str:
    """
    Generate a Web Mercator COG from an SFMS raster.

    GDAL's Python bindings natively support /vsis3/ paths for both reading
    and writing, so S3 operations are handled automatically.

    :param input_path: Path to input SFMS raster (BC_LCC projection, local or /vsis3/)
    :param output_path: Path for output Web Mercator COG (local or /vsis3/)
    :return: Path to output COG
    """
    logger.info(f"Generating Web Mercator COG for {input_path}")

    # GDAL Python API handles /vsis3/ paths directly - no shell commands needed
    result = generate_web_optimized_cog(
        input_path,
        output_path,
        target_srs=SpatialReferenceSystem.WEB_MERCATOR.srs,
        compression="LZW",
    )

    logger.info(f"COG generated successfully: {output_path}")
    return result


def batch_generate_sfms_cogs(
    date: str,
    raster_types: list[str],
    s3_input_prefix: str = "sfms/calculated/forecast",
    output_dir: str | None = None,
    s3_output_prefix: str | None = None,
) -> list[str]:
    """
    Batch process multiple SFMS rasters for a given date.

    :param date: Date string in format YYYYMMDD
    :param raster_types: List of raster types (e.g., ['fwi', 'dmc', 'dc'])
    :param s3_input_prefix: S3 prefix/folder for input (default: 'sfms/calculated/forecast')
    :param output_dir: Local directory for output COGs (mutually exclusive with s3_output_prefix)
    :param s3_output_prefix: S3 prefix for output COGs (mutually exclusive with output_dir)
    :return: List of output paths
    """
    if not output_dir and not s3_output_prefix:
        raise ValueError("Either output_dir or s3_output_prefix must be provided")
    if output_dir and s3_output_prefix:
        raise ValueError("Cannot specify both output_dir and s3_output_prefix")

    results = []
    date_formatted = f"{date[:4]}-{date[4:6]}-{date[6:8]}"  # YYYY-MM-DD

    for raster_type in raster_types:
        input_path = f"/vsis3/{bucket}/{s3_input_prefix}/{date_formatted}/{raster_type}{date}.tif"

        # Construct output path (local or S3)
        filename = f"{raster_type}{date}_3857_cog.tif"
        if s3_output_prefix:
            output_path = f"/vsis3/{bucket}/{s3_output_prefix}/{date_formatted}/{filename}"
        else:
            output_path = os.path.join(output_dir, filename)

        try:
            result = generate_sfms_cog(input_path, output_path)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {raster_type}: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Generate Web Mercator COGs for SFMS rasters")
    parser.add_argument("--input", help="Input raster path (local or /vsis3/)")
    parser.add_argument("--output", help="Output COG path")
    parser.add_argument("--s3-input", help="S3 key for input (e.g., sfms/calculated/forecast/...)")
    parser.add_argument("--s3-output", help="S3 key for output")
    parser.add_argument("--batch-date", help="Batch process all rasters for a date (YYYYMMDD)")
    parser.add_argument(
        "--batch-types",
        nargs="+",
        default=["fwi", "dmc", "dc", "ffmc", "bui", "isi"],
        help="Raster types for batch processing",
    )
    parser.add_argument(
        "--batch-s3-input-prefix",
        default="sfms/calculated/forecast",
        help="S3 prefix/folder for batch input (default: sfms/calculated/forecast)",
    )
    parser.add_argument("--batch-output-dir", help="Local output directory for batch processing")
    parser.add_argument(
        "--batch-s3-output-prefix",
        help="S3 prefix for batch output (e.g., sfms/cog/forecast). Mutually exclusive with --batch-output-dir",
    )

    args = parser.parse_args()

    set_s3_gdal_config()
    # Enable temp file usage for COG creation to S3 (COG driver requires random write access)
    gdal.SetConfigOption("CPL_VSIL_USE_TEMP_FILE_FOR_RANDOM_WRITE", "YES")
    configure_logging()

    # Check for production environment and require confirmation
    if is_production_environment():
        if not confirm_production_operation():
            logger.info("Operation cancelled by user")
            sys.exit(0)

    # Batch mode
    if args.batch_date:
        if not args.batch_output_dir and not args.batch_s3_output_prefix:
            parser.error(
                "Batch mode requires either --batch-output-dir or --batch-s3-output-prefix"
            )
        if args.batch_output_dir and args.batch_s3_output_prefix:
            parser.error("Cannot specify both --batch-output-dir and --batch-s3-output-prefix")

        output_desc = (
            args.batch_s3_output_prefix if args.batch_s3_output_prefix else args.batch_output_dir
        )
        logger.info(
            f"Batch processing rasters for {args.batch_date} from {args.batch_s3_input_prefix} to {output_desc}"
        )

        results = batch_generate_sfms_cogs(
            args.batch_date,
            args.batch_types,
            s3_input_prefix=args.batch_s3_input_prefix,
            output_dir=args.batch_output_dir,
            s3_output_prefix=args.batch_s3_output_prefix,
        )
        logger.info(f"Batch complete: {len(results)} COGs generated")
        return

    # Single file mode
    if args.s3_input:
        input_path = f"/vsis3/{bucket}/{args.s3_input}"
    elif args.input:
        input_path = args.input
    else:
        parser.error("Either --input or --s3-input required")

    if args.s3_output:
        output_path = f"/vsis3/{bucket}/{args.s3_output}"
    elif args.output:
        output_path = args.output
    else:
        parser.error("Either --output or --s3-output required")

    generate_sfms_cog(input_path, output_path)


if __name__ == "__main__":
    main()
