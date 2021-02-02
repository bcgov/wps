#!/usr/bin/env bash
set -Eeu
set -o pipefail

# The bcdevops version has a check for 90% disk usage here:
# ----
# check for disk space. Fails if usage hits above 90%
# df "${PATRONI_POSTGRESQL_DATA_DIR:-/home/postgres/pgdata}" --output=pcent | tail -n 1 | awk '{if ($1+0 > 90) exit 1; else exit 0;}'
# ----
# We've currently got a seperate script (disk_space_check.sh) that is called
# as a livenessProbe, and will generate warnings if the available disk space
# falls below a predefined size.

# patronictl list outputs status for each of the pods in the Patroni cluster, but we are only interested in
# the information for the individual pod that is currently running this script (identified by Openshift $(hostname))
# if the pod is the Leader, there is no Lag. If the pod is a Replica, there will be a "Lag in MB" attribute
# It's ok for there to be a little lag every now and then - if something is writing to the Leader a lot,
# we may have a little lag while the Replicas catch up.
# If there's a lot of lag, it probably means we have a big problem.
pg_isready -q && patronictl list --format=json | jq -e ".[] | select(.Member == \"$(hostname)\" and .State == \"running\" and (.Role == \"Leader\" or .\"Lag in MB\" < 10))?"
