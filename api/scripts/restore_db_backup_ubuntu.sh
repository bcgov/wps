#!/bin/bash

# Database backup restore helper
#
#   Restore database backup (made by the backup container).
#   This script works on Ubuntu.
#   TODO: Ideally we should have the same script for Ubuntu and for MacOS.
#
# Examples:
#   
#   FILENAME=some_backup.sql.gz ./restore_db_backup.sh
#

# drop existing DB, and re-create it
echo "You may be prompted for your sudo password now..."
sudo -u postgres psql -U postgres -c "alter role wps superuser;" -c "drop database wps;" -c "create database wps with owner wps;" 

echo "You may be prompted for the wps database user password now..."
gunzip -c "${FILENAME}" | psql -v ON_ERROR_STOP=1 -x -h localhost -U wps -d wps

sudo -u postgres psql -U postgres -c "alter role wps nosuperuser;"

sudo -u postgres psql -U postgres -d wps -c "create user wpsread with password 'wps';"
sudo -u postgres psql -U postgres -d wps -c "grant connect on database wps to wpsread; grant usage on schema public to wpsread; grant select on all tables in schema public to wpsread;"
