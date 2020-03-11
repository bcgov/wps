#!/bin/bash
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Cleanup Helper
#%
#%   Intended for use with a pull request-based pipeline.
#%
#% Usage:
#%
#%   ${THIS_FILE} [PR_NUMBER] [apply]
#%
#% Examples:
#%
#%   Provide a PR number. Default only returns object names.
#%   ${THIS_FILE} 0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} 0 apply
#%

# Set and process commands
#
APP_LABEL="${NAME}-pr-${PR_NO}"
if [ "${APPLY}" ]; then
	# Delete everything with the specified label
	OC_CLEAN_DEPLOY="oc -n ${PROJ_DEV} delete all -o name -l app=${APP_LABEL}"
	OC_CLEAN_TOOLS="oc -n ${PROJ_TOOLS} delete all -o name -l app=${APP_LABEL}"
else
	# List everything with the specified label
	OC_CLEAN_DEPLOY="oc -n ${PROJ_DEV} get all -o name -l app=${APP_LABEL}"
	OC_CLEAN_TOOLS="oc -n ${PROJ_TOOLS} get all -o name -l app=${APP_LABEL}"
fi

# Execute commands
#
echo -e "\n${PROJ_DEV}:"
eval "${OC_CLEAN_DEPLOY}"
echo -e "\n${PROJ_TOOLS}:"
eval "${OC_CLEAN_TOOLS}"

# Provide oc command instruction
#
display_helper "${OC_CLEAN_DEPLOY}" "${OC_CLEAN_TOOLS}"