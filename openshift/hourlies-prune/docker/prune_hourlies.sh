#!/bin/bash

# usage example:
# AWS_HOSTNAME=[your aws hostname] AWS_ACCESS_KEY=[your access key] AWS_SECRET_KEY=[your secret key] AWS_BUCKET=[your aws bucket] ./prune_hourlies.sh

# variable checks

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

hourlies_path="sfms/uploads/hourlies"
day_before_yesterday=$(TZ=America/Vancouver date -v-2d -I)

echo "Cleaning up hourlies from ${AWS_BUCKET}/${hourlies_path}/${day_before_yesterday}"
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY}" AWS_SECRET_ACCESS_KEY="${AWS_SECRET_KEY}" aws --endpoint="https://${AWS_HOSTNAME}" s3 rm --recursive "s3://${AWS_BUCKET}/${hourlies_path}/${day_before_yesterday}/"
echo 'Complete'