"""Delta Lake wrapper for performant queries with PyArrow."""

from __future__ import annotations

import asyncio

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset
from deltalake import DeltaTable

from wps_shared import config


def get_storage_options() -> dict[str, str]:
    """Get S3 storage options for delta-rs."""
    return {
        "AWS_ENDPOINT_URL": f"https://{config.get('OBJECT_STORE_SERVER')}",
        "AWS_ACCESS_KEY_ID": config.get("OBJECT_STORE_USER_ID"),
        "AWS_SECRET_ACCESS_KEY": config.get("OBJECT_STORE_SECRET"),
        "AWS_REGION": "us-east-1",
        "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
    }


def get_table_uri(table_key: str) -> str:
    """Get the S3 URI for a Delta table."""
    bucket = config.get("OBJECT_STORE_BUCKET")
    return f"s3://{bucket}/{table_key}"


# Lazy-initialized table registry
_table_registry: dict[str, DeltaTableWrapper] = {}


def get_table(table_key: str) -> "DeltaTableWrapper":
    """
    Get a lazily-initialized DeltaTableWrapper for the given table key.

    Args:
        table_key: The table path relative to the bucket (e.g., "historical/observations")

    Returns:
        A cached DeltaTableWrapper instance.
    """
    if table_key not in _table_registry:
        _table_registry[table_key] = DeltaTableWrapper(
            table_uri=get_table_uri(table_key),
            storage_options=get_storage_options(),
        )
    return _table_registry[table_key]


class DeltaTableWrapper:
    """
    Wrapper around Delta Lake for performant PyArrow queries.

    Usage:
        import pyarrow.compute as pc

        table = DeltaTableWrapper(
            table_uri="s3://bucket/table",
            storage_options={...},
        )

        # Query with predicate pushdown
        df = table.query(
            columns=["col1", "col2"],
            filter=(pc.field("station") == 123) & (pc.field("year") >= 2020),
        )

        # Async query
        df = await table.query_async(filter=pc.field("station") == 123)
    """

    def __init__(
        self,
        table_uri: str,
        storage_options: dict[str, str] | None = None,
    ):
        self._table_uri = table_uri
        self._storage_options = storage_options or {}
        self._dt = DeltaTable(table_uri, storage_options=self._storage_options)
        self._dataset = self._dt.to_pyarrow_dataset()

    @property
    def dataset(self) -> pyarrow.dataset.Dataset:
        """Get the PyArrow dataset for direct access."""
        return self._dataset

    @property
    def delta_table(self) -> DeltaTable:
        """Get the underlying DeltaTable."""
        return self._dt

    @property
    def schema(self) -> pa.Schema:
        """Get the table schema."""
        return self._dataset.schema

    @property
    def version(self) -> int:
        """Get the current table version."""
        return self._dt.version()

    def reload(self) -> None:
        """Reload the table to pick up new data."""
        self._dt = DeltaTable(self._table_uri, storage_options=self._storage_options)
        self._dataset = self._dt.to_pyarrow_dataset()

    def query(
        self,
        columns: list[str] | None = None,
        filter: pc.Expression | None = None,
    ) -> pd.DataFrame:
        """
        Query with predicate pushdown, return pandas DataFrame.

        Args:
            columns: Columns to select (None for all).
            filter: PyArrow filter expression for predicate pushdown.
                    Example: pc.field("station") == 123

        Returns:
            pandas DataFrame with results.
        """
        return self._dataset.to_table(columns=columns, filter=filter).to_pandas()

    def query_arrow(
        self,
        columns: list[str] | None = None,
        filter: pc.Expression | None = None,
    ) -> pa.Table:
        """Query with predicate pushdown, return PyArrow Table."""
        return self._dataset.to_table(columns=columns, filter=filter)

    async def query_async(
        self,
        columns: list[str] | None = None,
        filter: pc.Expression | None = None,
    ) -> pd.DataFrame:
        """Async version of query()."""
        return await asyncio.to_thread(self.query, columns, filter)

    async def query_arrow_async(
        self,
        columns: list[str] | None = None,
        filter: pc.Expression | None = None,
    ) -> pa.Table:
        """Async version of query_arrow()."""
        return await asyncio.to_thread(self.query_arrow, columns, filter)

    def scanner(
        self,
        columns: list[str] | None = None,
        filter: pc.Expression | None = None,
        batch_size: int = 131072,
    ) -> pyarrow.dataset.Scanner:
        """
        Get a scanner for streaming large results.

        Args:
            columns: Columns to select.
            filter: PyArrow filter expression.
            batch_size: Number of rows per batch.

        Returns:
            PyArrow Scanner for iterating over batches.
        """
        return self._dataset.scanner(
            columns=columns,
            filter=filter,
            batch_size=batch_size,
        )

    def count(self, filter: pc.Expression | None = None) -> int:
        """Count rows matching the filter."""
        return self._dataset.count_rows(filter=filter)

    def head(self, n: int = 10, columns: list[str] | None = None) -> pd.DataFrame:
        """Get first n rows."""
        return self._dataset.head(n, columns=columns).to_pandas()

    @staticmethod
    async def load_observations(
        station_code: int,
        start_year: int,
        end_year: int,
        columns: list[str],
    ) -> pa.Table:
        """
        Load observations for a station and year range.

        Uses the observations_by_station table (partitioned by station_code) for
        efficient single-station queries. Falls back to observations table if
        the by-station table is unavailable.

        Args:
            station_code: Weather station code.
            start_year: Start year (inclusive).
            end_year: End year (inclusive).
            columns: Columns to select.

        Returns:
            PyArrow Table with observations.
        """
        # Try the station-partitioned table first (much faster for single-station queries)
        try:
            filter_expr = (
                (pc.field("station_code") == station_code)
                & (pc.field("year") >= start_year)
                & (pc.field("year") <= end_year)
            )
            return await get_table("historical/observations_by_station").query_arrow_async(
                columns=columns,
                filter=filter_expr,
            )
        except Exception:
            # Fall back to year/month partitioned table
            filter_expr = (
                (pc.field("STATION_CODE") == station_code)
                & (pc.field("year") >= start_year)
                & (pc.field("year") <= end_year)
            )
            return await get_table("historical/observations").query_arrow_async(
                columns=columns,
                filter=filter_expr,
            )

    @staticmethod
    async def load_climatology_stats(
        station_code: int,
        start_year: int,
        end_year: int,
    ) -> pa.Table | None:
        """
        Load pre-computed climatology stats for a station and reference period.

        Args:
            station_code: Weather station code.
            start_year: Reference period start year.
            end_year: Reference period end year.

        Returns:
            PyArrow Table with climatology stats, or None if not available.
        """
        try:
            filter_expr = (
                (pc.field("station_code") == station_code)
                & (pc.field("ref_start_year") == start_year)
                & (pc.field("ref_end_year") == end_year)
            )
            return await get_table("historical/climatology_stats").query_arrow_async(
                filter=filter_expr,
            )
        except Exception:
            return None

    @staticmethod
    async def load_station(
        station_code: int,
        columns: list[str] | None = None,
    ) -> pa.Table:
        """
        Load station metadata.

        Args:
            station_code: Weather station code.
            columns: Columns to select (None for all).

        Returns:
            PyArrow Table with station info.
        """
        filter_expr = pc.field("STATION_CODE") == station_code
        return await get_table("historical/stations").query_arrow_async(
            columns=columns,
            filter=filter_expr,
        )
