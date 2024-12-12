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
#%    [PROJ_TARGET] [PG_DATABASE] [TABLE] ${THIS_FILE} [SUFFIX]
#%
#% Examples:
#%
#%   PROJ_TARGET=e1e498-dev PG_DATABASE=wps TABLE=table ${THIS_FILE} pr-0

JOB="job/fill-partition-data-${SUFFIX}"

# create the job
oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/partition_filler_job.yaml \
    -p SUFFIX=${SUFFIX} \
    -p PG_DATABASE=${PG_DATABASE} \
    -p CRUNCHYDB_USER=${CRUNCHY_NAME}-${SUFFIX}-pguser-${CRUNCHY_NAME}-${SUFFIX} \
    -p PROJ_TOOLS=${PROJ_TOOLS} | jq '.items[0]' | oc -n ${PROJ_TARGET} create -f -
# wait for the job to finish
oc wait --for=condition=complete ${JOB} --timeout=3600s
# output the log for debugging
oc logs -f ${JOB}
# we're done, so get rid of the job
oc delete ${JOB}

