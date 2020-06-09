""" Setup database to perform CRUD transactions
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import config

DB_STRING = 'postgres://{}:{}@{}:{}/{}'.format(
    config.get('POSTGRES_USER', 'wps'),
    config.get('POSTGRES_PASSWORD', 'wps'),
    config.get('POSTGRES_HOST', 'db'),
    config.get('POSTGRES_PORT', '5432'),
    config.get('POSTGRES_DATABASE', 'wps'))

# connect to database
ENGINE = create_engine(DB_STRING)

# bind session to database
SESSION = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)

# constructing a base class for declarative class definitions
BASE = declarative_base()
