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
OC_CLEAN_DEPLOY="oc -n ${PROJ_TEST} ${DELETE_OR_GET} all,cm -o name -l app=${NAME_OBJ}"
OC_CLEAN_EC_RDPS_CRONJOB="oc -n ${PROJ_TEST} ${DELETE_OR_GET} --ignore-not-found=true cronjob/env-canada-rdps-${NAME_APP}-${SUFFIX}"
OC_DELETE_EC_PODS="oc -n ${PROJ_TEST} get pods -o name | { grep -E 'env-canada-(gdps|rdps|hrdps)-${NAME_APP}-${SUFFIX}' || test \$? = 1; } | { xargs -r oc ${DELETE_OR_GET} || test \$? = 1; } | cat"

# Execute commands
#
echo -e "\n${PROJ_TEST}:"
eval "${OC_CLEAN_EC_RDPS_CRONJOB}"
eval "${OC_DELETE_EC_PODS}"
eval "${OC_CLEAN_DEPLOY}"

# Provide oc command instruction
#
display_helper "${OC_CLEAN_DEPLOY}" "${OC_CLEAN_EC_RDPS_CRONJOB}" "${OC_DELETE_EC_PODS}"
