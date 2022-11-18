#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Deploy Helper
#%
#%   Intended for use with a pull request-based pipeline.
#%   Suffixes incl.: pr-###.
#%
#% Usage:
#%
#%    ${THIS_FILE} [SUFFIX] [apply]
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
OBJ_NAME="tileserv-${SUFFIX}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/tileserv/tileserv.yaml \
-p SUFFIX=${SUFFIX}"

# Apply template (apply or use --dry-run)
#
OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run=client"

# Cancel all previous deployments
#
OC_CANCEL_ALL_PREV_DEPLOY="oc -n ${PROJ_TARGET} rollout cancel dc/${OBJ_NAME} || true"

# Deploy and follow the progress
#
OC_DEPLOY="oc -n ${PROJ_TARGET} rollout latest dc/${OBJ_NAME}"
OC_LOG="oc -n ${PROJ_TARGET} logs -f --pod-running-timeout=2m dc/${OBJ_NAME}"
if [ ! "${APPLY}" ]; then
  OC_CANCEL_ALL_PREV_DEPLOY=""
  OC_DEPLOY="${OC_DEPLOY} --dry-run=client || true" # in case there is no previous rollout
  OC_LOG=""
fi

# Execute commands
#
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"

# if [ "${APPLY}" ]; then
#   echo "canceling previous deployments..."
#   count=1
#   timeout=10
#   # Check previous deployment statuses before moving onto new deploying
#   while [ $count -le $timeout ]; do
#     sleep 1
#     PENDINGS="$(oc -n ${PROJ_TARGET} rollout history dc/${OBJ_NAME} | awk '{print $2}' | grep -c Pending || true)"
#     RUNNINGS="$(oc -n ${PROJ_TARGET} rollout history dc/${OBJ_NAME} | awk '{print $2}' | grep -c Running || true)"
#     if [ "${PENDINGS}" == 0 ] && [ "${RUNNINGS}" == 0 ]; then
#       # No pending or running replica controllers so exit the while loop
#       break 2
#     fi
#     eval "${OC_CANCEL_ALL_PREV_DEPLOY}"
#     count=$(( $count + 1 ))
#   done
#   if [ $count -gt $timeout ]; then
#     echo "\n*** timeout for canceling deployment ***\n"
#     exit 1
#   fi
# fi

eval "${OC_DEPLOY}"
eval "${OC_LOG}"


# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}"
