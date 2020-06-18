#!/bin/bash
set -Eeu
#set -o pipefail

function clean_all {
  oc delete all -l app=patroni-001 2> /dev/null
  oc delete all -l 'cluster-name=patroni,app.kubernetes.io/name=patroni' 2> /dev/null
  oc delete pvc,secret,configmap,rolebinding,role,ServiceAccount,Endpoints -l app=patroni-001 2> /dev/null
  oc delete pvc,secret,configmap,rolebinding,role,ServiceAccount,Endpoints -l 'cluster-name=patroni,app.kubernetes.io/name=patroni' 2> /dev/null
}

function remove_bc_triggers {
  jq 'del( .items[] | select (.kind == "BuildConfig") | .spec.triggers )'
}

function check_minishift {
  oc config current-context | grep -q "$(minishift ip)"
}