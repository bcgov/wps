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
JOB_NAME="cleanup-s3-backup-${NAME_APP}-${SUFFIX}"
IMAGE_NAMESPACE=${PROJ_TOOLS}
CLUSTER_NAME="patroni-${NAME_APP}-${SUFFIX}"

OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/backup-s3-cleanup-job.yaml \
    -p JOB_NAME=${JOB_NAME} \
    -p IMAGE_NAMESPACE=${IMAGE_NAMESPACE} \
    ${CPU_LIMIT:+ " -p CPU_LIMIT=${CPU_LIMIT}"} \
    ${CPU_REQUEST:+ " -p CPU_REQUEST=${CPU_REQUEST}"} \
    ${SCHEDULE:+ " -p SCHEDULE=\"${SCHEDULE}\""} \
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
