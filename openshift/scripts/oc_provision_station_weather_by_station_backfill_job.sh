#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Render Helper
#%
#%   Renders the one-off job that rebuilds the by_station table of station weather from the
#%   by_time table, from a year onwards. The nightly cron job only rebuilds the current year,
#%   so run this after backfilling earlier years. Renders the manifest to stdout -- does not
#%   apply it. Suffixes incl.: pr-###.
#%
#%   The job runs the deployment's jobs image, so the code it runs is the code that
#%   deployment was built from. It cannot be changed once created: delete the old job before
#%   running it again.
#%
#% Usage:
#%
#%    [FROM_YEAR] ${THIS_FILE} [SUFFIX]
#%
#% Examples:
#%
#%   Just render it, for every year from 1987:
#%   ${THIS_FILE} pr-0
#%
#%   Render and run it from a later year:
#%   FROM_YEAR=2020 ${THIS_FILE} pr-0 | oc -n e1e498-dev apply -f -
#%
#%   Follow it, then remove it:
#%   oc -n e1e498-dev logs -f job/station-weather-by-station-backfill-wps-pr-0
#%   oc -n e1e498-dev delete job station-weather-by-station-backfill-wps-pr-0
#%

# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

# From the data mart's first year, if the first year is not specified.
FROM_YEAR="${FROM_YEAR:-1987}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process --local -f ${TEMPLATE_PATH}/station_weather_by_station_backfill_job.yaml -o json \
-p JOB_NAME=station-weather-by-station-backfill-${APP_NAME}-${SUFFIX} \
-p APP_LABEL=${APP_NAME}-${SUFFIX} \
-p NAME=${APP_NAME} \
-p SUFFIX=${SUFFIX} \
-p FROM_YEAR=${FROM_YEAR} \
${PROJ_TOOLS:+ "-p PROJ_TOOLS=${PROJ_TOOLS}"} \
${IMAGE_REGISTRY:+ "-p IMAGE_REGISTRY=${IMAGE_REGISTRY}"} \
${MEMORY_REQUEST:+ "-p MEMORY_REQUEST=${MEMORY_REQUEST}"} \
${MEMORY_LIMIT:+ "-p MEMORY_LIMIT=${MEMORY_LIMIT}"}"

# Render the manifest to stdout.
#
eval "${OC_PROCESS}"
