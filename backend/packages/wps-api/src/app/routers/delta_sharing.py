"""Delta Sharing Protocol Router

Implements the Delta Sharing protocol for external access to Delta Lake tables.
https://github.com/delta-io/delta-sharing/blob/main/PROTOCOL.md

Compatible with the delta-sharing Python client:
    import delta_sharing
    client = delta_sharing.SharingClient("profile.share")
    df = delta_sharing.load_as_pandas("profile.share#historical.default.observations")
"""

import json
import logging
from typing import Annotated

from deltalake import DeltaTable
from fastapi import APIRouter, HTTPException, Path, Response
from pydantic import BaseModel, Field
from wps_shared import config
from wps_shared.utils.s3_client import S3Client

# File URL expiration in seconds (1 hour)
FILE_URL_EXPIRATION = 3600

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/delta-sharing",
)

# Configuration: single share with default schema
SHARE_NAME = "historical"
SCHEMA_NAME = "default"

# Available Delta tables
TABLES = {
    "observations": "historical/observations",
    "stations": "historical/stations",
    "observations_by_station": "historical/observations_by_station",
}


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


def ndjson_response(lines: list[dict], headers: dict[str, str] | None = None) -> Response:
    """Create a newline-delimited JSON response."""
    content = "\n".join(json.dumps(line) for line in lines)
    return Response(
        content=content,
        media_type="application/x-ndjson",
        headers=headers,
    )


def normalize_schema_string(schema_json: str) -> str:
    """Normalize schema types for delta-sharing client compatibility.

    The delta-sharing client doesn't recognize some newer Delta Lake types like
    'timestamp_ntz'. This function maps them to compatible types.
    """
    # Replace timestamp_ntz with timestamp (both are stored the same in parquet)
    return schema_json.replace('"timestamp_ntz"', '"timestamp"')


# --- List Shares ---
class Share(BaseModel):
    name: str
    id: str


class ListSharesResponse(BaseModel):
    items: list[Share]
    nextPageToken: str | None = None


@router.get("/shares", response_model=ListSharesResponse)
async def list_shares():
    """List all available shares."""
    return ListSharesResponse(items=[Share(name=SHARE_NAME, id=SHARE_NAME)])


@router.get("/shares/{share}")
async def get_share(share: Annotated[str, Path(description="Share name")]):
    """Get a share by name."""
    if share != SHARE_NAME:
        raise HTTPException(status_code=404, detail=f"Share '{share}' not found")
    return {"share": {"name": SHARE_NAME, "id": SHARE_NAME}}


# --- List Schemas ---
class Schema(BaseModel):
    name: str
    share: str


class ListSchemasResponse(BaseModel):
    items: list[Schema]
    nextPageToken: str | None = None


@router.get("/shares/{share}/schemas", response_model=ListSchemasResponse)
async def list_schemas(share: Annotated[str, Path(description="Share name")]):
    """List all schemas in a share."""
    if share != SHARE_NAME:
        raise HTTPException(status_code=404, detail=f"Share '{share}' not found")
    return ListSchemasResponse(items=[Schema(name=SCHEMA_NAME, share=SHARE_NAME)])


# --- List Tables ---
class Table(BaseModel):
    model_config = {"populate_by_name": True}

    name: str
    schema_: str = Field(serialization_alias="schema")
    share: str
    shareId: str
    id: str

    def model_dump(self, **kwargs):
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


class ListTablesResponse(BaseModel):
    items: list[Table]
    nextPageToken: str | None = None


@router.get("/shares/{share}/schemas/{schema}/tables", response_model=ListTablesResponse)
async def list_tables(
    share: Annotated[str, Path(description="Share name")],
    schema: Annotated[str, Path(description="Schema name")],
):
    """List all tables in a schema."""
    if share != SHARE_NAME:
        raise HTTPException(status_code=404, detail=f"Share '{share}' not found")
    if schema != SCHEMA_NAME:
        raise HTTPException(status_code=404, detail=f"Schema '{schema}' not found")

    items = [
        Table(
            name=table_name,
            schema_=SCHEMA_NAME,
            share=SHARE_NAME,
            shareId=SHARE_NAME,
            id=table_name,
        )
        for table_name in TABLES.keys()
    ]
    return ListTablesResponse(items=items)


@router.get("/shares/{share}/all-tables", response_model=ListTablesResponse)
async def list_all_tables(
    share: Annotated[str, Path(description="Share name")],
):
    """List all tables in a share (across all schemas)."""
    if share != SHARE_NAME:
        raise HTTPException(status_code=404, detail=f"Share '{share}' not found")

    items = [
        Table(
            name=table_name,
            schema_=SCHEMA_NAME,
            share=SHARE_NAME,
            shareId=SHARE_NAME,
            id=table_name,
        )
        for table_name in TABLES.keys()
    ]
    return ListTablesResponse(items=items)


# --- Table Metadata ---
@router.get("/shares/{share}/schemas/{schema}/tables/{table}/version")
async def get_table_version(
    share: Annotated[str, Path(description="Share name")],
    schema: Annotated[str, Path(description="Schema name")],
    table: Annotated[str, Path(description="Table name")],
):
    """Get the current version of a table."""
    if share != SHARE_NAME:
        raise HTTPException(status_code=404, detail=f"Share '{share}' not found")
    if schema != SCHEMA_NAME:
        raise HTTPException(status_code=404, detail=f"Schema '{schema}' not found")
    if table not in TABLES:
        raise HTTPException(status_code=404, detail=f"Table '{table}' not found")

    table_key = TABLES[table]
    storage_options = get_storage_options()
    table_uri = get_table_uri(table_key)

    try:
        dt = DeltaTable(table_uri, storage_options=storage_options)
        return Response(headers={"Delta-Table-Version": str(dt.version())})
    except Exception as e:
        logger.error(f"Error reading table version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shares/{share}/schemas/{schema}/tables/{table}/metadata")
async def get_table_metadata(
    share: Annotated[str, Path(description="Share name")],
    schema: Annotated[str, Path(description="Schema name")],
    table: Annotated[str, Path(description="Table name")],
):
    """Get table metadata (protocol and schema)."""
    if share != SHARE_NAME:
        raise HTTPException(status_code=404, detail=f"Share '{share}' not found")
    if schema != SCHEMA_NAME:
        raise HTTPException(status_code=404, detail=f"Schema '{schema}' not found")
    if table not in TABLES:
        raise HTTPException(status_code=404, detail=f"Table '{table}' not found")

    table_key = TABLES[table]
    storage_options = get_storage_options()
    table_uri = get_table_uri(table_key)

    try:
        dt = DeltaTable(table_uri, storage_options=storage_options)
        dt_schema = dt.schema()
        metadata = dt.metadata()
        version = dt.version()

        # Get last modified timestamp from history
        last_modified = None
        try:
            history = dt.history(limit=1)
            if history:
                last_modified = history[0].get("timestamp")
        except Exception as hist_err:
            logger.warning(f"Could not get table history: {hist_err}")

        meta_dict = {
            "id": metadata.id,
            "format": {"provider": "parquet"},
            "schemaString": normalize_schema_string(dt_schema.to_json()),
            "partitionColumns": metadata.partition_columns,
            "configuration": metadata.configuration,
        }
        if last_modified:
            meta_dict["lastModified"] = last_modified

        lines = [
            {"protocol": {"minReaderVersion": 1}},
            {"metaData": meta_dict},
        ]

        return ndjson_response(lines, headers={"Delta-Table-Version": str(version)})

    except Exception as e:
        logger.error(f"Error reading table metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Query Table ---
class PredicateHint(BaseModel):
    op: str
    children: list["PredicateHint | dict"] | None = None
    name: str | None = None
    value: str | None = None
    valueType: str | None = None


class QueryRequest(BaseModel):
    predicateHints: list[str] | None = None
    jsonPredicateHints: PredicateHint | None = None
    limitHint: int | None = None
    version: int | None = None


@router.post("/shares/{share}/schemas/{schema}/tables/{table}/query")
async def query_table(
    share: Annotated[str, Path(description="Share name")],
    schema: Annotated[str, Path(description="Schema name")],
    table: Annotated[str, Path(description="Table name")],
    request: QueryRequest | None = None,
):
    """
    Query a table and get pre-signed URLs to parquet files.

    Returns newline-delimited JSON with protocol, metadata, and file entries.
    Pre-signed URLs are valid for 1 hour.
    """
    if share != SHARE_NAME:
        raise HTTPException(status_code=404, detail=f"Share '{share}' not found")
    if schema != SCHEMA_NAME:
        raise HTTPException(status_code=404, detail=f"Schema '{schema}' not found")
    if table not in TABLES:
        raise HTTPException(status_code=404, detail=f"Table '{table}' not found")

    table_key = TABLES[table]
    storage_options = get_storage_options()
    table_uri = get_table_uri(table_key)

    try:
        dt = DeltaTable(table_uri, storage_options=storage_options)
        dt_schema = dt.schema()
        metadata = dt.metadata()
        version = dt.version()

        # Start response with protocol and metadata
        lines: list[dict] = [
            {"protocol": {"minReaderVersion": 1}},
            {
                "metaData": {
                    "id": metadata.id,
                    "format": {"provider": "parquet"},
                    "schemaString": normalize_schema_string(dt_schema.to_json()),
                    "partitionColumns": metadata.partition_columns,
                    "configuration": metadata.configuration,
                }
            },
        ]

        # Get file actions
        add_actions = dt.get_add_actions(flatten=True).to_pydict()
        num_files = len(add_actions.get("path", []))

        # Apply limit hint if provided
        limit = num_files
        if request and request.limitHint:
            limit = min(request.limitHint, num_files)

        # Generate presigned URLs for direct S3 access
        async with S3Client() as s3_client:
            for i in range(limit):
                file_path = add_actions["path"][i]
                size = add_actions.get("size_bytes", [0] * num_files)[i]
                stats = add_actions.get("stats", [None] * num_files)[i]

                # Parse partition values
                partition_values = {}
                for part in file_path.split("/"):
                    if "=" in part:
                        key, value = part.split("=", 1)
                        partition_values[key] = value

                s3_key = f"{table_key}/{file_path}"
                url = await s3_client.generate_presigned_url(s3_key, FILE_URL_EXPIRATION)

                file_entry = {
                    "file": {
                        "url": url,
                        "id": file_path,
                        "partitionValues": partition_values,
                        "size": size,
                    }
                }
                if stats:
                    file_entry["file"]["stats"] = stats
                lines.append(file_entry)

        return ndjson_response(lines, headers={"Delta-Table-Version": str(version)})

    except Exception as e:
        logger.error(f"Error querying table: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
