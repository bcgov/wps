#!/bin/bash

# Database restore helper
#
#   Restore database dump and csv with data to local database.
#
# Assumptions:
#
#   - Assumes your database server is up and running.
#   - Assumes you are using the users wps and wpsread.
#   - Assumes you already have a database and users in place.
#
# Usage:
#
#   PGPASSWORD=[password for wps user] MODE=[linux or docker] ${THIS_FILE}
#
#   Assumes you have openshift command line tools installed and are logged in.
#
# Examples:
#   
#   PGPASSWORD=mywpspassword MODE=native ./restore_db.sh
#

set -euo pipefail

NATIVE="native"
DOCKER="docker"

PARTIAL="${PARTIAL:-True}"
MODE="${MODE:-$DOCKER}"
BACKUP_FOLDER="${BACKUP_FOLDER:-./tmp}"
WITH_WPSREAD="${WITH_WPSREAD:-False}"

if [ "$MODE" = "$NATIVE" ]
then
    echo "Running assuming you're running postgres natively on Linux/Mac."
fi
if [ "$MODE" = "$DOCKER" ]
then
    echo "Running assuming you're running postgres in Docker."
fi


if [ "$MODE" = "$NATIVE" ]
then
    # Temporarily elevate roles in order to easily do restore:
    echo "You may be prompted for your sudo password..."
    ALTER="sudo -u postgres psql -U postgres -c \"alter role wps superuser;\""
    echo "${ALTER}"
    eval "${ALTER}"
fi


# Restore pg dump:
RESTORE="pg_restore -h localhost -d wps -U wps --no-owner --role=wps -n public -c ${BACKUP_FOLDER}/dump_db.tar"
echo "${RESTORE}"
eval "${RESTORE}"


if [ "$MODE" = "$NATIVE" ]
then
    # Change user rights back (remove superuser):
    ALTER="sudo -u postgres psql -U postgres -c \"alter role wps nosuperuser\""
    echo "${ALTER}"
    eval "${ALTER}"
fi

if [ "$PARTIAL" = "True" ]
then
    # Restore table data
    COPY="psql -h localhost -d wps -U wps -c \"\copy model_run_grid_subset_predictions FROM '${BACKUP_FOLDER}/model_run_grid_subset_predictions.csv' CSV\""
    echo "You may be prompted for the wps password..."
    echo "${COPY}"
    eval "${COPY}"

    # Restore table data
    COPY="psql -h localhost -d wps -U wps -c \"\copy weather_station_model_predictions FROM '${BACKUP_FOLDER}/weather_station_model_predictions.csv' CSV\""
    echo "${COPY}"
    eval "${COPY}"
fi

# Ensure wpsread user has appropriate rights:
if [ "$WITH_WPSREAD" == "True" ]
then
    # This step assumes you have wpsread user!
    # If it fails, you can go ahead and just make one: `create user wpsread with password 'wps';`
    if [ "$MODE" = "$NATIVE" ]
    then
        GRANT="sudo -u postgres psql -U postgres -d wps -c \"grant connect on database wps to wpsread; grant usage on schema public to wpsread; grant select on all tables in schema public to wpsread;\""
    fi
    if [ "$MODE" = "$DOCKER" ]
    then
        GRANT="psql -h localhost -U wps -d wps -c \"grant connect on database wps to wpsread; grant usage on schema public to wpsread; grant select on all tables in schema public to wpsread;\""
    fi

    echo "${GRANT}"
    eval "${GRANT}"
fi

exit 0
