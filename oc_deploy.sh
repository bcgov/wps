#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Deploy Helper
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
#%   Provide a PR number. Defaults to a dry-run.
#%   ${THIS_FILE} pr-0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} pr-0 apply
#%

# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

# Process a template (mostly variable substition)
#
OC_PROCESS="oc -n ${PROJ_TOOLS} process -f ${PATH_DC} -p NAME=${NAME_APP} -p SUFFIX=${SUFFIX}"

# Apply a template (apply or use --dry-run)
#
OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run"

# Deploy and follow the progress
# 
OC_DEPLOY="oc -n ${PROJ_TARGET} rollout latest dc/${NAME_OBJ}"
OC_LOG="oc -n ${PROJ_TARGET} logs -f dc/${NAME_OBJ}"
if [ ! "${APPLY}" ]; then
  OC_DEPLOY="${OC_DEPLOY} --dry-run"
  OC_LOG=""
fi

# Execute commands
#
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"
eval "${OC_DEPLOY}"
eval "${OC_LOG}"

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}" "${OC_DEPLOY}" "${OC_LOG}"
