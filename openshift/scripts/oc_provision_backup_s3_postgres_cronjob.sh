#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Render Helper
#%
#%   Renders this resource's manifest to stdout -- does not apply it. Intended for
#%   use with a pull request-based pipeline. Suffixes incl.: pr-###.
#%
#%   Applying is the caller's job: pipe into `oc apply -f -` yourself, or see
#%   oc_deploy_to_production.sh / deployment.yml for how this is combined with
#%   other resources and applied together in one call.
#%
#% Usage:
#%
#%    ${THIS_FILE} [SUFFIX]
#%
#% Examples:
#%
#%   Just render it:
#%   ${THIS_FILE} pr-0
#%
#%   Render and apply this one resource on its own:
#%   ${THIS_FILE} pr-0 | oc apply -f -
#%


# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

# Prepare variables for backups
JOB_NAME="backup-postgres-${APP_NAME}-${SUFFIX}"
IMAGE_NAMESPACE=${PROJ_TOOLS}
CLUSTER_NAME="${CRUNCHY_NAME}-${SUFFIX}"

OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/backup-s3-postgres-cronjob.yaml -o yaml \
    -p CRUNCHYDB_USER=${CRUNCHY_NAME}-${SUFFIX}-pguser-${CRUNCHY_NAME}-${SUFFIX} \
    -p JOB_NAME=${JOB_NAME} \
    -p IMAGE_NAMESPACE=${IMAGE_NAMESPACE} \
    -p APP_LABEL=${APP_NAME}-${SUFFIX} \
    -p CLUSTER_NAME=${CLUSTER_NAME} \
    ${CPU_REQUEST:+ " -p CPU_REQUEST=${CPU_REQUEST}"} \
    ${SCHEDULE:+ " -p SCHEDULE=\"${SCHEDULE}\""} \
    ${TAG_NAME:+ " -p TAG_NAME=${TAG_NAME}"}"

# Render the manifest to stdout.
#
eval "${OC_PROCESS}"
