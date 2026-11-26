"""What the Station Weather API's routes share: rows of an Arrow table as JSON or CSV."""

import io

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv
from fastapi import Request, Response

CSV = "text/csv"

CSV_RESPONSE = {200: {"content": {CSV: {}}}}


def rounded(rows: pa.Table) -> pa.Table:
    """Values are stored as float32, which as float64 reads 21.299999237 for 21.3."""
    for index, field in enumerate(rows.schema):
        if field.type == pa.float32():
            rows = rows.set_column(
                index, field.name, pc.round(rows[field.name].cast(pa.float64()), 3)
            )
    return rows


def wants_csv(request: Request) -> bool:
    return CSV in request.headers.get("accept", "")


def csv_response(rows: pa.Table, headers: dict[str, str]) -> Response:
    """The rows as CSV, with times as ISO 8601 UTC like the JSON."""
    for index, field in enumerate(rows.schema):
        if pa.types.is_timestamp(field.type):
            # Arrow's %S has the fraction of a second too, unless the time is in seconds.
            seconds = rows[field.name].cast(pa.timestamp("s", tz="UTC"), safe=False)
            rows = rows.set_column(
                index, field.name, pc.strftime(seconds, format="%Y-%m-%dT%H:%M:%SZ")
            )
    buffer = io.BytesIO()
    pyarrow.csv.write_csv(rows, buffer)
    return Response(content=buffer.getvalue(), media_type=CSV, headers=headers)
