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
 
# Prepare names for patroni ephemeral instance for this PR.
IMAGE_STREAM_NAMESPACE=${IMAGE_STREAM_NAMESPACE:-${PROJ_TOOLS}}
EPHEMERAL_STORAGE=${EPHEMERAL_STORAGE:-'False'}

# Process pre-requisite template
OC_PROCESS_PREREQUISITE="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/patroni_prerequisite.yaml \
-p NAME=\"patroni-${APP_NAME}-${SUFFIX}\" \
-p PARENT_NAME=\"${APP_NAME}\" \
-p TARGET_NAMESPACE=${PROJ_TARGET} \
-p IMAGE_STREAM_NAMESPACE=${IMAGE_STREAM_NAMESPACE} \
 ${IMAGE_NAME:+ " -p IMAGE_NAME=${IMAGE_NAME}"} \
 ${IMAGE_TAG:+ " -p IMAGE_TAG=${IMAGE_TAG}"} \
 ${IMAGE_REGISTRY:+ " -p IMAGE_REGISTRY=${IMAGE_REGISTRY}"} \
 ${PVC_SIZE:+ " -p PVC_SIZE=${PVC_SIZE}"} \
 ${CPU_REQUEST:+ "-p CPU_REQUEST=${CPU_REQUEST}"} \
 ${MEMORY_REQUEST:+ "-p MEMORY_REQUEST=${MEMORY_REQUEST}"} \
 ${MEMORY_LIMIT:+ "-p MEMORY_LIMIT=${MEMORY_LIMIT}"}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/patroni.yaml \
-p NAME=\"patroni-${APP_NAME}-${SUFFIX}\" \
-p APP_USER=\"${APP_NAME}\" \
-p PARENT_NAME=\"${APP_NAME}\" \
-p TARGET_NAMESPACE=${PROJ_TARGET} \
-p IMAGE_STREAM_NAMESPACE=${IMAGE_STREAM_NAMESPACE} \
 ${IMAGE_NAME:+ " -p IMAGE_NAME=${IMAGE_NAME}"} \
 ${IMAGE_TAG:+ " -p IMAGE_TAG=${IMAGE_TAG}"} \
 ${IMAGE_REGISTRY:+ " -p IMAGE_REGISTRY=${IMAGE_REGISTRY}"} \
 ${PVC_SIZE:+ " -p PVC_SIZE=${PVC_SIZE}"} \
 ${CPU_REQUEST:+ "-p CPU_REQUEST=${CPU_REQUEST}"} \
 ${MEMORY_REQUEST:+ "-p MEMORY_REQUEST=${MEMORY_REQUEST}"} \
 ${MEMORY_LIMIT:+ "-p MEMORY_LIMIT=${MEMORY_LIMIT}"}"


# In order to avoid running out of storage quote in our development environment, use
# ephemeral storage by removing the pvc request from the template.
if [ "$EPHEMERAL_STORAGE" = "True" ]
then
    # Pipe the template to jq, and delete the pvc and volume claim items from the template.
    OC_PROCESS="${OC_PROCESS} | jq 'del(.items[2].spec.template.spec.volumes[0].persistentVolumeClaim) \
| del(.items[2].spec.volumeClaimTemplates)'"
fi

# Apply template (apply or use --dry-run)
#
OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run=client"

# Execute commands
#
eval "${OC_PROCESS_PREREQUISITE}"
eval "${OC_PROCESS_PREREQUISITE} | ${OC_APPLY}"

eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"

# Provide oc command instruction
#
display_helper "${OC_PROCESS_PREREQUISITE} | ${OC_APPLY}"
display_helper "${OC_PROCESS} | ${OC_APPLY}"
