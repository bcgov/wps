"""
CSV to Parquet conversion utility for historical time series data.

Converts CSV files to Parquet format with date-based partitioning,
suitable for hosting on object storage and serving via API.

Usage:
    python -m wps_tools.csv_to_parquet input.csv --date-column timestamp --output-dir ./parquet_data
    python -m wps_tools.csv_to_parquet input.csv --date-column timestamp --upload-to-s3 historical/weather
"""

import argparse
import asyncio
import logging
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from wps_shared.utils.s3_client import S3Client

logger = logging.getLogger(__name__)


def csv_to_parquet(
    csv_path: str,
    date_column: str,
    output_dir: str,
    partition_by: str = "date",
) -> list[str]:
    """
    Convert a CSV file to partitioned Parquet files.

    Args:
        csv_path: Path to the input CSV file
        date_column: Name of the column containing timestamps
        output_dir: Directory to write Parquet files
        partition_by: Partition granularity - 'date', 'month', or 'year'

    Returns:
        List of created Parquet file paths
    """
    logger.info(f"Reading CSV from {csv_path}")
    df = pd.read_csv(csv_path, parse_dates=[date_column])

    if date_column not in df.columns:
        raise ValueError(f"Date column '{date_column}' not found in CSV")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    created_files = []

    # Group by partition columns and write separate files
    df["_year"] = df[date_column].dt.year
    df["_month"] = df[date_column].dt.month
    df["_day"] = df[date_column].dt.day

    if partition_by == "year":
        groups = df.groupby(["_year"])
    elif partition_by == "month":
        groups = df.groupby(["_year", "_month"])
    else:  # date (default)
        groups = df.groupby(["_year", "_month", "_day"])

    for keys, group_df in groups:
        if not isinstance(keys, tuple):
            keys = (keys,)

        # Build path like 2024/1/15/original_name.parquet
        int_keys = [int(k) for k in keys]
        path_parts = [str(k) for k in int_keys]
        partition_dir = output_path / "/".join(path_parts)
        partition_dir.mkdir(parents=True, exist_ok=True)

        # Drop partition columns from data
        group_df = group_df.drop(columns=["_year", "_month", "_day"], errors="ignore")

        # Use original CSV filename with .parquet extension
        original_name = Path(csv_path).stem.lower()
        file_path = partition_dir / f"{original_name}.parquet"
        table: pa.Table = pa.Table.from_pandas(group_df, preserve_index=False)  # type: ignore[attr-defined]
        pq.write_table(table, file_path, compression="snappy")
        created_files.append(str(file_path))

    logger.info(f"Created {len(created_files)} Parquet files")
    return created_files


async def upload_parquet_to_s3(local_dir: str, s3_prefix: str) -> list[str]:
    """
    Upload Parquet files from a local directory to S3.

    Args:
        local_dir: Local directory containing Parquet files
        s3_prefix: S3 key prefix (e.g., 'historical/weather')

    Returns:
        List of uploaded S3 keys
    """
    local_path = Path(local_dir)
    parquet_files = list(local_path.rglob("*.parquet"))

    uploaded_keys = []

    async with S3Client() as s3_client:
        for file_path in parquet_files:
            # Preserve partition structure in S3 key
            relative_path = file_path.relative_to(local_path)
            s3_key = f"{s3_prefix}/{relative_path}"

            logger.info(f"Uploading {file_path} to {s3_key}")

            with open(file_path, "rb") as f:
                await s3_client.put_object(s3_key, f.read())

            uploaded_keys.append(s3_key)

    logger.info(f"Uploaded {len(uploaded_keys)} files to S3")
    return uploaded_keys


async def convert_and_upload(
    csv_path: str,
    date_column: str,
    s3_prefix: str,
    partition_by: str = "date",
    keep_local: bool = False,
) -> list[str]:
    """
    Convert CSV to Parquet and upload to S3 in one operation.

    Args:
        csv_path: Path to the input CSV file
        date_column: Name of the column containing timestamps
        s3_prefix: S3 key prefix for uploaded files
        partition_by: Partition granularity - 'date', 'month', or 'year'
        keep_local: If True, keep local Parquet files after upload

    Returns:
        List of uploaded S3 keys
    """
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        # Convert CSV to Parquet
        csv_to_parquet(csv_path, date_column, temp_dir, partition_by)

        # Upload to S3
        uploaded_keys = await upload_parquet_to_s3(temp_dir, s3_prefix)

        if keep_local:
            # Copy to a permanent location
            output_dir = Path(csv_path).parent / f"{Path(csv_path).stem}_parquet"
            shutil.copytree(temp_dir, output_dir, dirs_exist_ok=True)
            logger.info(f"Local Parquet files saved to {output_dir}")

    return uploaded_keys


def main():
    parser = argparse.ArgumentParser(
        description="Convert CSV to Parquet with date-based partitioning"
    )
    parser.add_argument("csv_path", help="Path to the input CSV file")
    parser.add_argument(
        "--date-column",
        required=True,
        help="Name of the column containing timestamps",
    )
    parser.add_argument(
        "--output-dir",
        help="Local directory to write Parquet files (if not uploading to S3)",
    )
    parser.add_argument(
        "--upload-to-s3",
        metavar="PREFIX",
        help="S3 key prefix to upload files to (e.g., 'historical/weather')",
    )
    parser.add_argument(
        "--partition-by",
        choices=["date", "month", "year"],
        default="date",
        help="Partition granularity (default: date)",
    )
    parser.add_argument(
        "--keep-local",
        action="store_true",
        help="Keep local Parquet files after S3 upload",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if args.upload_to_s3:
        asyncio.run(
            convert_and_upload(
                args.csv_path,
                args.date_column,
                args.upload_to_s3,
                args.partition_by,
                args.keep_local,
            )
        )
    elif args.output_dir:
        csv_to_parquet(args.csv_path, args.date_column, args.output_dir, args.partition_by)
    else:
        parser.error("Either --output-dir or --upload-to-s3 must be specified")


if __name__ == "__main__":
    main()
