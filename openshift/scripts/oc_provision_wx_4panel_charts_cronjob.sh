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

# Specify a default schedule to run daily at 4am
SCHEDULE="${SCHEDULE:-$((3 + $RANDOM % 54)) * * * *}"

# wps-weather image: GHCR by default. Callers (e.g. the production promotion fallback) can
# override this to the internal OpenShift ImageStream if the GHCR build/promotion path failed.
WEATHER_IMAGE="${WEATHER_IMAGE:-ghcr.io/bcgov/wps/wps-weather:${SUFFIX}}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/wx_4panel_charts.cronjob.yaml \
-p JOB_NAME=wx-4panel-charts-${MODEL,,}-${APP_NAME}-${SUFFIX} \
-p APP_LABEL=${APP_NAME}-${SUFFIX} \
-p NAME=${APP_NAME} \
-p SUFFIX=${SUFFIX} \
-p SCHEDULE=\"${SCHEDULE}\" \
-p CRUNCHYDB_USER=${CRUNCHY_NAME}-${SUFFIX}-pguser-${CRUNCHY_NAME}-${SUFFIX} \
-p END_HOUR=${END_HOUR} \
-p STEP=${STEP} \
-p MODEL=${MODEL} \
-p WEATHER_IMAGE=${WEATHER_IMAGE}"

# Render the manifest to stdout.
#
eval "${OC_PROCESS}"
