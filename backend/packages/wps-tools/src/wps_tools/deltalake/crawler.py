"""
BCWS Data Mart Crawler

Crawls the BC Wildfire Service Data Mart, downloads CSV files,
and appends to Delta Lake tables on object storage.

Source: https://www.for.gov.bc.ca/ftp/HPR/external/!publish/BCWS_DATA_MART/

Usage:
    python -m wps_tools.deltalake.crawler --help
    python -m wps_tools.deltalake.crawler --years 2023 2024
    python -m wps_tools.deltalake.crawler --all --dry-run
"""

import argparse
import io
import logging
import re
from dataclasses import dataclass
from html.parser import HTMLParser

import numpy as np
import pandas as pd
import pyarrow as pa
import requests
from deltalake import DeltaTable, write_deltalake

from wps_tools.deltalake.config import (
    OBSERVATIONS_TABLE,
    STATIONS_TABLE,
    CLIMATOLOGY_STATS_TABLE,
    OBSERVATIONS_BY_STATION_TABLE,
    DATE_COLUMN,
    STATION_CODE_COLUMN,
    get_storage_options,
    get_table_uri,
)
from wps_tools.deltalake.maintenance import (
    create_checkpoint,
    optimize_table,
    vacuum_table,
    maintain_all_tables,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://www.for.gov.bc.ca/ftp/HPR/external/!publish/BCWS_DATA_MART"


# Alias for backwards compatibility
def get_table_key(table_name: str) -> str:
    """Get the S3 URI for a Delta table. Alias for get_table_uri."""
    return get_table_uri(table_name)


class DirectoryParser(HTMLParser):
    """Parse FTP directory listing HTML to extract links."""

    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value)


def parse_directory_listing(html: str) -> list[str]:
    """Extract links from an FTP directory listing page."""
    parser = DirectoryParser()
    parser.feed(html)
    return parser.links


def get_year_directories(session: requests.Session) -> list[int]:
    """Get list of year directories from the data mart."""
    response = session.get(f"{BASE_URL}/")
    response.raise_for_status()

    links = parse_directory_listing(response.text)
    years = []

    for link in links:
        match = re.search(r"(\d{4})/?$", link)
        if match:
            year = int(match.group(1))
            if 1900 < year < 2100:
                years.append(year)

    return sorted(set(years))


def get_csv_files_for_year(session: requests.Session, year: int) -> list[str]:
    """Get list of CSV files for a specific year."""
    response = session.get(f"{BASE_URL}/{year}/")
    response.raise_for_status()

    links = parse_directory_listing(response.text)
    csv_files = []

    for link in links:
        if link.endswith(".csv"):
            filename = link.split("/")[-1]
            csv_files.append(filename)

    return sorted(csv_files)


@dataclass
class CrawlResult:
    """Result of crawling a single CSV file."""

    year: int
    filename: str
    success: bool
    rows: int = 0
    error: str | None = None


def download_csv(session: requests.Session, year: int, filename: str) -> pd.DataFrame:
    """Download a CSV file and return as DataFrame."""
    url = f"{BASE_URL}/{year}/{filename}"
    response = session.get(url)
    response.raise_for_status()
    return pd.read_csv(io.StringIO(response.text))


def get_existing_dates(table_uri: str, storage_options: dict[str, str]) -> set[str]:
    """Get set of dates already in the Delta table."""
    try:
        dt = DeltaTable(table_uri, storage_options=storage_options)
        df = dt.to_pandas(columns=["date"])
        return set(df["date"].astype(str).unique())
    except Exception as e:
        logger.debug(f"Could not read existing dates: {e}")
        return set()


def process_stations_file(
    session: requests.Session,
    year: int,
    filename: str,
    storage_options: dict[str, str],
    dry_run: bool = False,
) -> CrawlResult:
    """Process station metadata file - append to stations Delta table."""
    try:
        df = download_csv(session, year, filename)
        df["source_year"] = year

        # Ensure consistent types for columns that vary across years
        # ASPECT contains compass directions (N, S, E, W, etc.) but is empty in older files
        # WINDSPEED_HEIGHT contains ranges like "9.0_11.9"
        string_columns = ["ASPECT", "WINDSPEED_HEIGHT"]
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype("string")

        table_uri = get_table_key(STATIONS_TABLE)

        if dry_run:
            logger.info(f"[DRY RUN] Would append {filename} ({len(df)} rows) to {table_uri}")
        else:
            write_deltalake(
                table_uri,
                df,
                mode="append",
                schema_mode="merge",
                storage_options=storage_options,
            )
            logger.info(f"Appended {filename} ({len(df)} rows) to {table_uri}")

        return CrawlResult(year, filename, True, rows=len(df))

    except Exception as e:
        logger.error(f"Error processing {year}/{filename}: {e}")
        return CrawlResult(year, filename, False, error=str(e))


def enrich_stations(
    csv_path: str,
    dry_run: bool = False,
) -> int:
    """
    Enrich the stations Delta table with additional attributes from a CSV file.

    Merges columns like FIRE_CENTRE_CODE, FIRE_ZONE_CODE, ECODIVISION_CODE,
    prep_stn, wind_only, FLAG, etc. into the existing stations table.

    Args:
        csv_path: Path to CSV file with station attributes (must have STATION_CODE column)
        dry_run: If True, don't actually write data

    Returns:
        Number of stations updated
    """
    storage_options = get_storage_options()
    table_uri = get_table_key(STATIONS_TABLE)

    logger.info(f"Enriching stations table from {csv_path}")

    # Load existing stations table
    logger.info("Loading existing stations table...")
    dt = DeltaTable(table_uri, storage_options=storage_options)
    existing_df = dt.to_pandas()
    logger.info(f"Loaded {len(existing_df)} existing station records")

    # Deduplicate by keeping most recent source_year for each station
    if "source_year" in existing_df.columns:
        existing_df = (
            existing_df.sort_values("source_year", ascending=False)
            .drop_duplicates(subset=[STATION_CODE_COLUMN], keep="first")
            .reset_index(drop=True)
        )
        logger.info(f"After deduplication: {len(existing_df)} unique stations")

    # Load CSV with new attributes (try different encodings)
    logger.info(f"Loading attributes from {csv_path}...")
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            new_attrs = pd.read_csv(csv_path, encoding=encoding)
            logger.info(f"Loaded {len(new_attrs)} stations from CSV (encoding: {encoding})")
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Could not read {csv_path} with any supported encoding")

    # Identify columns to add (excluding those already in existing table)
    existing_cols = set(existing_df.columns)
    new_cols = [c for c in new_attrs.columns if c not in existing_cols and c != STATION_CODE_COLUMN]
    merge_cols = [STATION_CODE_COLUMN] + new_cols
    logger.info(f"New columns to add: {new_cols}")

    # Merge on STATION_CODE
    merged_df = existing_df.merge(
        new_attrs[merge_cols],
        on=STATION_CODE_COLUMN,
        how="left",
    )

    # Count how many stations got enriched
    enriched_count = merged_df[new_cols[0]].notna().sum() if new_cols else 0
    logger.info(f"Enriched {enriched_count} of {len(merged_df)} stations")

    if dry_run:
        logger.info(f"[DRY RUN] Would overwrite stations table with {len(merged_df)} rows")
        logger.info(f"[DRY RUN] New schema columns: {new_cols}")
        return enriched_count

    # Overwrite the Delta table
    logger.info(f"Writing enriched stations table to {table_uri}...")
    write_deltalake(
        table_uri,
        merged_df,
        mode="overwrite",
        schema_mode="overwrite",
        storage_options=storage_options,
    )
    logger.info(f"Successfully enriched stations table with {len(new_cols)} new columns")

    return enriched_count


def process_observations_file(
    session: requests.Session,
    year: int,
    filename: str,
    existing_dates: set[str],
    storage_options: dict[str, str],
    dry_run: bool = False,
) -> CrawlResult:
    """Process observation file - append to observations Delta table."""
    try:
        df = download_csv(session, year, filename)

        if "DATE_TIME" not in df.columns:
            logger.warning(f"No DATE_TIME column in {filename}, skipping")
            return CrawlResult(year, filename, False, error="No DATE_TIME column")

        # Parse DATE_TIME and extract partition columns
        df["DATE_TIME"] = pd.to_datetime(df["DATE_TIME"], format="%Y%m%d%H", errors="coerce")
        df["date"] = df["DATE_TIME"].dt.date.astype(str)
        df["year"] = df["DATE_TIME"].dt.year
        df["month"] = df["DATE_TIME"].dt.month

        # Filter out dates that already exist
        initial_rows = len(df)
        df = df[~df["date"].isin(existing_dates)]

        if df.empty:
            logger.info(f"All dates in {filename} already exist, skipping")
            return CrawlResult(year, filename, True, rows=0)

        skipped = initial_rows - len(df)
        if skipped > 0:
            logger.info(f"Skipping {skipped} rows with existing dates in {filename}")

        table_uri = get_table_key(OBSERVATIONS_TABLE)

        if dry_run:
            unique_dates = df["date"].nunique()
            logger.info(
                f"[DRY RUN] Would append {filename}: {unique_dates} days, {len(df)} rows to {table_uri}"
            )
        else:
            write_deltalake(
                table_uri,
                df,
                mode="append",
                schema_mode="merge",
                partition_by=["year", "month"],
                storage_options=storage_options,
            )
            unique_dates = df["date"].nunique()
            logger.info(f"Appended {filename}: {unique_dates} days, {len(df)} rows to {table_uri}")

        return CrawlResult(year, filename, True, rows=len(df))

    except Exception as e:
        logger.error(f"Error processing {year}/{filename}: {e}")
        return CrawlResult(year, filename, False, error=str(e))


def process_csv_file(
    session: requests.Session,
    year: int,
    filename: str,
    existing_dates: set[str],
    storage_options: dict[str, str],
    dry_run: bool = False,
) -> CrawlResult:
    """Route CSV file to appropriate processor based on type."""
    filename_lower = filename.lower()

    if "station" in filename_lower:
        return process_stations_file(session, year, filename, storage_options, dry_run)
    else:
        return process_observations_file(
            session, year, filename, existing_dates, storage_options, dry_run
        )


def crawl_year(
    session: requests.Session,
    year: int,
    existing_dates: set[str],
    storage_options: dict[str, str],
    dry_run: bool = False,
) -> list[CrawlResult]:
    """Crawl and process all CSV files for a year."""
    logger.info(f"Processing year {year}")

    csv_files = get_csv_files_for_year(session, year)
    logger.info(f"Found {len(csv_files)} CSV files for {year}")

    if not csv_files:
        return []

    results = []
    for filename in csv_files:
        result = process_csv_file(session, year, filename, existing_dates, storage_options, dry_run)
        results.append(result)

    return results


def crawl_all(
    years: list[int] | None = None,
    dry_run: bool = False,
    skip_existing: bool = True,
) -> dict[int, list[CrawlResult]]:
    """
    Crawl the BCWS Data Mart and append to Delta Lake tables.

    Args:
        years: List of years to process, or None for all available years
        dry_run: If True, don't actually write data
        skip_existing: If True, skip dates that already exist in the table

    Returns:
        Dictionary mapping years to their crawl results
    """
    session = requests.Session()
    session.headers.update({"User-Agent": "BCWS-DataMart-Crawler/1.0"})

    storage_options = get_storage_options()

    # Get existing dates if skip_existing is enabled
    existing_dates: set[str] = set()
    if skip_existing and not dry_run:
        logger.info("Checking for existing dates in Delta table...")
        existing_dates = get_existing_dates(get_table_key(OBSERVATIONS_TABLE), storage_options)
        logger.info(f"Found {len(existing_dates)} existing dates")

    # Get available years
    available_years = get_year_directories(session)
    logger.info(f"Available years: {available_years}")

    if years:
        years_to_process = [y for y in years if y in available_years]
        missing = set(years) - set(available_years)
        if missing:
            logger.warning(f"Requested years not found: {missing}")
    else:
        years_to_process = available_years

    logger.info(f"Will process years: {years_to_process}")

    all_results = {}
    for year in years_to_process:
        results = crawl_year(session, year, existing_dates, storage_options, dry_run)
        all_results[year] = results

        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        total_rows = sum(r.rows for r in results if r.success)

        if results:
            logger.info(
                f"Year {year}: {successful} successful, {failed} failed, {total_rows} total rows"
            )

    return all_results


def compute_climatology_stats(start_year: int = 1991, end_year: int = 2020):
    """
    Pre-compute climatology statistics for all stations and save to a Delta table.

    This creates a small, fast-to-query table with pre-aggregated percentiles
    for each station and day of year.

    Args:
        start_year: Start year of reference period (default: 1991)
        end_year: End year of reference period (default: 2020)
    """
    storage_options = get_storage_options()
    obs_uri = get_table_key(OBSERVATIONS_TABLE)
    stats_uri = get_table_key(CLIMATOLOGY_STATS_TABLE)

    logger.info(f"Computing climatology stats for {start_year}-{end_year}")

    # Load observations for reference period
    logger.info("Loading observations...")
    dt = DeltaTable(obs_uri, storage_options=storage_options)
    df = dt.to_pandas(
        columns=[
            STATION_CODE_COLUMN,
            DATE_COLUMN,
            "HOURLY_TEMPERATURE",
            "HOURLY_RELATIVE_HUMIDITY",
            "HOURLY_WIND_SPEED",
            "HOURLY_PRECIPITATION",
            "HOURLY_FINE_FUEL_MOISTURE_CODE",
            "HOURLY_INITIAL_SPREAD_INDEX",
            "HOURLY_FIRE_WEATHER_INDEX",
        ],
        filters=[
            ("year", ">=", start_year),
            ("year", "<=", end_year),
        ],
    )
    logger.info(f"Loaded {len(df):,} observations")

    # Add day_of_year column
    df["day_of_year"] = pd.to_datetime(df[DATE_COLUMN]).dt.dayofyear

    # Define aggregation function
    def compute_stats(group):
        result = {}
        for var, prefix in [
            ("HOURLY_TEMPERATURE", "temp"),
            ("HOURLY_RELATIVE_HUMIDITY", "rh"),
            ("HOURLY_WIND_SPEED", "ws"),
            ("HOURLY_PRECIPITATION", "precip"),
            ("HOURLY_FINE_FUEL_MOISTURE_CODE", "ffmc"),
            ("HOURLY_INITIAL_SPREAD_INDEX", "isi"),
            ("HOURLY_FIRE_WEATHER_INDEX", "fwi"),
        ]:
            values = group[var].dropna()
            if len(values) > 0:
                result[f"{prefix}_mean"] = values.mean()
                result[f"{prefix}_p10"] = np.percentile(values, 10)
                result[f"{prefix}_p25"] = np.percentile(values, 25)
                result[f"{prefix}_p50"] = np.percentile(values, 50)
                result[f"{prefix}_p75"] = np.percentile(values, 75)
                result[f"{prefix}_p90"] = np.percentile(values, 90)
            else:
                for suffix in ["mean", "p10", "p25", "p50", "p75", "p90"]:
                    result[f"{prefix}_{suffix}"] = None
        return pd.Series(result)

    logger.info("Computing statistics by station and day of year...")
    stats_df = (
        df.groupby([STATION_CODE_COLUMN, "day_of_year"])
        .apply(compute_stats, include_groups=False)
        .reset_index()
    )
    stats_df = stats_df.rename(columns={STATION_CODE_COLUMN: "station_code"})
    stats_df["ref_start_year"] = start_year
    stats_df["ref_end_year"] = end_year

    logger.info(f"Computed {len(stats_df):,} climatology records")

    # Save to Delta table
    result_table = pa.Table.from_pandas(stats_df)
    write_deltalake(
        stats_uri,
        result_table,
        mode="overwrite",
        storage_options=storage_options,
    )
    logger.info(f"Saved climatology stats to {stats_uri}")


def build_observations_by_station():
    """
    Build a Delta table partitioned by station code.

    Creates one parquet file per station containing all years of observations.
    This enables efficient station-based queries without scanning year/month partitions.
    """
    storage_options = get_storage_options()
    source_uri = get_table_key(OBSERVATIONS_TABLE)
    target_uri = get_table_key(OBSERVATIONS_BY_STATION_TABLE)

    logger.info(f"Building observations by station from {source_uri}")

    # Load all observations
    logger.info("Loading observations from source table...")
    dt = DeltaTable(source_uri, storage_options=storage_options)

    # Get list of unique station codes
    station_df = dt.to_pandas(columns=[STATION_CODE_COLUMN])
    station_codes = sorted(station_df[STATION_CODE_COLUMN].dropna().unique())
    logger.info(f"Found {len(station_codes)} unique stations")

    # Process stations in batches to manage memory
    batch_size = 50
    total_rows = 0

    for i in range(0, len(station_codes), batch_size):
        batch_stations = station_codes[i : i + batch_size]
        logger.info(
            f"Processing stations {i + 1}-{min(i + batch_size, len(station_codes))} of {len(station_codes)}"
        )

        # Load data for this batch of stations
        batch_df = dt.to_pandas(
            filters=[(STATION_CODE_COLUMN, "in", list(batch_stations))]
        )

        if batch_df.empty:
            continue

        # Ensure station_code is the partition column (as integer)
        batch_df["station_code"] = batch_df[STATION_CODE_COLUMN].astype("int64")

        # Drop the redundant year/month columns if present (we're repartitioning)
        # Keep them as regular columns for reference but don't partition by them
        columns_to_keep = [c for c in batch_df.columns if c not in ["year", "month"]]
        batch_df = batch_df[columns_to_keep]

        # Re-add year/month as regular columns (not partition columns)
        batch_df["year"] = pd.to_datetime(batch_df[DATE_COLUMN]).dt.year
        batch_df["month"] = pd.to_datetime(batch_df[DATE_COLUMN]).dt.month

        # Write to Delta table partitioned by station_code
        mode = "append" if i > 0 else "overwrite"
        write_deltalake(
            target_uri,
            batch_df,
            mode=mode,
            schema_mode="merge",
            partition_by=["station_code"],
            storage_options=storage_options,
        )

        total_rows += len(batch_df)
        logger.info(f"Wrote {len(batch_df)} rows for {len(batch_stations)} stations")

    logger.info(f"Completed: {total_rows:,} total rows for {len(station_codes)} stations")
    logger.info(f"Output table: {target_uri}")

    # Run maintenance on the new table
    logger.info("Running maintenance on new table...")
    create_checkpoint(OBSERVATIONS_BY_STATION_TABLE)
    optimize_table(OBSERVATIONS_BY_STATION_TABLE)

    return total_rows


def main():
    parser = argparse.ArgumentParser(
        description="Crawl BCWS Data Mart and append to Delta Lake tables"
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        help="Specific years to process (default: all available)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all available years",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually write data, just show what would be done",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Re-process dates that already exist in the table",
    )
    parser.add_argument(
        "--checkpoint",
        action="store_true",
        help="Create checkpoint to speed up Delta log reads",
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Compact small files after crawling",
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="Remove old files after crawling",
    )
    parser.add_argument(
        "--maintain",
        action="store_true",
        help="Run all maintenance (checkpoint, optimize, vacuum) on all tables",
    )
    parser.add_argument(
        "--climatology",
        action="store_true",
        help="Compute climatology statistics for all stations",
    )
    parser.add_argument(
        "--climatology-start-year",
        type=int,
        default=1991,
        help="Start year for climatology reference period (default: 1991)",
    )
    parser.add_argument(
        "--climatology-end-year",
        type=int,
        default=2020,
        help="End year for climatology reference period (default: 2020)",
    )
    parser.add_argument(
        "--by-station",
        action="store_true",
        help="Build observations_by_station table (partitioned by station code)",
    )
    parser.add_argument(
        "--enrich-stations",
        type=str,
        metavar="CSV_PATH",
        help="Enrich stations table with attributes from CSV (e.g., FIRE_CENTRE_CODE, FIRE_ZONE_CODE)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if not args.years and not args.all and not args.checkpoint and not args.optimize and not args.vacuum and not args.maintain and not args.climatology and not args.by_station and not args.enrich_stations:
        parser.error("Either --years, --all, --checkpoint, --optimize, --vacuum, --maintain, --climatology, --by-station, or --enrich-stations must be specified")

    if args.years or args.all:
        years = None if args.all else args.years

        results = crawl_all(
            years=years,
            dry_run=args.dry_run,
            skip_existing=not args.no_skip_existing,
        )

        # Print summary
        total_success = sum(
            sum(1 for r in yr_results if r.success) for yr_results in results.values()
        )
        total_failed = sum(
            sum(1 for r in yr_results if not r.success) for yr_results in results.values()
        )
        total_rows = sum(
            sum(r.rows for r in yr_results if r.success) for yr_results in results.values()
        )

        print(f"\n{'=' * 50}")
        print("Crawl Complete")
        print(f"{'=' * 50}")
        print(f"Years processed: {len(results)}")
        print(f"Files successful: {total_success}")
        print(f"Files failed: {total_failed}")
        print(f"Total rows: {total_rows:,}")

        if total_failed > 0:
            print("\nFailed files:")
            for year, yr_results in results.items():
                for r in yr_results:
                    if not r.success:
                        print(f"  {year}/{r.filename}: {r.error}")

    if args.maintain and not args.dry_run:
        maintain_all_tables()
    else:
        if args.checkpoint and not args.dry_run:
            create_checkpoint()

        if args.optimize and not args.dry_run:
            optimize_table()

        if args.vacuum and not args.dry_run:
            vacuum_table()

    if args.climatology and not args.dry_run:
        compute_climatology_stats(
            start_year=args.climatology_start_year,
            end_year=args.climatology_end_year,
        )

    if args.by_station and not args.dry_run:
        build_observations_by_station()

    if args.enrich_stations:
        enriched = enrich_stations(args.enrich_stations, dry_run=args.dry_run)
        print(f"\nEnriched {enriched} stations with additional attributes")


if __name__ == "__main__":
    main()
