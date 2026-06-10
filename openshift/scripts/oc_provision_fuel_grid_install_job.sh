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
#%    [PROJ_TARGET] ${THIS_FILE} [SUFFIX]
#%
#% Examples:
#%
#%   PROJ_TARGET=e1e498-dev ${THIS_FILE} pr-0

PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"
FUEL_GRID_INSTALL_SUSPEND="${FUEL_GRID_INSTALL_SUSPEND:-false}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/fuel_grid_install_job.yaml \
-p NAME=${APP_NAME} \
-p SUFFIX=${SUFFIX} \
-p CRUNCHYDB_USER=${CRUNCHY_NAME}-${SUFFIX}-pguser-${CRUNCHY_NAME}-${SUFFIX} \
-p FUEL_GRID_INSTALL_SUSPEND=${FUEL_GRID_INSTALL_SUSPEND} \
-p PROJECT_NAMESPACE=${PROJ_TARGET}"

# Apply template (apply or use --dry-run)
#
OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run"

# Execute commands
#
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}"
