#!/bin/bash
set -Eeu
#set -o pipefail

# The script run within the parent folder
cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ..

source test/_functions.sh
check_minishift

maxConnections=$(oc get pod -l 'statefulset=patroni-001,statefulset.kubernetes.io/pod-name' -o custom-columns=name:.metadata.name --no-headers=true \
| xargs -I {} oc rsh {} psql -qAtX -c 'SHOW max_connections' | sort | uniq)

echo "${maxConnections}" | wc -l | awk '{ if ( $1 != 1){ print "same  max_connections... FAIL" $1; exit 1;} else { print "same max_connections ... OK"}}'
echo "${maxConnections}" | awk '{ if ( $1 != 100){ print "max_connections == 100? ... FAIL - Found " $1; exit 1;} else { print "max_connections == 100? ... OK"}}'
