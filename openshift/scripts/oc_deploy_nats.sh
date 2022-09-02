#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Deploy Helper
#%
#%   Intended for use through cli, a pull request-based pipeline will be added later.
#%
#% Usage:
#%
#%     ${THIS_FILE} [SUFFIX] [apply]
#%
#% Examples:
#%
#%   Provide the service name. This is a dry run.
#%   ${THIS_FILE} nats

# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"
OBJ_NAME="${APP_NAME}-${SUFFIX}"

# Process a template (mostly variable substitution)
#
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${PATH_NATS} \
 -p SUFFIX=${SUFFIX} \
 -p APP_NAME=${APP_NAME}"

# Apply a template (apply or use --dry-run=client)
#
OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run=client"

# Execute commands
#
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"

display_helper "${OC_PROCESS} | ${OC_APPLY}" 
