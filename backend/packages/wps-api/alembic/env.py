"""Configurations for Alembic migrations"""

import asyncio
from logging.config import fileConfig

import sqlalchemy
from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config

from wps_shared.db.database import ASYNC_DB_WRITE_STRING
from wps_shared.db.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
# sqlalchemy.url uses variables from .env file
config = context.config
escaped_db_url = ASYNC_DB_WRITE_STRING.replace("%", "%%")
config.set_main_option("sqlalchemy.url", escaped_db_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def exclude_tables_from_config(config_):
    """There are tables (e.g. spatial_ref_sys created by postgis), that must be ignored."""
    tables_ = config_.get("tables", None)
    if tables_ is not None:
        tables = tables_.split(",")
    return tables


# load tables to be excluded
exclude_tables = exclude_tables_from_config(config.get_section("alembic:exclude"))


def include_object(object, name, type_, reflected, compare_to):
    """any tables not in the ignore list, are to be included"""
    if type_ == "table" and name in exclude_tables:
        return False
    else:
        return True


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Run migrations with automatic stamping for production databases."""
    import os
    from alembic.script import ScriptDirectory
    from alembic.migration import MigrationContext

    # Check if we should auto-stamp (production only)
    is_production = os.getenv("ENVIRONMENT", "").lower() in ("production", "prod")

    if is_production:
        # Get current database version
        migration_context = MigrationContext.configure(connection)
        current_rev = migration_context.get_current_revision()

        # d276ba9eed1f is the last migration before compression
        # If production database is at this revision, stamp to head instead of running migrations
        if current_rev == "d276ba9eed1f":
            script = ScriptDirectory.from_config(config)
            head_revision = script.get_current_head()

            # Ensure head is the expected compressed migration (seed data)
            assert head_revision == "cf8397b26783", (
                f"Expected head revision cf8397b26783 but got {head_revision}"
            )

            # Stamp the database to the seed application data migration, it should run the migrations after it
            connection.execute(
                sqlalchemy.text(f"UPDATE alembic_version SET version_num = '{head_revision}'")
            )
            connection.commit()
            print(f"✓ Production database stamped from {current_rev} to {head_revision}")

    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=sqlalchemy.pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online():
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
