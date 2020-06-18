#!/bin/bash
set -Eeu
#set -o pipefail

# The script run within the parent folder
cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ..

source test/_functions.sh
check_minishift

#pods="$(oc get pod -l 'statefulset=patroni-001,statefulset.kubernetes.io/pod-name' -o custom-columns=name:.metadata.name --no-headers=true)"

POD_MASTER="$(oc get pod -l 'statefulset=patroni-001,statefulset.kubernetes.io/pod-name,role=master' -o custom-columns=name:.metadata.name --no-headers=true)"

NEW_MAX_CONECTIONS=$(oc get Endpoints/patroni-config -o 'custom-columns=name:.metadata.annotations.config' --no-headers | jq -cM '.postgresql.parameters.max_connections' | awk '{ print $1 + 2}')
echo "NEW_MAX_CONECTIONS=$NEW_MAX_CONECTIONS"
oc get Endpoints/patroni-config -o 'custom-columns=name:.metadata.annotations.config' --no-headers | jq -cM ".postgresql.parameters.max_connections = $NEW_MAX_CONECTIONS" | oc rsh $POD_MASTER patronictl edit-config  --apply - --force --quiet patroni

echo "Reloading patroni configuration ..."
oc rsh $POD_MASTER patronictl reload --role any --force patroni

echo "Waiting for configuration reloaded"
REPLICAS=3
PENDING_RESTART=0
while [ "$PENDING_RESTART" != "$REPLICAS" ]; do
  PENDING_RESTART=$(oc get pod -l 'statefulset=patroni-001,statefulset.kubernetes.io/pod-name,role=master' -o custom-columns=name:.metadata.name --no-headers=true | xargs -I {} oc rsh {} patronictl list -f json | jq -rM '.[] | ."Pending restart"' | grep '*' | wc -l | awk '{print $1}')
  echo "PENDING_RESTART = $PENDING_RESTART"
done

echo "Restarting patroni replicas ..."
oc rsh $POD_MASTER patronictl restart --role replica --force patroni

echo "Waiting for replicas to restart"
PENDING_RESTART=0
while [ "$PENDING_RESTART" != "1" ]; do
  PENDING_RESTART=$(oc get pod -l 'statefulset=patroni-001,statefulset.kubernetes.io/pod-name,role=master' -o custom-columns=name:.metadata.name --no-headers=true | xargs -I {} oc rsh {} patronictl list -f json | jq -rM '.[] | ."Pending restart"' | grep '*' | wc -l | awk '{print $1}')
  echo "PENDING_RESTART = $PENDING_RESTART"
done

echo "Restarting patroni master ..."
oc rsh $POD_MASTER patronictl restart --role master --force patroni

echo "Waiting for master to restart"
PENDING_RESTART=1
while [ "$PENDING_RESTART" != "0" ]; do
  PENDING_RESTART=$(oc get pod -l 'statefulset=patroni-001,statefulset.kubernetes.io/pod-name,role=master' -o custom-columns=name:.metadata.name --no-headers=true | xargs -I {} oc rsh {} patronictl list -f json | jq -rM '.[] | ."Pending restart"' | grep -v 'null' | wc -l | awk '{print $1}')
  echo "PENDING_RESTART = $PENDING_RESTART"
done

#oc get pod -l 'statefulset=patroni-001,statefulset.kubernetes.io/pod-name,role=master' -o custom-columns=name:.metadata.name --no-headers=true | xargs -I {} oc rsh {} patronictl list -f json | jq -r '.[] | ."Pending restart"'

maxConnections=''

while [ "$maxConnections" != "$NEW_MAX_CONECTIONS" ]; do
  sleep 2
  maxConnections=$(oc get pod -l 'statefulset=patroni-001,statefulset.kubernetes.io/pod-name' -o custom-columns=name:.metadata.name --no-headers=true | xargs -I {} oc rsh {} psql -qAtX -c 'SHOW max_connections' | sort | uniq)
  echo "maxConnections=${maxConnections}"
done

echo "${maxConnections}" | wc -l | awk '{ if ( $1 != 1){ print "same  max_connections... FAIL" $1; exit 1;} else { print "same max_connections ... OK"}}'
echo "${maxConnections}" | awk "{ if ( \$1 != $NEW_MAX_CONECTIONS){ print \"max_connections == $NEW_MAX_CONECTIONS? ... FAIL - Found \" \$1; exit 1;} else { print \"max_connections == $NEW_MAX_CONECTIONS? ... OK\"}}"
