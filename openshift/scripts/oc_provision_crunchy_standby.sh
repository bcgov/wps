#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Deploy Helper
#%
#%   Intended to deploy a once-off standby cluster which replicates from a pgbackrest repo
#%   Suffixes incl.: pr-###.
#%
#% Usage:
#%
#%    PROJ_TARGET={namespace-target} BUCKET={your-s3-bucket} ${THIS_FILE} [SUFFIX] [apply]
#%
#% Examples:
#%
#%   Provide a PR number. Defaults to a dry-run.
#%   PROJ_TARGET={namespace-target} BUCKET={your-s3-bucket} ${THIS_FILE} pr-0
#%
#%   Apply when satisfied.
#%   PROJ_TARGET={namespace-target} BUCKET={your-s3-bucket} ${THIS_FILE} pr-0 apply
#%


# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

# Set DATE to today's date if it isn't set
DATE=${DATE:-$(date +"%Y%m%d")}
 
# Prepare names for crunchy ephemeral instance for this PR.
IMAGE_STREAM_NAMESPACE=${IMAGE_STREAM_NAMESPACE:-${PROJ_TOOLS}}
EPHEMERAL_STORAGE=${EPHEMERAL_STORAGE:-'False'}

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/crunchy_standby.yaml \
-p SUFFIX=${SUFFIX} \
-p TARGET_NAMESPACE=${PROJ_TARGET} \
-p CRUNCHY_NAME=${CRUNCHY_NAME} \
-p BUCKET=${BUCKET} \
-p DATE=${DATE} \
-p DATA_SIZE=${DATA_SIZE:-65Gi} \
-p WAL_SIZE=${WAL_SIZE:-15Gi} \
 ${IMAGE_NAME:+ " -p IMAGE_NAME=${IMAGE_NAME}"} \
 ${IMAGE_TAG:+ " -p IMAGE_TAG=${IMAGE_TAG}"} \
 ${IMAGE_REGISTRY:+ " -p IMAGE_REGISTRY=${IMAGE_REGISTRY}"} \
 -p CPU_REQUEST=75m \
 -p MEMORY_REQUEST=2Gi \
 -p MEMORY_LIMIT=16Gi"



# In order to avoid running out of storage quota in our development environment, use
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

eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}"
