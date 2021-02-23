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
CONFIG_MAP_NAME="backup-mariadb-${NAME_APP}-${SUFFIX}-conf"
CONFIG_VOLUME_NAME="backup-mariadb-${NAME_APP}-${SUFFIX}-config-volume"
JOB_NAME="backup-mariadb-${NAME_APP}-${SUFFIX}"
IMAGE_NAMESPACE=${PROJ_TOOLS}
EPHEMERAL_STORAGE=${EPHEMERAL_STORAGE:-'False'}

OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/backup-mariadb-cronjob.yaml \
    -p CONFIG_VOLUME_NAME=${CONFIG_VOLUME_NAME} \
    -p CONFIG_MAP_NAME=${CONFIG_MAP_NAME} \
    -p DATABASE_SERVICE_NAME=patroni-${NAME_APP}-${SUFFIX}-leader \
    -p DATABASE_DEPLOYMENT_NAME=wps-global \
    -p JOB_NAME=${JOB_NAME} \
    -p JOB_PERSISTENT_STORAGE_NAME=${JOB_NAME} \
    -p IMAGE_NAMESPACE=${IMAGE_NAMESPACE} \
    ${JOB_PERSISTENT_STORAGE_NAME:+ " -p JOB_PERSISTENT_STORAGE_NAME=${JOB_PERSISTENT_STORAGE_NAME}"} \
    ${SCHEDULE:+ " -p SCHEDULE=\"${SCHEDULE}\""} \
    ${TAG_NAME:+ " -p TAG_NAME=${TAG_NAME}"}"

# In order to avoid running out of storage quote in our development environment, use
# ephemeral storage by removing the pvc request from the template.
if [ "$EPHEMERAL_STORAGE" = "True" ]
then
    # Pipe the template to jq, and delete the pvc and volume claim items from the template.
    OC_PROCESS="${OC_PROCESS} | jq 'del(.items[0].spec.jobTemplate.spec.template.spec.volumes[0].persistentVolumeClaim)'"
fi

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
