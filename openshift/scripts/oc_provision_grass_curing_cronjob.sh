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

# Specify a default schedule to run daily at 5am-ish
SCHEDULE="${SCHEDULE:-$((3 + $RANDOM % 54)) * * * *}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/grass_curing.cronjob.yaml -o yaml \
-p JOB_NAME=grass-curing-${APP_NAME}-${SUFFIX} \
-p APP_LABEL=${APP_NAME}-${SUFFIX} \
-p NAME=${APP_NAME} \
-p SUFFIX=${SUFFIX} \
-p SCHEDULE=\"${SCHEDULE}\" \
-p POSTGRES_DATABASE=${POSTGRES_DATABASE:-${APP_NAME}} \
-p CRUNCHYDB_USER=${CRUNCHY_NAME}-${SUFFIX}-pguser-${CRUNCHY_NAME}-${SUFFIX} \
${PROJ_TOOLS:+ "-p PROJ_TOOLS=${PROJ_TOOLS}"} \
${IMAGE_REGISTRY:+ "-p IMAGE_REGISTRY=${IMAGE_REGISTRY}"} \
-p PROJECT_NAMESPACE=${PROJ_TARGET}"

# Render the manifest to stdout.
#
eval "${OC_PROCESS}"
