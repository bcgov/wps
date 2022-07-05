#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Deploy Helper
#%
#%   Intended for use with a pull request-based pipeline.
#%   Suffixes incl.: pr-###, test and prod.
#%
#% Usage:
#%
#%   [CPU_REQUEST=<>] [CPU_LIMIT=<>] [MEMORY_REQUEST=<>] [MEMORY_LIMIT=<>] [REPLICAS=<>] \
#%     ${THIS_FILE} [SUFFIX] [apply]
#%
#% Examples:
#%
#%   Provide a PR number. Defaults to a dry-run=client.
#%   ${THIS_FILE} pr-0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} pr-0 apply
#%
#%   Override default CPU_REQUEST to 2000 millicores
#%   CPU_REQUEST=2000m ${THIS_FILE} pr-0

# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"
OBJ_NAME="${APP_NAME}-${SUFFIX}"

# Process a template (mostly variable substition)
#
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${PATH_DC} \
 -p SUFFIX=${SUFFIX} \
 -p PROJECT_NAMESPACE=${PROJ_TARGET} \
 -p POSTGRES_USER=${POSTGRES_USER:-${APP_NAME}} \
 -p POSTGRES_DATABASE=${POSTGRES_DATABASE:-${APP_NAME}} \
 -p POSTGRES_WRITE_HOST=${POSTGRES_WRITE_HOST:-"patroni-${APP_NAME}-${SUFFIX}-leader"} \
 -p POSTGRES_READ_HOST=${POSTGRES_READ_HOST:-"patroni-${APP_NAME}-${SUFFIX}-replica"} \
 -p VANITY_DOMAIN=${VANITY_DOMAIN} \
 ${SECOND_LEVEL_DOMAIN:+ "-p SECOND_LEVEL_DOMAIN=${SECOND_LEVEL_DOMAIN}"} \
 ${WORKERS_PER_CORE:+ "-p WORKERS_PER_CORE=${WORKERS_PER_CORE}"} \
 ${CPU_REQUEST:+ "-p CPU_REQUEST=${CPU_REQUEST}"} \
 ${CPU_LIMIT:+ "-p CPU_LIMIT=${CPU_LIMIT}"} \
 ${MEMORY_REQUEST:+ "-p MEMORY_REQUEST=${MEMORY_REQUEST}"} \
 ${MEMORY_LIMIT:+ "-p MEMORY_LIMIT=${MEMORY_LIMIT}"} \
 ${PROJ_TOOLS:+ "-p PROJ_TOOLS=${PROJ_TOOLS}"} \
 ${IMAGE_REGISTRY:+ "-p IMAGE_REGISTRY=${IMAGE_REGISTRY}"} \
 ${USE_WFWX:+ "-p USE_WFWX=${USE_WFWX}"} \
 ${ENVIRONMENT:+ "-p ENVIRONMENT=${ENVIRONMENT}"} \
 ${REPLICAS:+ "-p REPLICAS=${REPLICAS}"}"

# Apply a template (apply or use --dry-run=client)
#
OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run=client"

# Cancel all previous deployments
#
OC_CANCEL_ALL_PREV_DEPLOY="oc -n ${PROJ_TARGET} rollout cancel dc/${OBJ_NAME} || true"

# Deploy and follow the progress
#
OC_DEPLOY="oc -n ${PROJ_TARGET} rollout latest dc/${OBJ_NAME}"
OC_LOG="oc -n ${PROJ_TARGET} logs -f --pod-running-timeout=2m dc/${OBJ_NAME}"
if [ ! "${APPLY}" ]; then
  OC_CANCEL_ALL_PREV_DEPLOY=""
  OC_DEPLOY="${OC_DEPLOY} --dry-run=client || true" # in case there is no previous rollout
  OC_LOG=""
fi

# Execute commands
#
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"
if [ "${APPLY}" ]; then
  echo "canceling previous deployments..."
  eval "${OC_CANCEL_ALL_PREV_DEPLOY}"
  count=1
  timeout=10
  # Check previous deployment statuses before moving onto new deploying
  while [ $count -le $timeout ]; do
    sleep 1
    PENDINGS="$(oc -n ${PROJ_TARGET} rollout history dc/${OBJ_NAME} | awk '{print $2}' | grep -c Pending || true)"
    RUNNINGS="$(oc -n ${PROJ_TARGET} rollout history dc/${OBJ_NAME} | awk '{print $2}' | grep -c Running || true)"
    if [ "${PENDINGS}" == 0 ] && [ "${RUNNINGS}" == 0 ]; then
      # No pending or running replica controllers so exit the while loop
      break 2
    fi
    count=$(( $count + 1 ))
  done
  if [ $count -gt $timeout ]; then
    echo "\n*** timeout for canceling deployment ***\n"
    exit 1
  fi
fi
eval "${OC_DEPLOY}"
eval "${OC_LOG}"

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}" $OC_CANCEL_ALL_PREV_DEPLOY $OC_DEPLOY $OC_LOG
