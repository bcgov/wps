""" Setup database to perform CRUD transactions
"""
import config

write_user = config.get('TILESERV_DB_WRITE_USER', 'tileserv')
postgres_password = config.get('TILESERV_DB_PASSWORD', 'tileserv')
postgres_write_host = config.get('TILESERV_WRITE_HOST', 'localhost')
postgres_port = config.get('TILESERV_DB_PORT', '5432')
postgres_database = config.get('TILESERV_DB', 'tileserv')

# pylint: disable=line-too-long
DB_WRITE_STRING = f'postgresql://{write_user}:{postgres_password}@{postgres_write_host}:{postgres_port}/{postgres_database}'
