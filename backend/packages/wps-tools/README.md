# wps-tools

Utility tools for Wildfire Predictive Services Unit.

Contains utilities for managing raster data, S3 operations, and other administrative tasks.

Assumes installation and setup is done in [backend/README.md](../../README.md)

## Historical Data Tools

Tools for converting CSV data to Delta Lake tables on object storage for efficient querying.

### Architecture

```
CSV Files → Delta Lake Tables → API (DuckDB query) → Users
                  ↑
         (partitioned by year/month)
         s3://bucket/historical/observations/
```

Data is stored in [Delta Lake](https://delta.io/) format, which provides:
- **Append without rewrite** - Daily updates add new files, no need to rewrite existing data
- **ACID transactions** - Safe concurrent writes
- **Time travel** - Query data as of any past point
- **Efficient queries** - Parquet columnar storage with partition pruning

### bcws_data_mart_crawler

Crawls the [BC Wildfire Service Data Mart](https://www.for.gov.bc.ca/ftp/HPR/external/!publish/BCWS_DATA_MART/) and appends to Delta Lake tables.

```bash
# Dry run - see what would be written
python -m wps_tools.bcws_data_mart_crawler --years 2024 --dry-run

# Process specific years
python -m wps_tools.bcws_data_mart_crawler --years 2023 2024

# Process all available years (1987-2026)
python -m wps_tools.bcws_data_mart_crawler --all

# Optimize (compact small files) after crawling
python -m wps_tools.bcws_data_mart_crawler --years 2024 --optimize

# Vacuum (remove old files) after crawling
python -m wps_tools.bcws_data_mart_crawler --vacuum
```

**Options:**
- `--years YEAR [YEAR ...]`: Specific years to process
- `--all`: Process all available years
- `--dry-run`: Don't write, just show what would happen
- `--no-skip-existing`: Re-process dates already in the table
- `--optimize`: Compact small files after crawling
- `--vacuum`: Remove old files after crawling
- `--verbose`: Enable debug logging

**Delta Tables Created:**

| Table | Contents | Partitioning |
|-------|----------|--------------|
| `historical/observations` | Weather observations | `year`, `month` |
| `historical/stations` | Station metadata | None |

**Table Structure (observations):**
```
s3://bucket/historical/observations/
  _delta_log/
    00000000000000000000.json
    00000000000000000001.json
    ...
  year=2024/
    month=1/
      part-00001.parquet
      part-00002.parquet
    month=2/
      ...
```

### Querying Delta Tables

**With DuckDB (recommended):**
```python
import duckdb

conn = duckdb.connect()

# Query observations
df = conn.execute("""
    SELECT * FROM delta_scan('s3://bucket/historical/observations')
    WHERE year = 2024 AND month = 6
    LIMIT 100
""").fetchdf()

# Query with date filter
df = conn.execute("""
    SELECT STATION_CODE, DATE_TIME, HOURLY_TEMPERATURE, FIRE_WEATHER_INDEX
    FROM delta_scan('s3://bucket/historical/observations')
    WHERE date = '2024-06-15'
""").fetchdf()
```

**With deltalake Python:**
```python
from deltalake import DeltaTable

dt = DeltaTable("s3://bucket/historical/observations", storage_options={...})

# Read as pandas
df = dt.to_pandas()

# Read specific version (time travel)
df = dt.load_as_version(5).to_pandas()
```

### Maintenance

**Optimize (compact small files):**
```bash
python -m wps_tools.bcws_data_mart_crawler --optimize
```

Run periodically (e.g., weekly) to merge small files created by daily appends into larger files for better query performance.

**Vacuum (remove old files):**
```bash
python -m wps_tools.bcws_data_mart_crawler --vacuum
```

Removes files no longer referenced by the current table version. Default retention is 7 days.

### csv_to_parquet

Generic tool for converting any CSV file with a date column to partitioned Parquet files.

```bash
# Convert locally
python -m wps_tools.csv_to_parquet data.csv \
  --date-column timestamp \
  --output-dir ./output

# Convert and upload to S3
python -m wps_tools.csv_to_parquet data.csv \
  --date-column timestamp \
  --upload-to-s3 historical/my_dataset

# Partition by month instead of day
python -m wps_tools.csv_to_parquet data.csv \
  --date-column timestamp \
  --upload-to-s3 historical/my_dataset \
  --partition-by month
```

## Environment Variables

These tools use the standard object store configuration:

- `OBJECT_STORE_SERVER`: S3-compatible endpoint
- `OBJECT_STORE_USER_ID`: Access key ID
- `OBJECT_STORE_SECRET`: Secret access key
- `OBJECT_STORE_BUCKET`: Bucket name
