#!/bin/sh -l
#
source "$(dirname ${0})/common/envars"

PROJ_TARGET="e1e498-tools"

OC_NGINX_BUILD="oc -n ${PROJ_TARGET} apply -f ${TEMPLATE_PATH}/tileserv/nginx_build.yaml"
OC_NGINX_IS="oc -n ${PROJ_TARGET} create imagestream nginx-tileserv"
OC_NGINX_START_BUILD="oc -n ${PROJ_TARGET} start-build nginx-tileserv --from-dir=${TEMPLATE_PATH}/tileserv --follow"

# Execute commands
#
eval "${OC_NGINX_BUILD}"
eval "${OC_NGINX_IS}"
eval "${OC_NGINX_START_BUILD}"

