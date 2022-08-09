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
tileserver_postgres_password = config.get('TILESERVER_POSTGRES_PASSWORD', 'tileserv')
tileserver_postgres_read_host = config.get('TILESERVER_POSTGRES_READ_HOST', 'localhost')
tileserver_postgres_write_host = config.get('TILESERVER_POSTGRES_WRITE_HOST', 'localhost')
tileserver_postgres_database = config.get('TILESERVER_POSTGRES_DATABASE', 'tileserv')
postgres_port = config.get('POSTGRES_PORT', '5432')

TILESERVER_READ_STRING = f'postgresql+asyncpg://{tileserver_read_user}:{tileserver_postgres_password}@{tileserver_postgres_read_host}:{postgres_port}/{tileserver_postgres_database}'
TILESERVER_WRITE_STRING = f'postgresql+asyncpg://{tileserver_write_user}:{tileserver_postgres_password}@{tileserver_postgres_write_host}:{postgres_port}/{tileserver_postgres_database}'

tile_server_read_engine = create_async_engine(TILESERVER_READ_STRING)
# TODO: what about these other params?
# pool_size=int(config.get('POSTGRES_POOL_SIZE', 5)),
# max_overflow=int(config.get('POSTGRES_MAX_OVERFLOW', 10)),
# pool_pre_ping=True, connect_args={
# 'options': '-c timezone=utc'})

# connect to database - defaulting to always use utc timezone
tile_server_write_engine = create_async_engine(TILESERVER_WRITE_STRING)
# TODO: how do you tell asyncpg to use utc? e.g. connect_args={'options': '-c timezone=utc'})

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
        await session.commit()
    except Exception:
        await session.rollback()
        raise
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
