#!/usr/bin/env bash
set -e
export DATABASE_URL="${DATABASE_URL}"

# Run migrations
PYTHONPATH=. poetry run alembic upgrade head
./pg_tileserv