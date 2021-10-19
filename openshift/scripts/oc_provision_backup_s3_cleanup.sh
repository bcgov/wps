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

CLUSTER_NAME="patroni-${NAME_APP}-${SUFFIX}"

# create the job
# oc create -f ${TEMPLATE_PATH}/backup-s3-cleanup-job.yaml
oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/backup-s3-cleanup-job.yaml \
    -p SUFFIX=${SUFFIX} \
    -p PROJ_TOOLS=${PROJ_TOOLS} \
    -p CLUSTER_NAME=${CLUSTER_NAME}
# wait for the job to finish
# oc wait --for=condition=complete jobs/cleanup-s3 --timeout=30s
# output the log for debugging
# oc logs -f job/cleanup-s3
# we're done, so get rid of the job
# oc delete job/cleanup-s3

