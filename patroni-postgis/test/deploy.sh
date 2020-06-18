#!/bin/bash
set -Eeu
#set -o pipefail

# The script run within the parent folder
cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ..

source test/_functions.sh
check_minishift

echo "Deleting deploy objects ..."
# set -x
oc delete all -l app=patroni-001,phase=deploy --ignore-not-found 2> /dev/null
oc delete pvc,secret,configmap,rolebinding,role -l app=patroni-001 2> /dev/null
# { set +x; } 2>/dev/null

echo "Processing deployment templates ..."
# set -x
oc process -f openshift/deployment-prereq.yaml \
    -p SUFFIX=-001 -l app=patroni-001 | oc apply -f -

oc process -f openshift/deployment.yaml \
    -p "IMAGE_STREAM_NAMESPACE=$(oc project -q)" \
    -p "IMAGE_STREAM_TAG=patroni:v10-latest" \
    -p SUFFIX=-001 -l app=patroni-001 | oc apply -f -


DEPLOYED=0
echo "Deploying ...";
while [ $DEPLOYED -eq 0 ]; do
    # set -x
    sleep 5
    oc get StatefulSet/patroni-001 --no-headers -o custom-columns=DESIRED:.spec.replicas,CURRENT:.status.currentReplicas,READY:.status.readyReplicas | awk '{if ($1 == $2 && $2 == $3 ) print $0; else { print $0; exit 9;} }' && DEPLOYED=1
    # { set +x; } 2>/dev/null
done

./test/patroni.sh
./test/psql.sh
