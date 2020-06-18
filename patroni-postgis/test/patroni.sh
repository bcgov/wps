#!/bin/bash
set -Eeu
#set -o pipefail

# The script run within the parent folder
cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ..

source test/_functions.sh
check_minishift

pods=$(oc get pod -l 'statefulset=patroni-001,statefulset.kubernetes.io/pod-name' -o custom-columns=name:.metadata.name --no-headers=true)

leaders=$(echo "$pods" \
| xargs -I {} oc rsh {} patronictl list -f json | jq -er '.[] | select(.Role == "Leader") | .Member')


echo "${leaders}" | sort | uniq | wc -l | awk '{ if ( $1 != 1){ print "1 leader check ... FAIL" $1; exit 1;} else { print "1 leader check ... OK"}}'

lagInMB=$(echo "$pods" \
| xargs -I {} oc rsh {} patronictl list -f json | jq -er '.[] | ."Lag in MB"' | sort | uniq)


echo "${lagInMB}" | wc -l | awk '{ if ( $1 != 1){ print "same lag check ... FAIL" $1; exit 1;} else { print "same lag check ... OK"}}'
echo "${lagInMB}" | awk '{ if ( $1 != 0){ print "lag == 0? ... FAIL - Found " $1; exit 1;} else { print "lag == 0? ... OK"}}'
