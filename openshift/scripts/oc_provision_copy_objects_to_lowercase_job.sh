#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Render Helper
#%
#%   Renders this resource's manifest to stdout -- does not apply it. Intended for
#%   use with a pull request-based pipeline. Suffixes incl.: pr-###.
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
#%   Render and apply it:
#%   ${THIS_FILE} pr-0 | oc apply -f -
#%

# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

WEATHER_IMAGE="${WEATHER_IMAGE:-ghcr.io/bcgov/wps/wps-weather:${SUFFIX}}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process --local -f ${TEMPLATE_PATH}/copy_objects_to_lowercase.job.yaml -o json \
-p NAME=${APP_NAME} \
-p SUFFIX=${SUFFIX} \
-p WEATHER_IMAGE=${WEATHER_IMAGE}"

# Render the manifest to stdout.
#
eval "${OC_PROCESS}"
