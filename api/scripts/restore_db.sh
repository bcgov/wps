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
#   PGPASSWORD=PASSWORD_FOR_WPS_USER MODE=[linux or docker] ${THIS_FILE}
#
#   Assumes you have openshift command line tools installed and are logged in.
#
# Examples:
#   
#   PGPASSWORD=mywpspassword MODE=linux ./restore_db.sh
#

# We don't do: `set -e pipefail`, pg_restore 
set -euo pipefail

NATIVE_LINUX="linux"
DOCKER="docker"

MODE="${MODE:-$DOCKER}"

if [ "$MODE" = "$NATIVE_LINUX" ]
then
    echo "Running assuming you're running postgres natively on Linux."
fi
if [ "$MODE" = "$DOCKER" ]
then
    echo "Running assuming you're running postgres in Docker."
fi


if [ "$MODE" = "$NATIVE_LINUX" ]
then
    # Temporarily elevate roles in order to easily do restore:
    echo "You may be prompted for your sudo password..."
    ALTER="sudo -u postgres psql -U postgres -c \"alter role wps superuser;\""
    echo "${ALTER}"
    eval "${ALTER}"
fi


# Restore pg dump:
RESTORE="pg_restore -h localhost -d wps -U wps --no-owner --role=wps -n public -c tmp/dump_db.tar"
echo "${RESTORE}"
eval "${RESTORE}"


if [ "$MODE" = "$NATIVE_LINUX" ]
then
    # Change user rights back (remove superuser):
    ALTER="sudo -u postgres psql -U postgres -c \"alter role wps nosuperuser\""
    echo "${ALTER}"
    eval "${ALTER}"
fi

# Restore table data
COPY="psql -h localhost -d wps -U wps -c \"\copy model_run_grid_subset_predictions FROM 'tmp/model_run_grid_subset_predictions.csv' CSV\""
echo "You may be prompted for the wps password..."
echo "${COPY}"
eval "${COPY}"

# Restore table data
COPY="psql -h localhost -d wps -U wps -c \"\copy weather_station_model_predictions FROM 'tmp/weather_station_model_predictions.csv' CSV\""
echo "${COPY}"
eval "${COPY}"

# Ensure wpsread user has appropriate rights:
# This step assumes you have wpsread user!
# If it fails, you can go ahead and just make one: `create user wpsread with password 'wps';`
if [ "$MODE" = "$NATIVE_LINUX" ]
then
    # sudo -u postgres psql -U postgres -d wps -c "REASSIGN owned by wpsread to wps; drop owned by wpsread; drop role if exists wpsread; create user wpsread with password 'wps';"
    # sudo -u postgres psql -U postgres -d wps -c "grant connect on database wps to wpsread; grant usage on schema public to wpsread; grant select on all tables in schema public to wpsread;"
    GRANT="sudo -u postgres psql -U postgres -d wps -c \"grant connect on database wps to wpsread; grant usage on schema public to wpsread; grant select on all tables in schema public to wpsread;\""
fi
if [ "$MODE" = "$DOCKER" ]
then
    GRANT="psql -h localhost -U wps -d wps -c \"grant connect on database wps to wpsread; grant usage on schema public to wpsread; grant select on all tables in schema public to wpsread;\""
fi

echo "${GRANT}"
eval "${GRANT}"

exit 0
