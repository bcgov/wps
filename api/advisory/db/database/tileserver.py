""" The fire zone, fire centre and hfi polygons live in a different database - it's our "tileserver"
database.
"""
from typing import Generator
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from app import config

tileserver_read_user = config.get('TILESERVER_READ_USER', 'tileserv')
tileserver_write_user = config.get('TILESERVER_WRITE_USER', 'tileserv')
tileserver_postgres_password = config.get('TILESERVER_POSTGRES_PASSWORD', 'tileserv')
tileserver_postgres_read_host = config.get('TILESERVER_POSTGRES_READ_HOST', 'localhost')
tileserver_postgres_write_host = config.get('TILESERVER_POSTGRES_WRITE_HOST', 'localhost')
tileserver_postgres_database = config.get('TILESERVER_POSTGRES_DATABASE', 'tileserv')
postgres_port = config.get('POSTGRES_PORT', '5432')

TILESERVER_READ_STRING = f'postgresql://{tileserver_read_user}:{tileserver_postgres_password}@{tileserver_postgres_read_host}:{postgres_port}/{tileserver_postgres_database}'
TILESERVER_WRITE_STRING = f'postgresql://{tileserver_write_user}:{tileserver_postgres_password}@{tileserver_postgres_write_host}:{postgres_port}/{tileserver_postgres_database}'

tile_server_read_engine = create_engine(
    TILESERVER_READ_STRING,
    pool_size=int(config.get('POSTGRES_POOL_SIZE', 5)),
    max_overflow=int(config.get('POSTGRES_MAX_OVERFLOW', 10)),
    pool_pre_ping=True, connect_args={
        'options': '-c timezone=utc'})

# connect to database - defaulting to always use utc timezone
tile_server_write_engine = create_engine(TILESERVER_WRITE_STRING, connect_args={'options': '-c timezone=utc'})

tile_server_read_session = sessionmaker(
    autocommit=False, autoflush=False, bind=tile_server_read_engine)

tile_server_write_session = sessionmaker(
    autocommit=False, autoflush=False, bind=tile_server_write_engine)


def _get_tileserver_read_session() -> sessionmaker:
    """ abstraction used for mocking out a read session """
    return tile_server_read_session()


def _get_tileserver_write_session() -> sessionmaker:
    """ abstraction used for mocking out a write session """
    return tile_server_write_session()


@contextmanager
def get_tileserver_read_session_scope() -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of operations.
    """
    session = _get_tileserver_read_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_tileserver_write_session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = _get_tileserver_write_session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
