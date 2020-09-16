""" Configurations for Alembic migrations
"""
from logging.config import fileConfig
import sqlalchemy
from alembic import context
import app

# pylint: disable=invalid-name

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
# sqlalchemy.url uses variables from .env file
config = context.config
config.set_main_option('sqlalchemy.url', app.db.database.DB_WRITE_STRING)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = app.db.models.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def exclude_tables_from_config(config_):
    """ There are tables (e.g. spatial_ref_sys created by postgis), that must be ignored. """
    tables_ = config_.get("tables", None)
    if tables_ is not None:
        tables = tables_.split(",")
    return tables


# load tables to be excluded
exclude_tables = exclude_tables_from_config(
    config.get_section('alembic:exclude'))


def include_object(object, name, type_, reflected, compare_to):
    """ any tables not in the ignore list, are to be included """
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
        include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = sqlalchemy.engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=sqlalchemy.pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata,
            include_object=include_object
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
