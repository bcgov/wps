""" Setup database to perform CRUD transactions
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .. import config

DB_STRING = 'postgres://{}:{}@{}:{}/{}'.format(
    config.get('POSTGRES_USER', 'wps'),
    config.get('POSTGRES_PASSWORD', 'wps'),
    config.get('POSTGRES_HOST', 'localhost'),
    config.get('POSTGRES_PORT', '5432'),
    config.get('POSTGRES_DATABASE', 'wps'))

# connect to database - defaulting to always use utc timezone
engine = create_engine(DB_STRING, connect_args={'options': '-c timezone=utc'})

# bind session to database
_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# constructing a base class for declarative class definitions
Base = declarative_base()


def get_session() -> Session:
    """ Wrap getting session to assist in making unit tests a bit easier """
    return _session()
