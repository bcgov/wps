#!/bin/bash

# usage example:
# HOSTNAME=localhost PORT=5432 USER=wps BUCKET=gpdqha DATABASE=wps ./backup_to_s3.sh

_timestamp=`date +\%Y-\%m-\%d_%H-%M-%S`
_target_filename="${DATABASE}_${_timestamp}.sql.gz"

# Using s3cmd (https://github.com/s3tools/s3cmd) to upload the database backup to S3.
# TODO: figure out passing password for DB
# TODO: figure out passing credentials for s3cmd
# pg_dump -h localhost -p ${PORT} -U ${USER} ${DATABASE} | gzip | s3cmd put - s3://${BUCKET}/backup/${_target_filename}
