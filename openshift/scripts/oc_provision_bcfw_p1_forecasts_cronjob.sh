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

# Use a random time if schedule not specified. (The BCWS server can't handle multiple identical requests at
# the same time, it will throw a duplicate object exception.)
SCHEDULE="${SCHEDULE:-$((31 + $RANDOM % 29)) 8,16 * * *}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/bcfw_p1_forecasts.cronjob.yaml \
-p JOB_NAME=bcfw-p1-forecasts-${NAME_APP}-${SUFFIX} \
-p NAME=${NAME_APP} \
-p SUFFIX=${SUFFIX} \
-p SCHEDULE=\"${SCHEDULE}\" \
-p POSTGRES_USER=${POSTGRES_USER:-${NAME_APP}} \
-p POSTGRES_DATABASE=${POSTGRES_DATABASE:-${NAME_APP}} \
-p POSTGRES_WRITE_HOST=${POSTGRES_WRITE_HOST:-"patroni-${NAME_APP}-${SUFFIX}-leader"} \
${PROJ_TOOLS:+ "-p PROJ_TOOLS=${PROJ_TOOLS}"} \
${IMAGE_REGISTRY:+ "-p IMAGE_REGISTRY=${IMAGE_REGISTRY}"}"

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
