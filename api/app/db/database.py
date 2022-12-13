""" Setup database to perform CRUD transactions
"""
import logging
from typing import Generator, AsyncGenerator
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from .. import config

logger = logging.getLogger(__name__)

write_user = config.get('POSTGRES_WRITE_USER', 'wps')
read_user = config.get('POSTGRES_READ_USER', 'wpsread')
postgres_password = config.get('POSTGRES_PASSWORD', 'wps')
postgres_write_host = config.get('POSTGRES_WRITE_HOST', 'localhost')
postgres_read_host = config.get('POSTGRES_READ_HOST', 'localhost')
postgres_port = config.get('POSTGRES_PORT', '5432')
postgres_database = config.get('POSTGRES_DATABASE', 'wps')

# pylint: disable=line-too-long
DB_WRITE_STRING = f'postgresql://{write_user}:{postgres_password}@{postgres_write_host}:{postgres_port}/{postgres_database}'

# pylint: disable=line-too-long
DB_READ_STRING = f'postgresql://{read_user}:{postgres_password}@{postgres_read_host}:{postgres_port}/{postgres_database}'

# pylint: disable=line-too-long
ASYNC_DB_READ_STRING = f'postgresql+asyncpg://{read_user}:{postgres_password}@{postgres_read_host}:{postgres_port}/{postgres_database}'

# pylint: disable=line-too-long
ASYNC_DB_WRITE_STRING = f'postgresql+asyncpg://{write_user}:{postgres_password}@{postgres_write_host}:{postgres_port}/{postgres_database}'

# connect to database - defaulting to always use utc timezone
_write_engine = create_engine(DB_WRITE_STRING, connect_args={
                              'options': '-c timezone=utc'})

tileserv_db_uri = config.get('TILESERV_POSTGRES_URI', DB_WRITE_STRING)

# connect to database - defaulting to always use utc timezone
_tileserv_db_write_engine = create_engine(tileserv_db_uri, connect_args={
    'options': '-c timezone=utc'})
# use pre-ping on read, as connections are quite often stale due to how few users we have at the moment.
_read_engine = create_engine(
    DB_READ_STRING,
    pool_size=int(config.get('POSTGRES_POOL_SIZE', 5)),
    max_overflow=int(config.get('POSTGRES_MAX_OVERFLOW', 10)),
    pool_pre_ping=True, connect_args={
        'options': '-c timezone=utc'})

# TODO: figure out connection pooling? pre-ping etc.?
_async_read_engine = create_async_engine(ASYNC_DB_READ_STRING)
_async_write_engine = create_async_engine(ASYNC_DB_WRITE_STRING)

# bind session to database
# avoid using these variables anywhere outside of context manager - if
# sessions are not closed, it will result in the api running out of
# connections and becoming non-responsive.
_write_session = sessionmaker(
    autocommit=False, autoflush=False, bind=_write_engine)
_read_session = sessionmaker(
    autocommit=False, autoflush=False, bind=_read_engine)
_tileserv_write_session = sessionmaker(
    autocommit=False, autoflush=False, bind=_tileserv_db_write_engine)
_async_read_sessionmaker = sessionmaker(
    autocommit=False, autoflush=False, bind=_async_read_engine, class_=AsyncSession)
_async_write_sessionmaker = sessionmaker(
    autocommit=False, autoflush=False, bind=_async_write_engine, class_=AsyncSession)

# constructing a base class for declarative class definitions
Base = declarative_base()


def _get_write_session() -> Session:
    """ abstraction used for mocking out a write session """
    return _write_session()


def _get_read_session() -> Session:
    """ abstraction used for mocking out a read session """
    return _read_session()


def _get_sync_write_tileserv_session() -> Session:
    """ abstraction used for mocking out a read session """
    return _tileserv_write_session()


def _get_async_read_session() -> AsyncSession:
    """ abstraction used for mocking out a read session """
    return _async_read_sessionmaker()


def _get_async_write_session() -> AsyncSession:
    """ abstraction used for mocking out a read session """
    return _async_write_sessionmaker()


@asynccontextmanager
async def get_async_read_session_scope() -> AsyncGenerator[AsyncSession, None]:
    """ Return a session scope for async read session """
    session = _get_async_read_session()
    try:
        yield session
    finally:
        await session.close()


@asynccontextmanager
async def get_async_write_session_scope() -> AsyncGenerator[AsyncSession, None]:
    """ Return a session scope for async read session """
    session = _get_async_write_session()
    try:
        yield session
        await session.commit()
    except:
        await session.rollback()
        raise
    finally:
        await session.close()


@contextmanager
def get_sync_tileserv_db_scope() -> Generator[Session, None, None]:
    session = _get_sync_write_tileserv_session()
    try:
        yield session
    finally:
        logger.info('session closed by context manager')
        session.close()


@contextmanager
def get_read_session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations.
    THIS METHOD IS DEPRECATED! PLEASE MOVE TO USING: get_async_read_session_scope
    """
    session = _get_read_session()
    try:
        yield session
    finally:
        logger.info('session closed by context manager')
        session.close()


@contextmanager
def get_write_session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations.
    THIS METHOD IS DEPRECATED! PLEASE MOVE TO USING: get_async_write_session_scope
    """
    session = _get_write_session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
