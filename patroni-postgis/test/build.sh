#!/bin/bash
set -Eeu
#set -o pipefail

# The script run within the parent folder
cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ..

source test/_functions.sh
check_minishift

echo "Deleting build objects ..."
# set -x
oc delete all -l app=patroni-001,phase=build --ignore-not-found 2> /dev/null
oc delete ImageStreamTag/postgres:10 --ignore-not-found 2> /dev/null
# { set +x; } 2>/dev/null

echo "Processing build template ..."
# set -x
oc process -f openshift/build.yaml \
  -p "GIT_URI=$(git config --get remote.origin.url)" \
  -p "GIT_REF=$(git rev-parse --abbrev-ref HEAD)" \
  -p SUFFIX=-001 -p VERSION=v10-latest | remove_bc_triggers | oc create -f -
# { set +x; } 2>/dev/null
# wait until source images get pulled
IMAGES_PULLED=0
echo "Pulling source images ...";
while [ $IMAGES_PULLED -eq 0 ]; do
    # set -x
    #oc get ImageStreamTag/postgres:10 -o json | jq ".image.dockerImageLayers[0]" && IMAGES_PULLED=1 || IMAGES_PULLED=0
    oc get ImageStreamTag/postgres:10 -o 'custom-columns=name:.image.metadata.name' > /dev/null 2>/dev/null && IMAGES_PULLED=1 || IMAGES_PULLED=0
    # { set +x; } 2>/dev/null
done
echo "Building ..."
# set -x
# Avoid unecessary commits and build from current git clone/checkout directory.
oc start-build patroni-001 "--from-dir=$(git rev-parse --show-toplevel)" --wait
# { set +x; } 2>/dev/null