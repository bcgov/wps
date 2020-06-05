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
#%   [CPU_REQUEST=<>] [CPU_LIMIT=<>] [MEMORY_REQUEST=<>] [MEMORY_LIMIT=<>] [REPLICAS=<>] \
#%     ${THIS_FILE} [SUFFIX] [apply]
#%
#% Examples:
#%
#%   Provide a PR number. Defaults to a dry-run.
#%   ${THIS_FILE} pr-0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} pr-0 apply
#%
#%   Override default CPU_REQUEST to 2000 millicores
#%   CPU_REQUEST=2000m ${THIS_FILE} pr-0

# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

# Process a template (mostly variable substition)
#
OC_PROCESS="oc -n ${PROJ_TOOLS} process -f ${PATH_DC} \
 -p NAME=${NAME_APP} \
 -p SUFFIX=${SUFFIX} \
 ${CPU_REQUEST:+ "-p CPU_REQUEST=${CPU_REQUEST}"} \
 ${CPU_LIMIT:+ "-p CPU_LIMIT=${CPU_LIMIT}"} \
 ${MEMORY_REQUEST:+ "-p MEMORY_REQUEST=${MEMORY_REQUEST}"} \
 ${MEMORY_LIMIT:+ "-p MEMORY_LIMIT=${MEMORY_LIMIT}"} \
 ${REPLICAS:+ "-p REPLICAS=${REPLICAS}"}"

# Apply a template (apply or use --dry-run)
#
OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run"

# Deploy and follow the progress
#
OC_DEPLOY="oc -n ${PROJ_TARGET} rollout latest dc/${NAME_OBJ}"
OC_LOG="oc -n ${PROJ_TARGET} logs -f --pod-running-timeout=1m dc/${NAME_OBJ}"
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
