#!/bin/sh -l
#
# Script based on instruction found in readme of
# https://github.com/bcgov/nr-showcase-devops-tools/tree/master/tools/metabase

# TODO: copy metabase.np.yaml file from source and save into our repo
export BASE_URL="https://raw.githubusercontent.com/bcgov/nr-showcase-devops-tools/master/tools/metabase/openshift"
# TODO: parameterize namespace & ns_prefix & ns_env
export NAMESPACE=e1e498-prod
export NS_PREFIX=e1e498
export NS_ENV=dev

oc process -n $NAMESPACE -f $BASE_URL/metabase.np.yaml -p NS_PREFIX=$NS_PREFIX -p NS_ENV=$NS_ENV -o yaml | oc apply -n $NAMESPACE -f -