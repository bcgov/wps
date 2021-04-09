#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

# Build a base image with packages installed

# The image doesn't exist, so we have to build it.
# Process a template (mostly variable substition)
#
PATH_CACHE_BC="${PATH_CACHE_BC:-$(dirname ${0})/../templates/build.api.cache.bc.yaml}"
OC_PROCESS="oc -n ${PROJ_TOOLS} process -f ${PATH_BC} -p NAME=${NAME_APP} -p SUFFIX=${SUFFIX} -p GIT_BRANCH=${GIT_BRANCH} -p VERSION=${md5}"

# Apply a template (apply or use --dry-run)
#
OC_APPLY="oc -n ${PROJ_TOOLS} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run"

# Cancel non complete builds and start a new build (apply or don't run)
#
OC_CANCEL_BUILD="oc -n ${PROJ_TOOLS} cancel-build bc/${NAME_OBJ}"
[ "${APPLY}" ] || OC_CANCEL_BUILD=""
OC_START_BUILD="oc -n ${PROJ_TOOLS} start-build ${NAME_OBJ} --follow=true"
[ "${APPLY}" ] || OC_START_BUILD=""


# Calculat the hash, and look if the image exists.
md5=`md5sum api/poetry.lock | awk '{print $1}'`
echo $md5
tag="wps-api-pr-588-cache:${md5}"
echo $tag
command="oc -n e1e498-tools get istag/${tag}"
result=$(eval "${command}")
# result=$(command)
echo $?
echo "result = $result"


if [ $? -eq 0 ]
then
  echo "Cached image already exists"
else
  echo "Have to create it!"
fi

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}" "${OC_CANCEL_BUILD}" "${OC_START_BUILD}"