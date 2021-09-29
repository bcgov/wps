#!/bin/bash

# usage example:
# HOSTNAME=localhost PORT=5432 USER=wps BUCKET=gpdqha DATABASE=wps ./backup_to_s3.sh

# borrowing a lot from https://github.com/BCDevOps/backup-container
_timestamp=`date +\%Y-\%m-\%d_%H-%M-%S`
_target_filename="${DATABASE}_${_timestamp}.sql.gz"

# Using s3cmd (https://github.com/s3tools/s3cmd) to upload the database backup to S3.
# TODO: figure out passing password for DB
# TODO: figure out passing credentials for s3cmd
# TODO: what is -Fp ?
# backupcontainer does:
# PGPASSWORD=${_password} pg_dump -Fp -h "${_hostname}" ${_portArg} -U "${_username}" "${_database}" | gzip > ${_backupFile}
pg_dump -h "${HOSTNAME}}" -p ${PORT} -U "${USER}" "${DATABASE}" | gzip | s3cmd put - s3://${BUCKET}/backup/${_target_filename}
