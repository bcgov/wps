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

# Run the OC_PROCESS command
eval ${OC_PROCESS}

# Run OC_PROCESS and pipe it to OC_APPLY
eval "${OC_PROCESS} | ${OC_APPLY}"


# Log scaling events for the deployment to console
oc get events -n ${PROJ_TARGET} --field-selector involvedObject.kind=Deployment,involvedObject.name=${OBJ_NAME} --watch &

# Wait for all new replicas to be running and available
while true; do
    # Get the number of desired replicas
    DESIRED_REPLICAS=$(oc get deployment ${OBJ_NAME} -n ${PROJ_TARGET} -o jsonpath='{.status.replicas}')
    
    # Get the number of available replicas
    AVAILABLE_REPLICAS=$(oc get deployment ${OBJ_NAME} -n ${PROJ_TARGET} -o jsonpath='{.status.availableReplicas}')
    AVAILABLE_REPLICAS=${AVAILABLE_REPLICAS:-0} 

    # Check if available replicas match desired replicas
    if [ "$DESIRED_REPLICAS" -eq "$AVAILABLE_REPLICAS" ]; then
        echo "All ${DESIRED_REPLICAS} replicas are running and available."
        break
    fi

    echo "Waiting for all replicas to be available... (Desired: ${DESIRED_REPLICAS}, Available: ${AVAILABLE_REPLICAS})"
    sleep 10
done

# Kill the background process of the event logging
kill %1

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}"
