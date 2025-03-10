#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Cleanup Helper
#%
#%   Intended for use with a pull request-based pipeline.
#%   Suffixes incl.: pr-###
#%
#% Usage:
#%
#%   ${THIS_FILE} [SUFFIX] [apply]
#%
#% Examples:
#%
#%   Provide a PR number. Default only returns object names.
#%   ${THIS_FILE} pr-0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} pr-0 apply
#%

# Delete (apply) or get (not apply) items matching the a label
#
if [ "${APPLY}" ]; then
	DELETE_OR_GET="delete"
else
	DELETE_OR_GET="get"
fi

# Target project override for Dev, Test, or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

APPLICATION_NAME="patroni-${APP_NAME}-${SUFFIX}"

OC_CLEAN_DEPLOY="oc -n ${PROJ_TARGET} ${DELETE_OR_GET} \
    all,cm,secret,endpoints,serviceaccounts,rolebinding.rbac.authorization.k8s.io,roles.rbac.authorization.k8s.io,pvc \
    -o name -l app=${APPLICATION_NAME} -l cluster-name=${APPLICATION_NAME}"

OC_CLEAN_CRUNCHY="oc -n ${PROJ_TARGET} ${DELETE_OR_GET} \
    PostgresCluster \
    -o name -l app=${CRUNCHY_NAME}-${SUFFIX}"

OC_CLEAN_CONFIGMAPS="oc -n ${PROJ_TARGET} ${DELETE_OR_GET} \
    configmaps \
    -o name -l cluster-name=${APPLICATION_NAME}"

OC_CLEAN_PATRONI_NETWORK_POLICY="oc -n ${PROJ_TARGET} ${DELETE_OR_GET} networkpolicy patroni-db-to-db-patroni-${APP_NAME}-${SUFFIX} --ignore-not-found=true" 

# Execute commands
#
echo -e "\n${PROJ_TARGET}:"
eval "${OC_CLEAN_DEPLOY}"
eval "${OC_CLEAN_CRUNCHY}"
eval "${OC_CLEAN_CONFIGMAPS}"
eval "${OC_CLEAN_PATRONI_NETWORK_POLICY}"

# Provide oc command instruction
#
display_helper "${OC_CLEAN_DEPLOY}" "${OC_CLEAN_CRUNCHY}" "${OC_CLEAN_CONFIGMAPS}" "${OC_CLEAN_PATRONI_NETWORK_POLICY}"