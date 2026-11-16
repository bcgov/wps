"""Where the station weather tables live in object storage, and how Delta Lake reaches them."""

from wps_shared import config


def object_store_options() -> dict[str, str]:
    """Delta Lake storage options for our object store.

    `conditional_put` is what makes several writers per table safe: the store rejects a commit
    whose log entry already exists. Checked with backend/scripts/object_store_delta_check.py.
    """
    return {
        "AWS_ENDPOINT_URL": f"https://{config.get('OBJECT_STORE_SERVER')}",
        "AWS_ACCESS_KEY_ID": config.get("OBJECT_STORE_USER_ID"),
        "AWS_SECRET_ACCESS_KEY": config.get("OBJECT_STORE_SECRET"),
        "AWS_REGION": "us-east-1",
        "conditional_put": "etag",
    }


def resolve_table(
    key: str, table_uri: str | None, storage_options: dict[str, str] | None
) -> tuple[str, dict[str, str] | None]:
    """Return the table's location and storage options, defaulting to `key` in our object store."""
    if table_uri is not None:
        return table_uri, storage_options
    return f"s3://{config.get('OBJECT_STORE_BUCKET')}/{key}", object_store_options()
