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

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/c_haines.cronjob.yaml \
-p JOB_NAME=${NAME_APP}-c-haines-${SUFFIX} \
-p NAME=${NAME_APP}-c-haines \
-p IMAGE_NAME=${NAME_APP}-${SUFFIX} \
-p IMAGE_TAG=${SUFFIX} \
-p SUFFIX=${SUFFIX} \
-p POSTGRES_USER=wps \
-p POSTGRES_DATABASE=wps \
-p POSTGRES_WRITE_HOST=patroni-wps-${SUFFIX}-leader \
-p POSTGRES_READ_HOST=patroni-wps-${SUFFIX}-replica \
${PROJ_TOOLS:+ "-p PROJ_TOOLS=${PROJ_TOOLS}"}"

# Apply template (apply or use --dry-run)
#
OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run=client"

# Execute commands
#
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}"
