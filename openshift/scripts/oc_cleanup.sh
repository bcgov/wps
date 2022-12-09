#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Cleanup Helper
#%
#%   Intended for use with a pull request-based pipeline.
#%   Suffixes incl.: pr-###, test and prod.
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
APP_LABEL="${APP_NAME}-${SUFFIX}"

# Delete (apply) or get (not apply) items matching the a label
#
if [ "${APPLY}" ]; then
	DELETE_OR_GET="delete"
else
	DELETE_OR_GET="get"
fi
OC_CLEAN_DEPLOY="oc -n ${PROJ_TARGET} ${DELETE_OR_GET} all,cm,pvc -o name -l app=${APP_LABEL}"
OC_CLEAN_TILESERV="oc -n ${PROJ_TARGET} ${DELETE_OR_GET} all,cm,pvc,PostgresCluster -o name -l app=wps-tileserv-${SUFFIX}"

# Execute commands
#
echo -e "\n${PROJ_TARGET}:"
eval "${OC_CLEAN_DEPLOY}"
eval "${OC_CLEAN_TILESERV}"

# Provide oc command instruction
#
display_helper "${OC_CLEAN_DEPLOY}"
