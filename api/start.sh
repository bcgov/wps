#! /usr/bin/env sh
set -e

./prestart.sh
poetry run gunicorn app.main:app --keep-alive 65 --workers 8 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8080
