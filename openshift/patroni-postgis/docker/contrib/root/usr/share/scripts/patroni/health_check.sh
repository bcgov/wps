#!/usr/bin/env bash
set -Eeu
set -o pipefail

# patronictl list outputs status for each of the pods in the Patroni cluster, but we are only interested in
# the information for the individual pod that is currently running this script (identified by Openshift $(hostname))
# if the pod is the Leader, there is no Lag. If the pod is a Replica, there will be a "Lag in MB" attribute
# It's ok for there to be a little lag every now and then - if something is writing to the Leader a lot,
# we may have a little lag while the Replicas catch up.
# If there's a lot of lag, it probably means we have a big problem.
pg_isready -q && patronictl list --format=json | jq -e ".[] | select(.Member == \"$(hostname)\" and .State == \"running\" and (.Role == \"Leader\" or .\"Lag in MB\" < 10))?"
