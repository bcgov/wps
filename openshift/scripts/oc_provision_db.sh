#!/bin/bash -l
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
PATRONI_CLUSTER_NAME="patroni-${NAME_APP}-${SUFFIX}"
APPLICATION_NAME="patroni-${NAME_APP}-${SUFFIX}"
PATRONI_LEADER_SERVICE_NAME="patroni-leader-${NAME_APP}-${SUFFIX}"
PATRONI_REPLICA_SERVICE_NAME="patroni-replica-${NAME_APP}-${SUFFIX}"
SERVICE_ACCOUNT="patroniocp-${NAME_APP}-${SUFFIX}"
IMAGE_NAMESPACE=${PROJ_TOOLS}

# Process template
# Note: A role issue is currenty preventing use of the image if it resides in the tools project.
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/patroni.yaml \
-p NAME=${NAME_APP} \
-p SUFFIX=${SUFFIX} \
-p PATRONI_CLUSTER_NAME=${PATRONI_CLUSTER_NAME} \
-p APPLICATION_NAME=${APPLICATION_NAME} \
-p PATRONI_LEADER_SERVICE_NAME=${PATRONI_LEADER_SERVICE_NAME} \
-p PATRONI_REPLICA_SERVICE_NAME=${PATRONI_REPLICA_SERVICE_NAME} \
-p SERVICE_ACCOUNT=${SERVICE_ACCOUNT} \
-p IMAGE_NAMESPACE=${IMAGE_NAMESPACE} \
 ${PVC_SIZE:+ " -p PVC_SIZE=${PVC_SIZE}"} \
 ${CPU_REQUEST:+ "-p CPU_REQUEST=${CPU_REQUEST}"} \
 ${CPU_LIMIT:+ "-p CPU_LIMIT=${CPU_LIMIT}"} \
 ${MEMORY_REQUEST:+ "-p MEMORY_REQUEST=${MEMORY_REQUEST}"} \
 ${MEMORY_LIMIT:+ "-p MEMORY_LIMIT=${MEMORY_LIMIT}"}"

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
