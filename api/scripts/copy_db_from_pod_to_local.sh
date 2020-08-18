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
#   PROJECT=auzhsi-prod POD=patroni-wps-api-prod-2 DATABASE=wps-api-prod ./copy_db_from_pod_to_local.sh
#

set -euo pipefail

################
# Variable check
################
if [ -z ${PROJECT+0} ]
then
    echo "PROJECT not specified"
    exit 1
fi

if [ -z ${POD+0} ]
then
    echo "POD not specified"
    exit 1
fi

if [ -z ${DATABASE+0} ]
then
    echo "DATABASE not specified"
    exit 1
fi


#####################
# Define some globals
#####################

# name of file to dump.
FILENAME="dump_db.tar"
# openshift rsh command.
RSH="oc -n ${PROJECT} rsh ${POD}"


#####################
# Backup the database
#####################

# command to dump database.
# --clean clean (drop) database objects before recreating
# -Ft output file format (custom, directory, tar, plain text (default))
PG_DUMP="pg_dump --file=/tmp/${FILENAME} --clean -Ft ${DATABASE}"
# command to dump database on pod.
BACKUP_COMMAND="${RSH} ${PG_DUMP}"

echo $BACKUP_COMMAND
eval "${BACKUP_COMMAND}"

##################
# Copy it to local
##################

# compress it on the remote server.
COMPRESS_COMMAND="${RSH} gzip /tmp/${FILENAME}"
echo $COMPRESS_COMMAND
eval $COMPRESS_COMMAND

# copy the data dump from server to local.
# you'll get a weird message that says: "tar: Removing leading `/' from member names" - just ignore it.
COPY_COMMAND="oc -n ${PROJECT} cp ${POD}:/tmp/${FILENAME}.gz ."
echo $COPY_COMMAND
eval $COPY_COMMAND

# delete the remote file (cleanup).
DELETE_COMMAND="${RSH} rm /tmp/${FILENAME}.gz"
echo $DELETE_COMMAND
eval $DELETE_COMMAND

# unzip it locally
gunzip "${FILENAME}.gz"

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
#   pg_restore -d wps -U wps --no-owner --role=wps -c dump_db.tar
#
#   change user rights back:
#   psql -U postgres -c "alter role wps nosuperuser"

