#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift ASA Go API Deploy Helper
#%
#%   Deploy the dedicated ASA Go API service used behind APS.
#%
#% Usage:
#%
#%   [CPU_REQUEST=<>] [MEMORY_REQUEST=<>] [MEMORY_LIMIT=<>] [REPLICAS=<>] \
#%   [ALLOWED_ORIGINS=<>] ${THIS_FILE} [SUFFIX] [apply]
#%
#% Examples:
#%
#%   ${THIS_FILE} pr-0
#%   ${THIS_FILE} pr-0 apply
#

PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"
OBJ_NAME="${APP_NAME}-${SUFFIX}-asa-go"
DEPLOY_VERSION="${DEPLOY_VERSION:-$(date +%s)}"

OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/asa_go_api.yaml \
 -p APP_NAME=${APP_NAME} \
 -p SUFFIX=${SUFFIX} \
 -p PROJECT_NAMESPACE=${PROJ_TARGET} \
 -p POSTGRES_DATABASE=${POSTGRES_DATABASE:-${APP_NAME}} \
 -p CRUNCHYDB_USER=${CRUNCHY_NAME}-${SUFFIX}-pguser-${CRUNCHY_NAME}-${SUFFIX} \
 ${GUNICORN_WORKERS:+ "-p GUNICORN_WORKERS=${GUNICORN_WORKERS}"} \
 ${CPU_REQUEST:+ "-p CPU_REQUEST=${CPU_REQUEST}"} \
 ${MEMORY_REQUEST:+ "-p MEMORY_REQUEST=${MEMORY_REQUEST}"} \
 ${MEMORY_LIMIT:+ "-p MEMORY_LIMIT=${MEMORY_LIMIT}"} \
 ${PROJ_TOOLS:+ "-p PROJ_TOOLS=${PROJ_TOOLS}"} \
 ${IMAGE_REGISTRY:+ "-p IMAGE_REGISTRY=${IMAGE_REGISTRY}"} \
 ${ENVIRONMENT:+ "-p ENVIRONMENT=${ENVIRONMENT}"} \
 ${ALLOWED_ORIGINS:+ "-p ALLOWED_ORIGINS=${ALLOWED_ORIGINS}"} \
 ${REPLICAS:+ "-p REPLICAS=${REPLICAS}"} \
 -p DEPLOY_VERSION=${DEPLOY_VERSION}"

OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run=client"

eval ${OC_PROCESS}
eval "${OC_PROCESS} | ${OC_APPLY}"

oc -n ${PROJ_TARGET} rollout status deployment/${OBJ_NAME}

display_helper "${OC_PROCESS} | ${OC_APPLY}"
