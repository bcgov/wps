#!/bin/bash

# usage example:
# PG_PASSWORD=wps PG_HOSTNAME=localhost PG_PORT=5432 PG_USER=wps PG_DATABASE=wps AWS_HOSTNAME=[your aws hostname] AWS_ACCESS_KEY=[your access key] AWS_SECRET_KEY=[your secret key] AWS_BUCKET=[your aws bucket] ./backup_to_s3.sh

# variable checks
if [ -z ${PG_PASSWORD+0} ]
then
    echo "PG_PASSWORD not specified"
    echo "Specify a postgress password"
    exit 1
fi

if [ -z ${PG_HOSTNAME+0} ]
then
    echo "PG_HOSTNAME not specified"
    echo "Specify a postgress hostname"
    exit 1
fi

if [ -z ${PG_PORT+0} ]
then
    echo "PG_PORT not specified"
    echo "Specify a postgress port"
    exit 1
fi

if [ -z ${PG_USER+0} ]
then
    echo "PG_USER not specified"
    echo "Specify a postgress user"
    exit 1
fi

if [ -z ${PG_DATABASE+0} ]
then
    echo "PG_DATABASE not specified"
    echo "Specify a postgress database"
    exit 1
fi

if [ -z ${AWS_HOSTNAME+0} ]
then
    echo "AWS_HOSTNAME not specified"
    echo "Specify an AWS hostname"
    exit 1
fi

if [ -z ${AWS_ACCESS_KEY+0} ]
then
    echo "AWS_ACCESS_KEY not specified"
    echo "Specify an AWS access key"
    exit 1
fi

if [ -z ${AWS_SECRET_KEY+0} ]
then
    echo "AWS_SECRET_KEY not specified"
    echo "Specify an AWS secret key"
    exit 1
fi

if [ -z ${AWS_BUCKET+0} ]
then
    echo "AWS_BUCKET not specified"
    echo "Specify an AWS bucket"
    exit 1
fi

# borrowing a lot from https://github.com/BCDevOps/backup-container
_timestamp=`date +\%Y-\%m-\%d_%H-%M-%S`
_datestamp=`date +\%Y/\%m`
_target_filename="${PG_HOSTNAME}_${PG_DATABASE}_${_timestamp}.sql.gz"
_target_folder="${PG_HOSTNAME}_${PG_DATABASE}/${_datestamp}"

# Using the official aws cli to upload the database back to S3:
# pg_dump | gzip | aws s3:
# this is tested and works.
PGPASSWORD="${PG_PASSWORD}" pg_dump -Fp -h "${PG_HOSTNAME}" -p ${PG_PORT} -U "${PG_USER}" -n "public" --no-owner "${PG_DATABASE}" | gzip | AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY}" AWS_SECRET_ACCESS_KEY="${AWS_SECRET_KEY}" aws --endpoint="https://${AWS_HOSTNAME}" s3 cp - "s3://${AWS_BUCKET}/backup/${_target_folder}/${_target_filename}"


# Run python code to prune old backups.
cd /tmp
poetry env activate
python prune.py