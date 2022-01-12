#!/bin/sh -l
#
# Script based on instruction found in readme of
# https://github.com/bcgov/nr-showcase-devops-tools/tree/master/tools/metabase

# TODO: copy metabase.secret.yaml and metabase.dc.yaml files from github repo into ours
export BASE_URL="https://raw.githubusercontent.com/bcgov/nr-showcase-devops-tools/master/tools/metabase/openshift"
export ADMIN_EMAIL=BCWS.predictiveservices@gov.bc.ca
# TODO: parameterize namespace
export NAMESPACE=e1e498-dev
# TODO: parameterize prefix
export PREFIX="prod-"

oc process -n $NAMESPACE -f $BASE_URL/metabase.secret.yaml -p ADMIN_EMAIL=$ADMIN_EMAIL -o yaml | oc create -n $NAMESPACE -f -

oc process -n $NAMESPACE -f $BASE_URL/metabase.dc.yaml -p NAMESPACE=$NAMESPACE -p PREFIX=$PREFIX -o yaml | oc apply -n $NAMESPACE -f -