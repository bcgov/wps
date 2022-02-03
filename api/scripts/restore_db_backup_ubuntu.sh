#!/bin/bash
echo "You maybe be promted for your sudo password now..."
sudo -u postgres psql -U postgres -c "alter role wps superuser;" -c "drop database wps;" -c "create database wps with owner wps;" 

echo "You may be promted for the wps database user password now..."
# pg_restore -h localhost -d wps -U wps --no-owner --role=wps -c tmp/dump_db.tar
gunzip -c "${FILENAME}" | psql -v ON_ERROR_STOP=1 -x -h localhost -U wps -d wps

sudo -u postgres psql -U postgres -c "alter role wps nosuperuser;"

sudo -u postgres psql -U postgres -d wps -c "create user wpsread with password 'wps';"
sudo -u postgres psql -U postgres -d wps -c "grant connect on database wps to wpsread; grant usage on schema public to wpsread; grant select on all tables in schema public to wpsread;"
