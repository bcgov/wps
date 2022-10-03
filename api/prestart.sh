#! /usr/bin/env bash

# Run migrations
PYTHONPATH=. poetry run alembic upgrade head
