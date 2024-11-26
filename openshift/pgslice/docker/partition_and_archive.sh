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

ENCODED_PASS=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${PG_PASSWORD}'))")
PGSLICE_URL=postgresql://${PG_USER}:${ENCODED_PASS}@${PG_HOSTNAME}:${PG_PORT}/${PG_DATABASE}

# Add new partition for next month
NEXT_MONTH_DATE=$(date -d "$(date +%Y-%m-01) next month" +%Y%m)
FIRST_DAY_NEXT_MONTH=$(date -d "$(date +%Y-%m-01) next month" +%Y-%m-%d)
LAST_DAY_NEXT_MONTH=$(date -d "$(date +%Y-%m-01) next month +1 month -1 day" +%Y-%m-%d)
echo "Creating new partition for dates: $FIRST_DAY_NEXT_MONTH to $LAST_DAY_NEXT_MONTH"

NEW_PARTITION="${TABLE}_${NEXT_MONTH_DATE}"
DETACH_COMMAND="
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_partitions WHERE schemaname = 'public' AND tablename = 'weather_station_model_predictions_202408') THEN
        EXECUTE 'DROP PARTITION FOR (PARTITION weather_station_model_predictions_202408)';
    END IF;
END $$;
"


NEW_PARTITION_COMMAND="CREATE TABLE ${TABLE}_${NEXT_MONTH_DATE} PARTITION OF $TABLE FOR VALUES FROM ('$FIRST_DAY_NEXT_MONTH') TO ('$LAST_DAY_NEXT_MONTH');"
psql -c "$NEW_PARTITION_COMMAND" "$PGSLICE_URL"

# Mark tables from 3 months ago to 6 months ago as retired if they exist, then detach and dump them to object store
# Borrowing a lot from https://github.com/BCDevOps/backup-container
for i in {3..6}; do
    DATE=$(date -d "$(date +%Y-%m-01) -$i months" +%Y%m)
    PARTITION_TABLE="weather_station_model_predictions_${DATE}"
    DETACH_COMMAND="
    DO \$BODY\$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_catalog.pg_partitions WHERE schemaname = 'public' AND tablename = '${PARTITION_TABLE}') THEN
            EXECUTE 'ALTER TABLE weather_station_model_predictions DETACH PARTITION ${PARTITION_TABLE}';
        END IF;
    END \$BODY\$;"

    echo "Detaching partition: ${PARTITION_TABLE}"
    psql -c "$DETACH_COMMAND" $PGSLICE_URL
    
    echo "Dumping partition: ${PARTITION_TABLE}"
    _datestamp=`date +\%Y/\%m`
    _target_filename="${PG_HOSTNAME}_${PARTITION_TABLE}_retired_${DATE}.sql.gz"
    _target_folder="${PG_HOSTNAME}_${PG_DATABASE}/${_datestamp}"
    pg_dump -c -Fc -t ${PARTITION_TABLE} $PGSLICE_URL | gzip | AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY AWS_SECRET_ACCESS_KEY=$AWS_SECRET_KEY aws --endpoint="https://${AWS_HOSTNAME}" s3 cp - "s3://${AWS_BUCKET}/retired/${_target_folder}/${_target_filename}"
    psql -c "DROP TABLE ${PARTITION_TABLE} IF EXISTS" $PGSLICE_URL
done