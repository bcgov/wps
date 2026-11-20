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

# Once a night at a random minute past 11:00 UTC, after the maintenance job, if schedule not
# specified.
SCHEDULE="${SCHEDULE:-$((RANDOM % 60)) 11 * * *}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process --local -f ${TEMPLATE_PATH}/station_weather_by_station.cronjob.yaml -o json \
-p JOB_NAME=station-weather-by-station-${APP_NAME}-${SUFFIX} \
-p APP_LABEL=${APP_NAME}-${SUFFIX} \
-p NAME=${APP_NAME} \
-p SUFFIX=${SUFFIX} \
-p SCHEDULE=\"${SCHEDULE}\" \
${PROJ_TOOLS:+ "-p PROJ_TOOLS=${PROJ_TOOLS}"} \
${IMAGE_REGISTRY:+ "-p IMAGE_REGISTRY=${IMAGE_REGISTRY}"} \
${MEMORY_REQUEST:+ "-p MEMORY_REQUEST=${MEMORY_REQUEST}"} \
${MEMORY_LIMIT:+ "-p MEMORY_LIMIT=${MEMORY_LIMIT}"}"

# Render the manifest to stdout.
#
eval "${OC_PROCESS}"
