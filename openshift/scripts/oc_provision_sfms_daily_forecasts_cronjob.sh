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

# Schedule: 15:00 UTC (8:00 AM PDT)
SCHEDULE="${SCHEDULE:-0 15 * * *}"

# Optional suffix to distinguish multiple forecast schedules for the same deployment,
# e.g. "8am" vs "545pm" -- folded into the name prefix, same convention
# oc_provision_wx_4panel_charts_cronjob.sh uses for its MODEL variant, so every cronjob
# script's JOB_NAME ends the same way: <prefix>-${APP_NAME}-${SUFFIX}. (Previously a
# one-off ${JOB_NAME_SUFFIX} derived variable, which put ${SUFFIX} in an unexpected
# place -- confirmed live: this quietly broke a hand-generated Kustomize base that
# assumed the standard pattern.)
JOB_SUFFIX="${JOB_SUFFIX:-}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/sfms_daily_forecasts.cronjob.yaml -o yaml \
-p JOB_NAME=sfms-forecast${JOB_SUFFIX:+-${JOB_SUFFIX}}-${APP_NAME}-${SUFFIX} \
-p APP_LABEL=${APP_NAME}-${SUFFIX} \
-p NAME=${APP_NAME} \
-p SUFFIX=${SUFFIX} \
-p SCHEDULE=\"${SCHEDULE}\" \
-p POSTGRES_DATABASE=${POSTGRES_DATABASE:-${APP_NAME}} \
-p CRUNCHYDB_USER=${CRUNCHY_NAME}-${SUFFIX}-pguser-${CRUNCHY_NAME}-${SUFFIX} \
-p PROJECT_NAMESPACE=${PROJ_TARGET} \
${MEMORY_REQUEST:+ "-p MEMORY_REQUEST=${MEMORY_REQUEST}"} \
${MEMORY_LIMIT:+ "-p MEMORY_LIMIT=${MEMORY_LIMIT}"} \
${PROJ_TOOLS:+ "-p PROJ_TOOLS=${PROJ_TOOLS}"} \
${IMAGE_REGISTRY:+ "-p IMAGE_REGISTRY=${IMAGE_REGISTRY}"}"

# Render the manifest to stdout.
#
eval "${OC_PROCESS}"
