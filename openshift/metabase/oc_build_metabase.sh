#!/bin/sh -l
#
# Script based on instruction found in readme of
# https://github.com/bcgov/nr-showcase-devops-tools/tree/master/tools/metabase

export BASE_URL="https://raw.githubusercontent.com/bcgov/nr-showcase-devops-tools/master/tools/metabase/openshift"
export NAMESPACE="e1e498-dev"
export METABASE_VERSION=v0.41.5

oc process -n $NAMESPACE -f $BASE_URL/metabase.bc.yaml -p METABASE_VERSION=$METABASE_VERSION -o yaml | oc apply -n $NAMESPACE -f -