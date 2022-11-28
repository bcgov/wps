""" Setup database to perform CRUD transactions
"""
import config

write_user = config.get('TILESERV_DB_WRITE_USER', 'tileserv')
postgres_password = config.get('TILESERV_DB_PASSWORD', 'tileserv')
postgres_write_host = config.get('TILESERV_WRITE_HOST', 'host.docker.internal')
postgres_port = config.get('TILESERV_DB_PORT', '5432')
postgres_database = config.get('TILESERV_DB', 'tileserv')
postgres_url = config.get('DATABASE_URL')

DATABASE_URL = postgres_url
