#!/bin/bash

# Adds a new partition for the next month, fills and swaps any partitions
#
# usage example:
# PG_PASSWORD=wps PG_HOSTNAME=localhost PG_PORT=5432 PG_USER=wps PG_DATABASE=wps TABLE=table ./partition_and_archive.sh

# From http://redsymbol.net/articles/unofficial-bash-strict-mode/ 
# Exits execution if any command fails for safety

set -euxo pipefail

# We can extend this later on to be a list of tables
TABLE=weather_station_model_predictions

# variable checks
if [ -z ${PG_PASSWORD+0} ]
then
    echo "PG_PASSWORD not specified"
    echo "Specify a postgres password"
    exit 1
fi

if [ -z ${PG_HOSTNAME+0} ]
then
    echo "PG_HOSTNAME not specified"
    echo "Specify a postgres hostname"
    exit 1
fi

if [ -z ${PG_PORT+0} ]
then
    echo "PG_PORT not specified"
    echo "Specify a postgres port"
    exit 1
fi

if [ -z ${PG_USER+0} ]
then
    echo "PG_USER not specified"
    echo "Specify a postgres user"
    exit 1
fi

if [ -z ${PG_DATABASE+0} ]
then
    echo "PG_DATABASE not specified"
    echo "Specify a postgres database"
    exit 1
fi

export PGSLICE_URL = "postgresql://${PG_USER}:${PG_PASSWORD}@${PG_HOSTNAME}:${PG_PORT}/${PG_DATABASE}"
# Add partitions to the intermediate table (assumes it already exists)
pgslice add_partitions $TABLE --intermediate --future 1
# Fill the partitions with data from the original table
pgslice fill $TABLE
# Analyze for query planner
pgslice analyze $TABLE
# Swap the intermediate table with the original table
pgslice swap $TABLE
# Fill the rest (rows inserted between the first fill and the swap)
pgslice fill $TABLE --swapped
# Dump any retired tables to S3 and drop
pg_dump -c -Fc -t ${TABLE}_retired $PGSLICE_URL | gzip | AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY}" AWS_SECRET_ACCESS_KEY="${AWS_SECRET_KEY}" aws --endpoint="https://${AWS_HOSTNAME}" s3 cp - "s3://${AWS_BUCKET}/retired/${TABLE}_retired.dump.gz"
psql -c "DROP TABLE ${TABLE}_retired" $PGSLICE_URL