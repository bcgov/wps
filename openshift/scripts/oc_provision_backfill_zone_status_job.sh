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
#%    [PROJ_TARGET] [PG_DATABASE] [TABLE] ${THIS_FILE} [SUFFIX]
#%
#% Examples:
#%
#%   PROJ_TARGET=e1e498-dev PG_DATABASE=wps TABLE=table ${THIS_FILE} pr-0

PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/backfill_zone_status_job.yaml \
-p NAME=${APP_NAME} \
-p SUFFIX=${SUFFIX} \
-p CRUNCHYDB_USER=${CRUNCHY_NAME}-${SUFFIX}-pguser-${CRUNCHY_NAME}-${SUFFIX}"

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
