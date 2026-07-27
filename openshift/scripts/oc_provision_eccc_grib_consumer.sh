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

# wps-weather image: GHCR by default. Callers (e.g. the production promotion fallback) can
# override this to the internal OpenShift ImageStream if the GHCR build/promotion path failed.
WEATHER_IMAGE="${WEATHER_IMAGE:-ghcr.io/bcgov/wps/wps-weather:${SUFFIX}}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/eccc_grib_consumer.yaml \
-p SUFFIX=${SUFFIX} \
-p WEATHER_IMAGE=${WEATHER_IMAGE}"

# Apply template (apply or use --dry-run)
#
OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run"

# Restart the deployment so it actually pulls the freshly-pushed image. Unlike the internal
# OpenShift registry, ghcr.io isn't watched by an ImageStream trigger, so re-applying the same
# manifest with the same tag (e.g. pr-###) wouldn't otherwise cause a rollout.
OC_ROLLOUT_RESTART="oc -n ${PROJ_TARGET} rollout restart deployment/${APP_NAME}-${SUFFIX}-eccc-consumer"
[ "${APPLY}" ] || OC_ROLLOUT_RESTART=""

# Execute commands
#
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"
eval "${OC_ROLLOUT_RESTART}"

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}"
