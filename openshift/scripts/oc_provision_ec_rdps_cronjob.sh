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

# Specify a default schedule to run every 2 hours, since one run of the cronjob
# can sometimes take over an hour
SCHEDULE="${SCHEDULE:-$((24 + $RANDOM % 35)) */2 * * *}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/env_canada_rdps.cronjob.yaml \
-p JOB_NAME=env-canada-rdps-${NAME_APP}-${SUFFIX} \
-p NAME=${NAME_APP} \
-p SUFFIX=${SUFFIX} \
-p SCHEDULE=\"${SCHEDULE}\" \
-p POSTGRES_USER=${POSTGRES_USER:-${NAME_APP}-${SUFFIX}} \
-p POSTGRES_DATABASE=${POSTGRES_DATABASE:-${NAME_APP}-${SUFFIX}} \
-p POSTGRES_WRITE_HOST=${POSTGRES_WRITE_HOST:-"patroni-${NAME_APP}-${SUFFIX}-leader"} \
-p POSTGRES_READ_HOST=${POSTGRES_READ_HOST:-"patroni-${NAME_APP}-${SUFFIX}-replica"} \
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
