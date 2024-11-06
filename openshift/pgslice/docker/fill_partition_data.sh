#!/bin/bash

# usage example:
# PG_PASSWORD=wps PG_HOSTNAME=localhost PG_PORT=5432 PG_USER=wps PG_DATABASE=wps TABLE=table ./backup_to_s3.sh

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

if [ -z ${TABLE+0} ]
then
    echo "TABLE not specified"
    echo "Specify a postgres table"
    exit 1
fi

export PGSLICE_URL = "postgresql://${PG_USER}:${PG_PASSWORD}@${PG_HOSTNAME}:${PG_PORT}/${PG_DATABASE}"
pgslice fill $TABLE
pgslice analyze $TABLE
pgslice swap $TABLE