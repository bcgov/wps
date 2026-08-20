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
SCHEDULE="${SCHEDULE:-$((14 + $RANDOM % 41)) 22 * * *}"

# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/s3_retention.cronjob.yaml \
-p JOB_NAME=s3-retention-${APP_NAME}-${SUFFIX} \
-p APP_LABEL=${APP_NAME}-${SUFFIX} \
-p SUFFIX=${SUFFIX} \
-p SCHEDULE=\"${SCHEDULE}\""

# Render the manifest to stdout.
#
eval "${OC_PROCESS}"
