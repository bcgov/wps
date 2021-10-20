#!/bin/bash

# DANGER! Don't run this in production!

# usage example:
# AWS_HOSTNAME=[your aws hostname] AWS_ACCESS_KEY=[your access key] AWS_SECRET_KEY=[your secret key] AWS_BUCKET=[your aws bucket] PG_HOSTNAME=localhost PG_DATABASE=wps ./cleanup_bucket.sh

# variable checks



if [ -z ${PG_HOSTNAME+0} ]
then
    echo "PG_HOSTNAME not specified"
    echo "Specify a postgress hostname"
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

_datestamp=`date +\%Y/\%m`
_target_folder="${PG_HOSTNAME}_${PG_DATABASE}/${_datestamp}"

echo "run the thing!"

cmd=`AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY}" AWS_SECRET_ACCESS_KEY="${AWS_SECRET_KEY}" aws --endpoint="https://${AWS_HOSTNAME}" s3 rm --recursive "s3://${AWS_BUCKET}/backup/${_target_folder}/"`
echo cmd

AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY}" AWS_SECRET_ACCESS_KEY="${AWS_SECRET_KEY}" aws --endpoint="https://${AWS_HOSTNAME}" s3 rm --recursive "s3://${AWS_BUCKET}/backup/${_target_folder}/"

echo "thing done run"
