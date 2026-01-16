#!/bin/bash

# Fills recently partitioned tables with data from the origin table and swaps in the partition
#
# usage example:
# PG_PASSWORD=wps PG_HOSTNAME=localhost PG_PORT=5432 PG_USER=wps PG_DATABASE=wps TABLE=table ./fill_partition_data.sh

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

ENCODED_PASS=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${PG_PASSWORD}', safe=''))")
PGSLICE_URL=postgresql://${PG_USER}:${ENCODED_PASS}@${PG_HOSTNAME}:${PG_PORT}/${PG_DATABASE}
# Fill the partitions with data from the original table
pgslice fill $TABLE --url $PGSLICE_URL
# Analyze for query planner
pgslice analyze $TABLE --url $PGSLICE_URL
# Swap the intermediate table with the original table
pgslice swap $TABLE --url $PGSLICE_URL
# Fill the rest (rows inserted between the first fill and the swap)
pgslice fill $TABLE --swapped --url $PGSLICE_URL