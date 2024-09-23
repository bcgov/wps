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
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${PATH_DEPLOY} \
 -p SUFFIX=${SUFFIX} \
 -p PROJECT_NAMESPACE=${PROJ_TARGET} \
 -p POSTGRES_USER=wps-crunchydb-${SUFFIX} \
 -p POSTGRES_DATABASE=${POSTGRES_DATABASE:-${APP_NAME}} \
 -p CRUNCHYDB_USER=wps-crunchydb-${SUFFIX}-pguser-wps-crunchydb-${SUFFIX} \
 -p VANITY_DOMAIN=${VANITY_DOMAIN} \
 ${SECOND_LEVEL_DOMAIN:+ "-p SECOND_LEVEL_DOMAIN=${SECOND_LEVEL_DOMAIN}"} \
 ${GUNICORN_WORKERS:+ "-p GUNICORN_WORKERS=${GUNICORN_WORKERS}"} \
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

# Select the most recently created pod for the deployment
SELECTED_POD=$(oc get pods -n ${PROJ_TARGET} -l name=${OBJ_NAME} --sort-by=.metadata.creationTimestamp -o custom-columns=":metadata.name" | tail -n 1)

# Prepare the log command with the selected pod, so we don't logs from old pods that are being terminated
if [ -n "$SELECTED_POD" ]; then
    OC_LOG="oc -n ${PROJ_TARGET} logs -f ${SELECTED_POD} --pod-running-timeout=2m --all-containers=true"
else
    echo "No pods found for deployment ${OBJ_NAME}."
    OC_LOG=""
fi

# Run the OC_PROCESS command
eval ${OC_PROCESS}

# Run OC_PROCESS and pipe it to OC_APPLY
eval "${OC_PROCESS} | ${OC_APPLY}"

# Run the OC_LOG command only if it's not empty
if [ -n "${OC_LOG}" ]; then
  eval "${OC_LOG}"
fi

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}" "${OC_LOG}"
