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

# Apply template (apply or use --dry-run)
#
OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run"

# Execute commands
#
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}"
