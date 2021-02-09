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
# PATRONI_CLUSTER_NAME="patroni-${NAME_APP}-${SUFFIX}"
# APPLICATION_NAME="patroni-${NAME_APP}-${SUFFIX}"
# PATRONI_LEADER_SERVICE_NAME="patroni-leader-${NAME_APP}-${SUFFIX}"
# PATRONI_REPLICA_SERVICE_NAME="patroni-replica-${NAME_APP}-${SUFFIX}"
# SERVICE_ACCOUNT="patroniocp-${NAME_APP}-${SUFFIX}"
IMAGE_STREAM_NAMESPACE=${IMAGE_STREAM_NAMESPACE:-${PROJ_TOOLS}}
EPHEMERAL_STORAGE=${EPHEMERAL_STORAGE:-'False'}
TEMPLATE=${TEMPLATE:-'patroni.yaml'}

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/${TEMPLATE} \
-p NAME=\"patroni-${NAME_APP}-${SUFFIX}\" \
-p PARENT_NAME=\"${NAME_APP}\" \
-p TARGET_NAMESPACE=${PROJ_TARGET} \
-p IMAGE_STREAM_NAMESPACE=${IMAGE_STREAM_NAMESPACE} \
 ${IMAGE_NAME:+ " -p IMAGE_NAME=${IMAGE_NAME}"} \
 ${IMAGE_TAG:+ " -p IMAGE_TAG=${IMAGE_TAG}"} \
 ${IMAGE_REGISTRY:+ " -p IMAGE_REGISTRY=${IMAGE_REGISTRY}"} \
 ${PVC_SIZE:+ " -p PVC_SIZE=${PVC_SIZE}"} \
 ${CPU_REQUEST:+ "-p CPU_REQUEST=${CPU_REQUEST}"} \
 ${CPU_LIMIT:+ "-p CPU_LIMIT=${CPU_LIMIT}"} \
 ${MEMORY_REQUEST:+ "-p MEMORY_REQUEST=${MEMORY_REQUEST}"} \
 ${MEMORY_LIMIT:+ "-p MEMORY_LIMIT=${MEMORY_LIMIT}"}"


# OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/patroni.yaml \
# -p NAME=${NAME_APP} \
# -p SUFFIX=${SUFFIX} \
# -p PATRONI_CLUSTER_NAME=${PATRONI_CLUSTER_NAME} \
# -p APPLICATION_NAME=${APPLICATION_NAME} \
# -p PATRONI_LEADER_SERVICE_NAME=${PATRONI_LEADER_SERVICE_NAME} \
# -p PATRONI_REPLICA_SERVICE_NAME=${PATRONI_REPLICA_SERVICE_NAME} \
# -p SERVICE_ACCOUNT=${SERVICE_ACCOUNT} \
# -p IMAGE_NAMESPACE=${IMAGE_NAMESPACE} \
# -p TARGET_NAMESPACE=${PROJ_TARGET} \
#  ${IMAGE_SERVER:+ " -p IMAGE_SERVER=${IMAGE_SERVER}"} \
#  ${IMAGE_VERSION:+ " -p IMAGE_VERSION=${IMAGE_VERSION}"} \
#  ${POD_MANAGEMENT_POLICY:+ " -p POD_MANAGEMENT_POLICY=${POD_MANAGEMENT_POLICY}"} \
#  ${PVC_SIZE:+ " -p PVC_SIZE=${PVC_SIZE}"} \
#  ${CPU_REQUEST:+ "-p CPU_REQUEST=${CPU_REQUEST}"} \
#  ${CPU_LIMIT:+ "-p CPU_LIMIT=${CPU_LIMIT}"} \
#  ${MEMORY_REQUEST:+ "-p MEMORY_REQUEST=${MEMORY_REQUEST}"} \
#  ${MEMORY_LIMIT:+ "-p MEMORY_LIMIT=${MEMORY_LIMIT}"}"

# In order to avoid running out of storage quote in our development environment, use
# ephemeral storage by removing the pvc request from the template.
if [ "$EPHEMERAL_STORAGE" = "True" ]
then
    # Pipe the template to jq, and delete the pvc and volume claim items from the template.
    OC_PROCESS="${OC_PROCESS} | jq 'del(.items[6].spec.template.spec.volumes[0].persistentVolumeClaim) \
| del(.items[6].spec.volumeClaimTemplates)'"
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
