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

# Delete (apply) or get (not apply) items matching the a label
#
if [ "${APPLY}" ]; then
	DELETE_OR_GET="delete"
else
	DELETE_OR_GET="get"
fi
OC_CLEAN_DEPLOY="oc -n ${PROJ_DEV} ${DELETE_OR_GET} all,cm -o name -l app=${NAME_OBJ}"
OC_CLEAN_TOOLS="oc -n ${PROJ_TOOLS} ${DELETE_OR_GET} all,cm -o name -l app=${NAME_OBJ}"

# Execute commands
#
echo -e "\n${PROJ_DEV}:"
eval "${OC_CLEAN_DEPLOY}"
echo -e "\n${PROJ_TOOLS}:"
eval "${OC_CLEAN_TOOLS}"

# Provide oc command instruction
#
display_helper "${OC_CLEAN_DEPLOY}" "${OC_CLEAN_TOOLS}"
