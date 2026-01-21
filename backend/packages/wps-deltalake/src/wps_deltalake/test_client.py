"""Test Delta Sharing Client

Tests the delta-sharing protocol implementation against a running API.

Usage:
    python -m wps_tools.test_delta_sharing --endpoint http://localhost:8080/api/delta-sharing
    python -m wps_tools.test_delta_sharing --endpoint https://api.example.com/api/delta-sharing --token <jwt>
"""

import argparse
import json
import logging
import os
import tempfile

logger = logging.getLogger(__name__)


def patch_fsspec_for_presigned_urls():
    """Patch fsspec to handle presigned URLs with encoded paths.

    The delta-sharing client uses fsspec's HTTPFileSystem to fetch parquet files.
    By default, fsspec re-encodes URLs which breaks presigned URLs that already
    contain percent-encoded characters (like partition paths with `=` -> `%3D`).

    This patch makes fsspec treat URLs as already encoded.
    """
    import fsspec

    _original_filesystem = fsspec.filesystem

    def patched_filesystem(protocol, **kwargs):
        if protocol in ("http", "https") and "encoded" not in kwargs:
            kwargs["encoded"] = True
        return _original_filesystem(protocol, **kwargs)

    fsspec.filesystem = patched_filesystem
    logger.info("Patched fsspec.filesystem to use encoded=True for HTTP(S)")


def test_delta_sharing(endpoint: str, token: str | None = None):
    """Test with the official delta-sharing Python client."""
    try:
        import delta_sharing
    except ImportError:
        print("delta-sharing package not installed. Install with: pip install delta-sharing")
        return

    # Patch fsspec to handle presigned URLs with encoded partition paths
    patch_fsspec_for_presigned_urls()

    print("=== Testing Delta Sharing Protocol ===\n")

    # Create a profile file
    profile = {
        "shareCredentialsVersion": 1,
        "endpoint": endpoint,
        "bearerToken": token or "unused",
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".share", delete=False) as f:
        json.dump(profile, f)
        profile_path = f.name

    try:
        # Create client
        client = delta_sharing.SharingClient(profile_path)

        # List all tables
        print("1. list_all_tables()")
        tables = client.list_all_tables()
        for t in tables:
            print(f"   - {t.share}.{t.schema}.{t.name}")
        print()

        # Load stations as pandas (smaller table)
        print("2. load_as_pandas(stations)")
        table_url = f"{profile_path}#historical.default.stations"
        df = delta_sharing.load_as_pandas(table_url)
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        print("   Sample:")
        print(df.head(3).to_string())
        print()

        # Load observations with limit
        print("3. load_as_pandas(observations) - first 1000 rows")
        table_url = f"{profile_path}#historical.default.observations"
        df = delta_sharing.load_as_pandas(table_url, limit=1000)
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {list(df.columns)[:8]}...")
        print("   Sample:")
        print(df.head(3).to_string(max_cols=8))
        print()

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        os.unlink(profile_path)


def main():
    parser = argparse.ArgumentParser(description="Test Delta Sharing protocol implementation")
    parser.add_argument(
        "--endpoint",
        default="http://localhost:8080/api/delta-sharing",
        help="Delta Sharing endpoint URL",
    )
    parser.add_argument(
        "--token",
        help="Bearer token for authentication (optional if auth is disabled)",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    test_delta_sharing(args.endpoint, args.token)


if __name__ == "__main__":
    main()
