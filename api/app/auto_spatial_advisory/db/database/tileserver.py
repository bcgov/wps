""" The fire zone, fire centre and hfi polygons live in a different database - it's our "tileserver"
database.
"""
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app import config

tileserver_read_user = config.get('TILESERVER_READ_USER', 'tileserv')
tileserver_write_user = config.get('TILESERVER_WRITE_USER', 'tileserv')
tileserver_postgres_read_password = config.get('TILESERVER_POSTGRES_READ_PASSWORD', 'tileserv')
tileserver_postgres_write_password = config.get('TILESERVER_POSTGRES_WRITE_PASSWORD', 'tileserv')
tileserver_postgres_read_host = config.get('TILESERVER_POSTGRES_READ_HOST', 'localhost')
tileserver_postgres_write_host = config.get('TILESERVER_POSTGRES_WRITE_HOST', 'localhost')
tileserver_postgres_database = config.get('TILESERVER_POSTGRES_DATABASE', 'tileserv')
postgres_port = config.get('POSTGRES_PORT', '5432')

TILESERVER_READ_STRING = f'postgresql+asyncpg://{tileserver_read_user}:{tileserver_postgres_read_password}@{tileserver_postgres_read_host}:{postgres_port}/{tileserver_postgres_database}'
TILESERVER_WRITE_STRING = f'postgresql+asyncpg://{tileserver_write_user}:{tileserver_postgres_write_password}@{tileserver_postgres_write_host}:{postgres_port}/{tileserver_postgres_database}'

# TODO: figure out connection pooling?
tile_server_read_engine = create_async_engine(TILESERVER_READ_STRING, connect_args={"timeout": 30})

tile_server_write_engine = create_async_engine(TILESERVER_WRITE_STRING)

tile_server_read_session_maker = sessionmaker(
    autocommit=False, autoflush=False, bind=tile_server_read_engine, class_=AsyncSession)

tile_server_write_session_maker = sessionmaker(
    autocommit=False, autoflush=False, bind=tile_server_write_engine, class_=AsyncSession)


def _get_tileserver_read_session() -> AsyncSession:
    """ abstraction used for mocking out a read session """
    return tile_server_read_session_maker()


def _get_tileserver_write_session() -> AsyncSession:
    """ abstraction used for mocking out a write session """
    return tile_server_write_session_maker()


@asynccontextmanager
async def get_tileserver_read_session_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional scope around a series of operations.
    """
    session = _get_tileserver_read_session()
    try:
        yield session
    finally:
        await session.close()


@asynccontextmanager
async def get_tileserver_write_session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope around a series of operations."""
    session = _get_tileserver_write_session()
    try:
        yield session
        await session.commit()
    except:
        await session.rollback()
        raise
    finally:
        await session.close()
