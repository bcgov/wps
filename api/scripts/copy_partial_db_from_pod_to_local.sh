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
#   PROJECT=auzhsi-prod POD=patroni-wps-prod-2 DATABASE=wps-prod ./copy_db_from_pod_to_local.sh
#

set -euo pipefail

#####################
# Define some globals
#####################

# openshift rsh command.
RSH="oc -n ${PROJECT} rsh ${POD}"

################
# Variable check
################
if [ -z ${PROJECT+0} ]
then
    echo "---------------------"
    echo "PROJECT not specified"
    print "\nSpecify a project:\n\n"
    RSH="oc get projects"
    eval $RSH
    exit 1
fi

if [ -z ${POD+0} ]
then
    echo "-----------------"
    echo "POD not specified"
    printf "\nSpecify a pod:\n\n"
    RSH="oc -n ${PROJECT} get pods"
    eval $RSH
    exit 1
fi

# Check that the pod specified is a replica, not a leader. We don't want to bog
# down the leader, since it's getting a lot of stuff written to it.
if eval "${RSH} patronictl list" | grep ${POD} | grep -q 'Leader'; then
    echo "-------------------------"
    echo "Please specify a Replica!"
    printf "\n\n"
    eval "${RSH} patronictl list"
    exit 1
fi

if [ -z ${DATABASE+0} ]
then
    echo "----------------------"
    echo "DATABASE not specified"
    echo "Specify a database:"
    echo ""
    eval "${RSH} psql -c '\l'"
    exit 1
fi

#####################
# Backup the database
#####################

# name of file to dump.
FILENAME="dump_db.tar"

# command to dump database (excluding the giant tables)
# --clean clean (drop) database objects before recreating
# -Ft output file format (custom, directory, tar, plain text (default))
# --exclude-table-data get the table definitions, but not the data
PG_DUMP="pg_dump --file=/tmp/${FILENAME} --clean -Ft ${DATABASE} --exclude-table-data=model_run_grid_subset_predictions --exclude-table-data=weather_station_model_predictions"
# command to dump database on pod.
BACKUP_COMMAND="${RSH} ${PG_DUMP}"

echo "pgdump..."
echo $BACKUP_COMMAND
# eval "${BACKUP_COMMAND}"
printf "\n\n"

# command to dump remaning tables
STATION_FILE="weather_station_model_predictions.csv"
GRID_FILE="model_run_grid_subset_predictions.csv"
STATION_PREDICTIONS="\copy (SELECT * FROM weather_station_model_predictions WHERE prediction_timestamp > current_date - 5) to '/tmp/${STATION_FILE}' with csv"
GRID_PREDICTIONS="\copy (SELECT * FROM model_run_grid_subset_predictions WHERE prediction_timestamp > current_date - 5) to '/tmp/${GRID_FILE}' with csv"

COPY_COMMAND="${RSH} psql ${DATABASE} -c \"${STATION_PREDICTIONS}\""
echo "copy weather_station_model_predictions to csv..."
echo "${COPY_COMMAND}"
# eval "${COPY_COMMAND}"
printf "\n\n"

COPY_COMMAND="${RSH} psql ${DATABASE} -c \"${GRID_PREDICTIONS}\""
echo "copy model_run_grid_subset_predictions to csv..."
echo "${COPY_COMMAND}"
# eval "${COPY_COMMAND}"
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
    # eval $COMPRESS_COMMAND
done
printf "\n\n"

# copy the data dump from server to local.
# you'll get a weird message that says: "tar: Removing leading `/' from member names" - just ignore it.
echo "copy *.gz files locally... (you can ignore the error message re leading '/')"
for file in "${FILES[@]}"
do
    COPY_COMMAND="oc -n ${PROJECT} cp ${POD}:/tmp/${file}.gz ./${file}.gz"
    echo "${COPY_COMMAND}"
    # eval "${COPY_COMMAND}"
done
printf "\n\n"

# delete the remote files (cleanup).
echo "delete remote files..."
for file in "${FILES[@]}"
do
    DELETE_COMMAND="${RSH} rm /tmp/${file}.gz"
    echo "${DELETE_COMMAND}"
    # eval "${DELETE_COMMAND}"
done
printf "\n\n"

# unzip it locally
echo "unzip local files..."
for file in "${FILES[@]}"
do
    UNZIP_COMMAND="gunzip ${file}.gz"
    echo "${UNZIP_COMMAND}"
    # eval "${UNZIP_COMMAND}"
done
printf "\n\n"

####################
# Restore it locally
####################

# Now do the restore, there are a number of ways to do this.
# example 1:
#   Restore the database with the same name, with the same owner as the source.
# 
#   pg_restore -d ${DATABASE} -U postgres -c --if-exists ${FILENAME}
#   - Adding --if-exists hides harmless errors you may see the first time you run it if there isn't already
#       a database with tables etc. to drop.
#   - This assumes the existence of a database named ${DATABASE}
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

