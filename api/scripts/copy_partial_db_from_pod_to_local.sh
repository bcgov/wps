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
#   Copy partial database from a pod in production.
#   PROJECT=e1e498-prod POD=patroni-wps-prod-2 DATABASE=wps ./copy_partial_db_from_pod_to_local.sh
#

set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"

source "$SCRIPT_DIR/common_oc_checks.sh"

#####################
# Backup the database
#####################

# Create a lock file
CREATE_LOCK="mkdir /tmp/${DATABASE}.lock"
LOCK_COMMAND="${RSH} ${CREATE_LOCK}"
echo $LOCK_COMMAND
eval "${LOCK_COMMAND}"
printf "\n\n"

# name of file to dump.
FILENAME="dump_db.tar"

# command to dump database (excluding the giant tables)
# --clean clean (drop) database objects before recreating
# -Ft output file format (custom, directory, tar, plain text (default))
# --exclude-table-data get the table definitions, but not the data
PG_DUMP="pg_dump --file=/tmp/${FILENAME} --clean -Fc ${DATABASE} --exclude-table-data=model_run_grid_subset_predictions --exclude-table-data=weather_station_model_predictions --exclude-table-data=c_haines_polygons"
# command to dump database on pod.
BACKUP_COMMAND="${RSH} ${PG_DUMP}"

echo "pgdump..."
echo $BACKUP_COMMAND
eval "${BACKUP_COMMAND}"
printf "\n\n"

# command to dump remaining tables
STATION_FILE="weather_station_model_predictions.csv"
GRID_FILE="model_run_grid_subset_predictions.csv"
STATION_PREDICTIONS="\copy (SELECT * FROM weather_station_model_predictions WHERE prediction_timestamp > current_date - 5) to '/tmp/${STATION_FILE}' with csv"
GRID_PREDICTIONS="\copy (SELECT * FROM model_run_grid_subset_predictions WHERE prediction_timestamp > current_date - 5) to '/tmp/${GRID_FILE}' with csv"

COPY_COMMAND="${RSH} psql ${DATABASE} -c \"${STATION_PREDICTIONS}\""
echo "copy weather_station_model_predictions to csv..."
echo "${COPY_COMMAND}"
eval "${COPY_COMMAND}"
printf "\n\n"

COPY_COMMAND="${RSH} psql ${DATABASE} -c \"${GRID_PREDICTIONS}\""
echo "copy model_run_grid_subset_predictions to csv..."
echo "${COPY_COMMAND}"
eval "${COPY_COMMAND}"
printf "\n\n"

##################
# Copy it to local
##################

FILES=( "${FILENAME}" "${STATION_FILE}" "${GRID_FILE}" )

# compress files on the remote server.
echo "compress files..."
for file in "${FILES[@]}"
do
    COMPRESS_COMMAND="${RSH} gzip /tmp/${file}"
    echo "compress ${file}..."
    echo "${COMPRESS_COMMAND}"
    eval $COMPRESS_COMMAND
done
printf "\n\n"

# copy the data dump from server to local.
# you'll get a weird message that says: "tar: Removing leading `/' from member names" - just ignore it.
echo "copy *.gz files locally... (you can ignore the error message re leading '/')"
for file in "${FILES[@]}"
do
    COPY_COMMAND="oc -n ${PROJECT} cp ${POD}:/tmp/${file}.gz ./${file}.gz"
    echo "${COPY_COMMAND}"
    eval "${COPY_COMMAND}"
done
printf "\n\n"

# delete the remote files (cleanup).
echo "delete remote files..."
for file in "${FILES[@]}"
do
    DELETE_COMMAND="${RSH} rm /tmp/${file}.gz"
    echo "${DELETE_COMMAND}"
    eval "${DELETE_COMMAND}"
done
printf "\n\n"

# remove the lock file
echo "deleting lock file..."
REMOVE_LOCK="rmdir /tmp/${DATABASE}.lock"
UNLOCK_COMMAND="${RSH} ${REMOVE_LOCK}"
echo $UNLOCK_COMMAND
eval "${UNLOCK_COMMAND}"
printf "\n\n"


# unzip it locally
echo "unzip local files..."
for file in "${FILES[@]}"
do
    UNZIP_COMMAND="gunzip ${file}.gz"
    echo "${UNZIP_COMMAND}"
    eval "${UNZIP_COMMAND}"
done
printf "\n\n"
