#!/usr/bin/env bash
set -e

# Run migrations
PYTHONPATH=. poetry run alembic upgrade head
./pg_tileserv