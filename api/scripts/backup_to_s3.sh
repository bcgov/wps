#!/bin/bash

# usage example:
# PG_PASSWORD=wps PG_HOSTNAME=localhost PG_PORT=5432 PG_USER=wps PG_DATABASE=wps AWS_HOSTNAME=[your aws hostname] AWS_ACCESS_KEY=[your access key] AWS_SECRET_KEY=[your secret key] AWS_BUCKET=[your aws bucket] ./backup_to_s3.sh

# borrowing a lot from https://github.com/BCDevOps/backup-container
_timestamp=`date +\%Y-\%m-\%d_%H-%M-%S`
_datestamp=`date +\%Y/\%m`
_target_filename="${PG_HOSTNAME}_${PG_DATABASE}_${_timestamp}.sql.gz"
_target_folder="${PG_HOSTNAME}_${PG_DATABASE}/${_datestamp}"


# backupcontainer does:
# PGPASSWORD=${_password} pg_dump -Fp -h "${_hostname}" ${_portArg} -U "${_username}" "${_database}" | gzip > ${_backupFile}

# Using s3cmd (https://github.com/s3tools/s3cmd) to upload the database backup to S3:
# pg_dump | gzip | s3cmd
# this is tested and works.
# PGPASSWORD="${PG_PASSWORD}" pg_dump -Fp -h "${PG_HOSTNAME}" -p ${PG_PORT} -U "${PG_USER}" "${PG_DATABASE}" | gzip | s3cmd --host "${AWS_HOSTNAME}" --access_key "${AWS_ACCESS_KEY}" --secret_key "${AWS_SECRET_KEY}" --host-bucket "${AWS_BUCKET}" --expiry-days 30 put - s3://${AWS_BUCKET}/backup/${_target_folder}/${_target_filename}

# Using the official aws cli to upload the database back to S3:
# pg_dump | gzip | aws s3:
# this is tested and works.
PGPASSWORD="${PG_PASSWORD}" pg_dump -Fp -h "${PG_HOSTNAME}" -p ${PG_PORT} -U "${PG_USER}" "${PG_DATABASE}" | gzip | AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY}" AWS_SECRET_ACCESS_KEY="${AWS_SECRET_KEY}" aws --endpoint="https://${AWS_HOSTNAME}" s3 cp - "s3://${AWS_BUCKET}/backup/${_target_folder}/${_target_filename}"


