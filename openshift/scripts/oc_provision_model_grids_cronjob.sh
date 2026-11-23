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
#%   MODEL is required: the model whose grids the job keeps (HRDPS, RDPS, GDPS, GFS, ECMWF).
#%
#% Usage:
#%
#%    MODEL=<model> ${THIS_FILE} [SUFFIX]
#%
#% Examples:
#%
#%   Just render it:
#%   MODEL=HRDPS ${THIS_FILE} pr-0
#%
#%   Render and apply this one resource on its own:
#%   MODEL=HRDPS ${THIS_FILE} pr-0 | oc apply -f -
#%

if [ -z "${MODEL:-}" ]; then
	echo "MODEL is required, e.g. MODEL=HRDPS" >&2
	exit 1
fi
MODEL_LOWER=$(echo "${MODEL}" | tr '[:upper:]' '[:lower:]')

# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

# Hourly at a random minute, if schedule not specified: a run is stored soon after all of it
# is published.
SCHEDULE="${SCHEDULE:-$((RANDOM % 60)) * * * *}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process --local -f ${TEMPLATE_PATH}/model_grids.cronjob.yaml -o json \
-p JOB_NAME=model-grids-${MODEL_LOWER}-${APP_NAME}-${SUFFIX} \
-p MODEL=${MODEL} \
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
