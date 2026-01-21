"""Delta Lake wrapper for performant queries with PyArrow."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pandas as pd
import pyarrow as pa
from deltalake import DeltaTable

if TYPE_CHECKING:
    import pyarrow.compute as pc
    import pyarrow.dataset


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
