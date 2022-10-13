#! /usr/bin/env sh
set -e

# run pre-start scripts
./prestart.sh
# set some defaults
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
# start the server
poetry run gunicorn app.main:app --timeout 200 --workers $GUNICORN_WORKERS --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8080
