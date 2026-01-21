# wps-deltalake

Delta Lake tools for BC Wildfire Service weather data.

Provides utilities for:
- Crawling the BCWS Data Mart and loading into Delta Lake tables
- Converting CSV files to Parquet format
- Maintaining Delta Lake tables (checkpoint, optimize, vacuum)
- Testing Delta Sharing protocol implementations

## Installation

```bash
uv pip install -e packages/wps-deltalake
```

## Architecture

```
CSV Files → Delta Lake Tables → API (Delta Sharing) → Users
                  ↑
         (partitioned by year/month)
         s3://bucket/historical/observations/
```

Data is stored in [Delta Lake](https://delta.io/) format, which provides:
- **Append without rewrite** - Daily updates add new files, no need to rewrite existing data
- **ACID transactions** - Safe concurrent writes
- **Time travel** - Query data as of any past point
- **Efficient queries** - Parquet columnar storage with partition pruning

## BCWS Data Mart Crawler

Crawls the [BC Wildfire Service Data Mart](https://www.for.gov.bc.ca/ftp/HPR/external/!publish/BCWS_DATA_MART/) and appends to Delta Lake tables.

```bash
# Dry run - see what would be written
python -m wps_deltalake.crawler --years 2024 --dry-run

# Process specific years
python -m wps_deltalake.crawler --years 2023 2024

# Process all available years (1987-2026)
python -m wps_deltalake.crawler --all

# Enrich stations with additional attributes
python -m wps_deltalake.crawler \
  --enrich-stations /path/to/station_attributes.csv
```

**Options:**
- `--years YEAR [YEAR ...]`: Specific years to process
- `--all`: Process all available years
- `--dry-run`: Don't write, just show what would happen
- `--no-skip-existing`: Re-process dates already in the table
- `--enrich-stations CSV_PATH`: Merge station attributes from CSV into stations table
- `--verbose`: Enable debug logging

**Delta Tables Created:**

| Table | Contents | Partitioning |
|-------|----------|--------------|
| `historical/observations` | Weather observations | `year`, `month` |
| `historical/stations` | Station metadata | None |
| `historical/climatology_stats` | Pre-computed percentiles | None |
| `historical/observations_by_station` | Observations | `station_code` |

## Maintenance

Maintain Delta Lake tables with checkpoint, optimize, and vacuum operations.

```bash
# Run all maintenance on all tables
python -m wps_deltalake.maintenance --all

# Optimize a specific table
python -m wps_deltalake.maintenance --optimize --table observations

# Checkpoint and vacuum only
python -m wps_deltalake.maintenance --checkpoint --vacuum

# With custom retention (default 168 hours = 7 days)
python -m wps_deltalake.maintenance --vacuum --retention-hours 72
```

**Operations:**
- **Checkpoint**: Speed up Delta log reads by creating checkpoint files
- **Optimize**: Compact small files into larger ones for better query performance
- **Vacuum**: Remove old files no longer referenced by current table version

## CSV to Parquet

Generic tool for converting any CSV file with a date column to partitioned Parquet files.

```bash
# Convert locally
python -m wps_deltalake.csv_to_parquet data.csv \
  --date-column timestamp \
  --output-dir ./output

# Convert and upload to S3
python -m wps_deltalake.csv_to_parquet data.csv \
  --date-column timestamp \
  --upload-to-s3 historical/my_dataset

# Partition by month instead of day
python -m wps_deltalake.csv_to_parquet data.csv \
  --date-column timestamp \
  --upload-to-s3 historical/my_dataset \
  --partition-by month
```

## Python API

```python
from wps_deltalake import (
    # Crawler
    crawl_all,
    enrich_stations,
    compute_climatology_stats,
    build_observations_by_station,
    # Maintenance
    create_checkpoint,
    optimize_table,
    vacuum_table,
    maintain_all_tables,
    # Config
    OBSERVATIONS_TABLE,
    STATIONS_TABLE,
    get_storage_options,
    get_table_uri,
)

# Crawl specific years
results = crawl_all(years=[2023, 2024])

# Enrich stations with attributes
enrich_stations("/path/to/stations.csv")

# Maintain tables
maintain_all_tables()
```

## Environment Variables

- `OBJECT_STORE_SERVER`: S3-compatible endpoint
- `OBJECT_STORE_USER_ID`: Access key ID
- `OBJECT_STORE_SECRET`: Secret access key
- `OBJECT_STORE_BUCKET`: Bucket name
