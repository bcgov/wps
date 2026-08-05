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
#%    MODEL=HRDPS|GDPS|RDPS ${THIS_FILE} [SUFFIX] [apply]
#%
#% Examples:
#%
#%   Provide a PR number. Defaults to a dry-run.
#%   MODEL=HRDPS ${THIS_FILE} pr-0
#%
#%   Apply when satisfied.
#%   MODEL=HRDPS ${THIS_FILE} pr-0 apply
#%

# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

# Use a random time if schedule not specified. RDPS runs can take over an hour, so it
# gets its own schedule every 2 hours; HRDPS and GDPS each get their own random hourly
# offset so they don't all hit Env Canada's servers at the same time.
case "$MODEL" in
  RDPS)
    SCHEDULE="${SCHEDULE:-$((24 + $RANDOM % 35)) */2 * * *}"
    ;;
  HRDPS)
    SCHEDULE="${SCHEDULE:-$((13 + $RANDOM % 46)) * * * *}"
    ;;
  *)
    SCHEDULE="${SCHEDULE:-$((9 + $RANDOM % 50)) * * * *}"
    ;;
esac

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/env_canada.cronjob.yaml \
-p JOB_NAME=env-canada-${MODEL,,}-${APP_NAME}-${SUFFIX} \
-p MODEL=${MODEL} \
-p APP_LABEL=${APP_NAME}-${SUFFIX} \
-p NAME=${APP_NAME} \
-p SUFFIX=${SUFFIX} \
-p SCHEDULE=\"${SCHEDULE}\" \
-p POSTGRES_DATABASE=${POSTGRES_DATABASE:-${APP_NAME}} \
-p CRUNCHYDB_USER=${CRUNCHY_NAME}-${SUFFIX}-pguser-${CRUNCHY_NAME}-${SUFFIX} \
${PROJ_TOOLS:+ "-p PROJ_TOOLS=${PROJ_TOOLS}"} \
${IMAGE_REGISTRY:+ "-p IMAGE_REGISTRY=${IMAGE_REGISTRY}"} \
${MEMRAY_ENABLED:+ "-p MEMRAY_ENABLED=${MEMRAY_ENABLED}"} \
${MEMORY_REQUEST:+ "-p MEMORY_REQUEST=${MEMORY_REQUEST}"} \
${MEMORY_LIMIT:+ "-p MEMORY_LIMIT=${MEMORY_LIMIT}"} \
${MALLOC_ARENA_MAX:+ "-p MALLOC_ARENA_MAX=${MALLOC_ARENA_MAX}"} \
-p PROJECT_NAMESPACE=${PROJ_TARGET}"

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
