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
NAME="backup-postgres-${NAME_APP}-${SUFFIX}"
VERIFICATION_VOLUME_NAME="backup-verification-postgres-${NAME_APP}-${SUFFIX}"
CLUSTER_NAME="patroni-${NAME_APP}-${SUFFIX}"
IMAGE_NAMESPACE=${PROJ_TOOLS}
EPHEMERAL_STORAGE=${EPHEMERAL_STORAGE:-'False'}
# /-/_ : replace dash with underscore
# ^^ to uppercase
WPS_ENVIRONMENT_USERNAME_KEY="PATRONI_${NAME_APP}_${SUFFIX/-/_}_LEADER_USER"
WPS_ENVIRONMENT_USERNAME_KEY=${WPS_ENVIRONMENT_USERNAME_KEY^^}
WPS_ENVIRONMENT_PASSWORD_KEY="PATRONI_${NAME_APP}_${SUFFIX/-/_}_LEADER_PASSWORD"
WPS_ENVIRONMENT_PASSWORD_KEY=${WPS_ENVIRONMENT_PASSWORD_KEY^^}

OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/backup-postgres.dc.yaml \
    -p NAME=${NAME} \
    -p BACKUP_VOLUME_NAME=${NAME} \
    -p VERIFICATION_VOLUME_NAME=${VERIFICATION_VOLUME_NAME} \
    -p IMAGE_NAMESPACE=${IMAGE_NAMESPACE} \
    -p CLUSTER_NAME=${CLUSTER_NAME} \
    -p WPS_ENVIRONMENT_USERNAME_KEY=${WPS_ENVIRONMENT_USERNAME_KEY} \
    -p WPS_ENVIRONMENT_PASSWORD_KEY=${WPS_ENVIRONMENT_PASSWORD_KEY} \
    ${BACKUP_VOLUME_SIZE:+ " -p BACKUP_VOLUME_SIZE=${BACKUP_VOLUME_SIZE}"} \
    ${BACKUP_VOLUME_CLASS:+ " -p BACKUP_VOLUME_CLASS=${BACKUP_VOLUME_CLASS}"}"

# In order to avoid running out of storage quote in our development environment, use
# ephemeral storage by removing the pvc request from the template.
if [ "$EPHEMERAL_STORAGE" = "True" ]
then
    # Pipe the template to jq, and delete the pvc and volume claim items from the template.
    OC_PROCESS="${OC_PROCESS} | jq 'del(.items[0]) \
| del(.items[1].spec.template.spec.volumes[0].persistentVolumeClaim)'"
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
