"""Shared configuration for Delta Lake tools."""

from wps_shared import config

# Delta table paths
OBSERVATIONS_TABLE = "historical/observations"
STATIONS_TABLE = "historical/stations"
CLIMATOLOGY_STATS_TABLE = "historical/climatology_stats"
OBSERVATIONS_BY_STATION_TABLE = "historical/observations_by_station"

# Column names
DATE_COLUMN = "DATE_TIME"
STATION_CODE_COLUMN = "STATION_CODE"


def get_storage_options() -> dict[str, str]:
    """Get S3 storage options for delta-rs."""
    return {
        "AWS_ENDPOINT_URL": f"https://{config.get('OBJECT_STORE_SERVER')}",
        "AWS_ACCESS_KEY_ID": config.get("OBJECT_STORE_USER_ID"),
        "AWS_SECRET_ACCESS_KEY": config.get("OBJECT_STORE_SECRET"),
        "AWS_REGION": "us-east-1",  # Required but ignored for non-AWS S3
        "AWS_S3_ALLOW_UNSAFE_RENAME": "true",  # Required for S3-compatible storage
    }


def get_table_uri(table_name: str) -> str:
    """Get the S3 URI for a Delta table."""
    bucket = config.get("OBJECT_STORE_BUCKET")
    return f"s3://{bucket}/{table_name}"
