#!/bin/bash

# Database copy helper
#
#   Connect to an openshift pod, dump a postgresql database and copy it locally.
#
# Usage:
#
#   PROJECT=OPENSHIFT_PROJECT_NAME POD=OPENSHIFT_POD DATABASE=POSTGRESQL_DATABASE ${THIS_FILE}
#
#   Assumes you have openshift command line tools installed and are logged in.
#
# Examples:
#   
#   Copy database from a pod in production.
#   PGPASSWORD=mywpspassword ./restore_db.sh
#

set -euo pipefail


ALTER="sudo -u postgres psql -U postgres -c \"alter role wps superuser;\""
echo "${ALTER}"
# eval "${ALTER}"

RESTORE="pg_restore -h localhost -d wps -U wps --no-owner --role=wps -c dump_db.tar"
echo "${RESTORE}"
# eval "${RESTORE}"

# change user rights back:
ALTER="sudo -u postgres psql -U postgres -c \"alter role wps nosuperuser\""
echo "${ALTER}"
# eval "${ALTER}"

# copy model_run_grid_subset_predictions from csv
COPY="psql -h localhost -d wps -U wps -c \"\copy model_run_grid_subset_predictions FROM 'model_run_grid_subset_predictions.csv' CSV\""
echo "${COPY}"
eval "${COPY}"

COPY="psql -h localhost -d wps -U wps -c \"\copy weather_station_model_predictions FROM 'weather_station_model_predictions.csv' CSV\""
echo "${COPY}"
# eval "${COPY}"

exit 0
#
# example 2:
#   Restore the database with a different name and owner.
#
#   give the wps user superuser roles for restore:
#   psql -U postgres -c "alter role wps superuser;"
#
#   restore the database to wps database:
#   pg_restore -h localhost -d wps -U wps --no-owner --role=wps -c dump_db.tar
#
#   change user rights back:
#   psql -U postgres -c "alter role wps nosuperuser"

