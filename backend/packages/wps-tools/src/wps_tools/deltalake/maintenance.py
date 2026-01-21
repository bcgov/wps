"""Delta Lake table maintenance utilities.

Provides functions for maintaining Delta Lake tables:
- Checkpointing (speed up log reads)
- Optimization (compact small files)
- Vacuum (remove old files)

Usage:
    python -m wps_tools.deltalake.maintenance --help
    python -m wps_tools.deltalake.maintenance --checkpoint
    python -m wps_tools.deltalake.maintenance --optimize
    python -m wps_tools.deltalake.maintenance --vacuum
    python -m wps_tools.deltalake.maintenance --all
"""

import argparse
import logging

from deltalake import DeltaTable

from wps_tools.deltalake.config import (
    OBSERVATIONS_TABLE,
    STATIONS_TABLE,
    CLIMATOLOGY_STATS_TABLE,
    OBSERVATIONS_BY_STATION_TABLE,
    get_storage_options,
    get_table_uri,
)

logger = logging.getLogger(__name__)

# All tables that can be maintained
ALL_TABLES = [
    OBSERVATIONS_TABLE,
    STATIONS_TABLE,
    CLIMATOLOGY_STATS_TABLE,
    OBSERVATIONS_BY_STATION_TABLE,
]


def create_checkpoint(table_name: str = OBSERVATIONS_TABLE):
    """Create a checkpoint for the Delta table to speed up log reads."""
    storage_options = get_storage_options()
    table_uri = get_table_uri(table_name)

    logger.info(f"Creating checkpoint for {table_uri}...")
    dt = DeltaTable(table_uri, storage_options=storage_options)
    dt.create_checkpoint()
    logger.info("Checkpoint created")


def optimize_table(table_name: str = OBSERVATIONS_TABLE):
    """Compact small files in the Delta table."""
    storage_options = get_storage_options()
    table_uri = get_table_uri(table_name)

    logger.info(f"Optimizing {table_uri}...")
    dt = DeltaTable(table_uri, storage_options=storage_options)
    dt.optimize.compact()
    logger.info("Optimization complete")


def vacuum_table(table_name: str = OBSERVATIONS_TABLE, retention_hours: int = 168):
    """Remove old files from the Delta table."""
    storage_options = get_storage_options()
    table_uri = get_table_uri(table_name)

    logger.info(f"Vacuuming {table_uri} (retention: {retention_hours} hours)...")
    dt = DeltaTable(table_uri, storage_options=storage_options)
    dt.vacuum(retention_hours=retention_hours, enforce_retention_duration=False)
    logger.info("Vacuum complete")


def maintain_table(table_name: str, retention_hours: int = 168):
    """Run all maintenance operations on a single table."""
    logger.info(f"\n{'='*50}\nMaintaining {table_name}\n{'='*50}")
    try:
        create_checkpoint(table_name)
        optimize_table(table_name)
        vacuum_table(table_name, retention_hours)
    except Exception as e:
        logger.error(f"Error maintaining {table_name}: {e}")
        raise


def maintain_all_tables(retention_hours: int = 168):
    """Run maintenance (checkpoint, optimize, vacuum) on all Delta tables."""
    for table in ALL_TABLES:
        try:
            maintain_table(table, retention_hours)
        except Exception as e:
            logger.error(f"Error maintaining {table}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Maintain Delta Lake tables (checkpoint, optimize, vacuum)"
    )
    parser.add_argument(
        "--table",
        type=str,
        choices=["observations", "stations", "climatology_stats", "observations_by_station"],
        help="Specific table to maintain (default: all tables)",
    )
    parser.add_argument(
        "--checkpoint",
        action="store_true",
        help="Create checkpoint to speed up Delta log reads",
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Compact small files",
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="Remove old files",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all maintenance operations (checkpoint, optimize, vacuum)",
    )
    parser.add_argument(
        "--retention-hours",
        type=int,
        default=168,
        help="Retention period for vacuum in hours (default: 168 = 7 days)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if not any([args.checkpoint, args.optimize, args.vacuum, args.all]):
        parser.error("At least one of --checkpoint, --optimize, --vacuum, or --all must be specified")

    # Map table name to constant
    table_map = {
        "observations": OBSERVATIONS_TABLE,
        "stations": STATIONS_TABLE,
        "climatology_stats": CLIMATOLOGY_STATS_TABLE,
        "observations_by_station": OBSERVATIONS_BY_STATION_TABLE,
    }

    tables = [table_map[args.table]] if args.table else ALL_TABLES

    for table in tables:
        if args.all:
            maintain_table(table, args.retention_hours)
        else:
            if args.checkpoint:
                create_checkpoint(table)
            if args.optimize:
                optimize_table(table)
            if args.vacuum:
                vacuum_table(table, args.retention_hours)


if __name__ == "__main__":
    main()
