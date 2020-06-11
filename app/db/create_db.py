""" Creates all database objects """
from db.database import BASE, ENGINE
import db.models # pylint: disable = unused-import

BASE.metadata.create_all(ENGINE)
