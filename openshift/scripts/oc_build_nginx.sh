#!/bin/sh -l
#
source "$(dirname ${0})/common/envars"

PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

OC_NGINX_BUILD="oc -n ${PROJ_TARGET} apply -f ${TEMPLATE_PATH}/tileserv/nginx_build.yaml"
OC_NGINX_IS="oc create imagestream nginx-tileserv"
OC_NGINX_START_BUILD="oc start-build nginx-tileserv --from-dir=${TEMPLATE_PATH}/tileserv --follow"

# Execute commands
#
eval "${OC_NGINX_BUILD}"
eval "${OC_NGINX_IS}"
eval "${OC_NGINX_START_BUILD}"

