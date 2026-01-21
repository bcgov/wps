"""Delta Lake tools for BCWS weather data.

This module provides utilities for:
- Crawling the BCWS Data Mart and loading into Delta Lake tables
- Converting CSV files to Parquet format
- Maintaining Delta Lake tables (checkpoint, optimize, vacuum)
- Testing Delta Sharing protocol implementations

Usage:
    # Crawler
    python -m wps_tools.deltalake.crawler --help
    python -m wps_tools.deltalake.crawler --years 2023 2024
    python -m wps_tools.deltalake.crawler --enrich-stations /path/to/stations.csv

    # Maintenance
    python -m wps_tools.deltalake.maintenance --help
    python -m wps_tools.deltalake.maintenance --all
    python -m wps_tools.deltalake.maintenance --optimize --table observations

    # CSV to Parquet
    python -m wps_tools.deltalake.csv_to_parquet input.csv --date-column timestamp --output-dir ./data

    # Test client
    python -m wps_tools.deltalake.test_client --endpoint http://localhost:8080/api/delta-sharing
"""

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

from wps_tools.deltalake.crawler import (
    crawl_all,
    crawl_year,
    enrich_stations,
    compute_climatology_stats,
    build_observations_by_station,
)

from wps_tools.deltalake.maintenance import (
    create_checkpoint,
    optimize_table,
    vacuum_table,
    maintain_table,
    maintain_all_tables,
)

from wps_tools.deltalake.csv_to_parquet import (
    csv_to_parquet,
    upload_parquet_to_s3,
    convert_and_upload,
)

__all__ = [
    # Config
    "OBSERVATIONS_TABLE",
    "STATIONS_TABLE",
    "CLIMATOLOGY_STATS_TABLE",
    "OBSERVATIONS_BY_STATION_TABLE",
    "DATE_COLUMN",
    "STATION_CODE_COLUMN",
    "get_storage_options",
    "get_table_uri",
    # Crawler
    "crawl_all",
    "crawl_year",
    "enrich_stations",
    "compute_climatology_stats",
    "build_observations_by_station",
    # Maintenance
    "create_checkpoint",
    "optimize_table",
    "vacuum_table",
    "maintain_table",
    "maintain_all_tables",
    # CSV to Parquet
    "csv_to_parquet",
    "upload_parquet_to_s3",
    "convert_and_upload",
]
