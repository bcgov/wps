"""
Hourly sync for BCWS Data Mart observations.

Syncs new weather observations to Delta Lake, fetching only data newer than
what already exists.

Usage:
    python -m wps_deltalake.ftp_sync
    python -m wps_deltalake.ftp_sync --dry-run
"""

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd
import requests
from deltalake import DeltaTable, write_deltalake

from wps_deltalake.config import (
    OBSERVATIONS_TABLE,
    DATE_COLUMN,
    get_storage_options,
    get_table_uri,
)
from wps_deltalake.crawler import (
    get_csv_files_for_year,
    download_csv,
)

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    success: bool
    new_rows: int = 0
    error: str | None = None


def get_max_timestamp(storage_options: dict[str, str]) -> datetime | None:
    """Get the maximum timestamp in the observations table."""
    try:
        dt = DeltaTable(get_table_uri(OBSERVATIONS_TABLE), storage_options=storage_options)
        df = dt.to_pandas(columns=[DATE_COLUMN])
        if df.empty:
            return None
        max_ts = pd.to_datetime(df[DATE_COLUMN]).max()
        return max_ts.to_pydatetime() if pd.notna(max_ts) else None
    except Exception as e:
        logger.warning(f"Could not read max timestamp: {e}")
        return None


def sync_hourly(dry_run: bool = False) -> SyncResult:
    """Sync latest observations, only rows newer than existing data."""
    now = datetime.now(tz=timezone.utc)
    year = now.year
    storage_options = get_storage_options()

    logger.info(f"Starting hourly sync at {now.isoformat()}")

    session = requests.Session()
    session.headers.update({"User-Agent": "BCWS-DataMart-Sync/1.0"})

    try:
        # Get latest observation file
        files = [f for f in get_csv_files_for_year(session, year) if "station" not in f.lower()]
        if not files:
            logger.warning(f"No observation files found for {year}")
            return SyncResult(success=True)

        filename = files[-1]
        logger.info(f"Downloading {year}/{filename}")

        df = download_csv(session, year, filename)

        # Parse timestamps and filter to new data only
        df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], format="%Y%m%d%H", errors="coerce")

        max_existing = get_max_timestamp(storage_options)
        if max_existing:
            df = df[df[DATE_COLUMN] > max_existing]
            logger.info(f"Filtered to {len(df)} rows after {max_existing}")

        if df.empty:
            logger.info("No new observations")
            return SyncResult(success=True)

        # Add partition columns
        df["date"] = df[DATE_COLUMN].dt.date.astype(str)
        df["year"] = df[DATE_COLUMN].dt.year
        df["month"] = df[DATE_COLUMN].dt.month

        if dry_run:
            logger.info(f"[DRY RUN] Would append {len(df)} rows")
            return SyncResult(success=True, new_rows=len(df))

        write_deltalake(
            get_table_uri(OBSERVATIONS_TABLE),
            df,
            mode="append",
            schema_mode="merge",
            partition_by=["year", "month"],
            storage_options=storage_options,
        )
        logger.info(f"Appended {len(df)} rows")

        return SyncResult(success=True, new_rows=len(df))

    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        return SyncResult(success=False, error=str(e))


def main():
    parser = argparse.ArgumentParser(description="Sync latest BCWS observations")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    result = sync_hourly(dry_run=args.dry_run)
    print(f"\nSync: {'OK' if result.success else 'FAILED'}, {result.new_rows} new rows")
    if result.error:
        print(f"Error: {result.error}")

    sys.exit(os.EX_OK if result.success else os.EX_SOFTWARE)


if __name__ == "__main__":
    main()
