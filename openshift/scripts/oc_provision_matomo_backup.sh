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
NAME="${NAME_APP}-${SUFFIX}"
IMAGE_NAMESPACE=${PROJ_TOOLS}
CONFIG_MAP_NAME="matomo-backup-${NAME_APP}-${SUFFIX}-config"
VERIFICATION_VOLUME_NAME="matomo-backup-verification-${NAME_APP}-${SUFFIX}"

OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/mariadb-backup.dc.json \
    -p NAME=${NAME} \
    -p IMAGE_NAMESPACE=${IMAGE_NAMESPACE} \
    -p CONFIG_MAP_NAME=${CONFIG_MAP_NAME} \
    -p VERIFICATION_VOLUME_NAME=${VERIFICATION_VOLUME_NAME} \
    ${TAG_NAME:+ " -p TAG_NAME=${TAG_NAME}"} \
    -p BACKUP_VOLUME_NAME=${BACKUP_VOLUME_NAME:-"matomo-backup-${NAME_APP}-${SUFFIX}"}"

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
