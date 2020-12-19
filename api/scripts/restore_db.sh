#!/bin/bash

# Database restore helper
#
#   Restore database dump and csv with data to local database.
#
# Assumptions:
#
#   - Assumes you are using the users wps and wpsread.
#   - Assumes you already have a database and users in place.
#
# Usage:
#
#   PGPASSWORD=PASSWORD_FOR_WPS_USER ${THIS_FILE}
#
#   Assumes you have openshift command line tools installed and are logged in.
#
# Examples:
#   
#   PGPASSWORD=mywpspassword ./restore_db.sh
#

set -euo pipefail

# Temporarily elevate roles in order to easily do restore:
echo "You may be prompted for your sudo password..."
ALTER="sudo -u postgres psql -U postgres -c \"alter role wps superuser;\""
echo "${ALTER}"
eval "${ALTER}"

# Restore pg dump:
RESTORE="pg_restore -h localhost -d wps -U wps --no-owner --role=wps -c tmp/dump_db.tar"
echo "${RESTORE}"
eval "${RESTORE}"

# Change user rights back (remove superuser):
ALTER="sudo -u postgres psql -U postgres -c \"alter role wps nosuperuser\""
echo "${ALTER}"
eval "${ALTER}"

# Restore table data
COPY="psql -h localhost -d wps -U wps -c \"\copy model_run_grid_subset_predictions FROM 'tmp/model_run_grid_subset_predictions.csv' CSV\""
echo "You may be prompted for the wps password..."
echo "${COPY}"
eval "${COPY}"

# Restore table data
COPY="psql -h localhost -d wps -U wps -c \"\copy weather_station_model_predictions FROM 'tmp/weather_station_model_predictions.csv' CSV\""
echo "${COPY}"
eval "${COPY}"

# Ensure wpsread user has appropriate rights:
# This step assumes you have wpsread user!
# sudo -u postgres psql -U postgres -d wps -c "REASSIGN owned by wpsread to wps; drop owned by wpsread; drop role if exists wpsread; create user wpsread with password 'wps';"
sudo -u postgres psql -U postgres -d wps -c "grant connect on database wps to wpsread; grant usage on schema public to wpsread; grant select on all tables in schema public to wpsread;"

exit 0
