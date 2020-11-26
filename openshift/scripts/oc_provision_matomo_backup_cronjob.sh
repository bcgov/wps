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

# Prepare variables for backups
CONFIG_VOLUME_NAME="${NAME_APP}-${SUFFIX}-config-volume"
JOB_NAME="matomo-backup-${NAME_APP}-${SUFFIX}"
IMAGE_NAMESPACE=${PROJ_TOOLS}
CONFIG_MAP_NAME="matomo-backup-${NAME_APP}-${SUFFIX}-config"

OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/mariadb-backup-cronjob.yaml \
    -p CONFIG_VOLUME_NAME=${CONFIG_VOLUME_NAME} \
    -p JOB_NAME=${JOB_NAME} \
    -p CONFIG_MAP_NAME=${CONFIG_MAP_NAME} \
    -p JOB_PERSISTENT_STORAGE_NAME=${JOB_PERSISTENT_STORAGE_NAME:-"matomo-backup-${NAME_APP}-${SUFFIX}"} \
    -p IMAGE_NAMESPACE=${IMAGE_NAMESPACE} \
    ${TAG_NAME:+ " -p TAG_NAME=${TAG_NAME}"}"

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
