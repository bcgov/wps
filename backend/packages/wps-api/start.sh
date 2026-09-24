#! /usr/bin/env sh
set -e

# run pre-start scripts
./prestart.sh
# set some defaults
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_MAX_REQUESTS="${GUNICORN_MAX_REQUESTS:-1000}"
GUNICORN_MAX_REQUESTS_JITTER="${GUNICORN_MAX_REQUESTS_JITTER:-100}"
APP_MODULE="${APP_MODULE:-app.main:app}"
# start the server
GUNICORN_CMD_ARGS="--max-requests ${GUNICORN_MAX_REQUESTS} --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER}" gunicorn "$APP_MODULE" --timeout 200 --workers $GUNICORN_WORKERS --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8080 --no-control-socket
