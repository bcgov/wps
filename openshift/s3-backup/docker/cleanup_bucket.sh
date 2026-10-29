#!/bin/bash

# DANGER! Don't run this in production!

# usage example:
# SUFFIX=pr-### CLUSTER_NAME=[postgres cluster name] AWS_HOSTNAME=[your aws hostname] AWS_ACCESS_KEY=[your access key] AWS_SECRET_KEY=[your secret key] AWS_BUCKET=[your aws bucket] ./cleanup_bucket.sh

# variable checks
if [ -z ${SUFFIX+0} ]
then
    echo "SUFFIX not specified"
    echo "Specify a PR suffix"
    exit 1
fi

if [ "$SUFFIX" == "prod" ]
then
    echo "Please only specify a dev suffix"
    exit 1
fi

if [ -z "${CLUSTER_NAME}" ]
then
    echo "CLUSTER_NAME not specified"
    echo "Specify the postgres cluster name, e.g. wps-crunchydb-16-pr-###"
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

# pgbackrest/ holds the Crunchy cluster's own backups; backup/ holds the
# pg_dump files written by backup_to_s3.sh (named after PG_HOSTNAME and PG_DATABASE).
for _target_path in "s3://${AWS_BUCKET}/pgbackrest/${SUFFIX}/" "s3://${AWS_BUCKET}/backup/${CLUSTER_NAME}-primary_wps/"
do
    echo "Cleaning up ${_target_path}"
    AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY}" AWS_SECRET_ACCESS_KEY="${AWS_SECRET_KEY}" aws --endpoint="https://${AWS_HOSTNAME}" s3 rm --recursive "${_target_path}"
done
echo 'Complete'