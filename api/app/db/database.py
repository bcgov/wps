""" Setup database to perform CRUD transactions
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .. import config

DB_WRITE_STRING = 'postgres://{}:{}@{}:{}/{}'.format(
    config.get('POSTGRES_WRITE_USER', 'wps'),
    config.get('POSTGRES_PASSWORD', 'wps'),
    config.get('POSTGRES_WRITE_HOST', 'localhost'),
    config.get('POSTGRES_PORT', '5432'),
    config.get('POSTGRES_DATABASE', 'wps'))

DB_READ_STRING = 'postgres://{}:{}@{}:{}/{}'.format(
    config.get('POSTGRES_READ_USER', 'wpsread'),
    config.get('POSTGRES_PASSWORD', 'wps'),
    config.get('POSTGRES_READ_HOST', 'localhost'),
    config.get('POSTGRES_PORT', '5432'),
    config.get('POSTGRES_DATABASE', 'wps'))

# connect to database - defaulting to always use utc timezone
_write_engine = create_engine(DB_WRITE_STRING, connect_args={
                              'options': '-c timezone=utc'})
# use pre-ping on read, as connections are quite often stale due to how few users we have at the moment.
_read_engine = create_engine(
    DB_READ_STRING,
    pool_size=config.get('POSTGRES_POOL_SIZE', 5),
    max_overflow=config.get('POSTGRES_MAX_OVERFLOW', 10),
    pool_pre_ping=True, connect_args={
        'options': '-c timezone=utc'})

# bind session to database
_write_session = sessionmaker(
    autocommit=False, autoflush=False, bind=_write_engine)
_read_session = sessionmaker(
    autocommit=False, autoflush=False, bind=_read_engine)

# constructing a base class for declarative class definitions
Base = declarative_base()


def get_read_session() -> Session:
    """ Wrap getting read session to assist in making unit tests a bit easier """
    return _read_session()


def get_write_session() -> Session:
    """ Wrap getting write session to assist in making unit test a bit easier"""
    return _write_session()
