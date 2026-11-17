#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Render Helper
#%
#%   Renders the one-off job that copies historical station observations from the BCWS data
#%   mart into the station weather tables in object storage. Renders the manifest to stdout --
#%   does not apply it. Suffixes incl.: pr-###.
#%
#%   The job runs the deployment's jobs image, so the code it runs is the code that
#%   deployment was built from. It cannot be changed once created: delete the old job before
#%   running it again.
#%
#% Usage:
#%
#%    [FROM_YEAR] [TO_YEAR] ${THIS_FILE} [SUFFIX]
#%
#% Examples:
#%
#%   Just render it, for every year:
#%   ${THIS_FILE} pr-0
#%
#%   Render and run it for some years:
#%   FROM_YEAR=2020 TO_YEAR=2026 ${THIS_FILE} pr-0 | oc -n e1e498-dev apply -f -
#%
#%   Follow it, then remove it:
#%   oc -n e1e498-dev logs -f job/station-actuals-data-mart-backfill-wps-pr-0
#%   oc -n e1e498-dev delete job station-actuals-data-mart-backfill-wps-pr-0
#%

# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

# Every year the data mart has, if the years are not specified.
FROM_YEAR="${FROM_YEAR:-1987}"
TO_YEAR="${TO_YEAR:-$(date -u +%Y)}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process --local -f ${TEMPLATE_PATH}/station_actuals_data_mart_backfill_job.yaml -o json \
-p JOB_NAME=station-actuals-data-mart-backfill-${APP_NAME}-${SUFFIX} \
-p APP_LABEL=${APP_NAME}-${SUFFIX} \
-p NAME=${APP_NAME} \
-p SUFFIX=${SUFFIX} \
-p FROM_YEAR=${FROM_YEAR} \
-p TO_YEAR=${TO_YEAR} \
${PROJ_TOOLS:+ "-p PROJ_TOOLS=${PROJ_TOOLS}"} \
${IMAGE_REGISTRY:+ "-p IMAGE_REGISTRY=${IMAGE_REGISTRY}"} \
${MEMORY_REQUEST:+ "-p MEMORY_REQUEST=${MEMORY_REQUEST}"} \
${MEMORY_LIMIT:+ "-p MEMORY_LIMIT=${MEMORY_LIMIT}"}"

# Render the manifest to stdout.
#
eval "${OC_PROCESS}"
