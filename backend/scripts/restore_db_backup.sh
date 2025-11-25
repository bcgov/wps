#!/bin/bash

# Database backup restore helper
#
#   Restore database backup (made by the backup container).
#   This script works on MacOS with postgis installed using brew.
#
# Examples:
#   
#   FILENAME=some_backup.sql.gz ./restore_db_backup.sh
#

# drop existing DB
psql postgres -c "drop database wps;" || true

# create wps user
psql postgres -c "create user wps with password 'wps';" || true

# create wps database
psql postgres -c "create database wps with owner wps;"

# restore database from backup
# based on https://github.com/BCDevOps/backup-container/blob/master/docker/backup.postgres.plugin
gunzip -c "${FILENAME}" | psql -v ON_ERROR_STOP=1 -x -h "localhost" -d "wps"