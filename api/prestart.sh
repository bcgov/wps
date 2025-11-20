#! /usr/bin/env bash

# Run migrations
PYTHONPATH=. alembic upgrade head
