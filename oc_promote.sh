#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift ImageStreamTag Promotion Helper
#%
#%   Promote a passing imagestreamtag by labeling is as prod.
#%   Suffixes incl.: pr-###, test and prod.
#%
#% Usage:
#%
#%   ${THIS_FILE} [SUFFIX] [apply]
#%
#% Examples:
#%
#%   Provide a PR number. Defaults to a dry-run.
#%   ${THIS_FILE} pr-0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} pr-0 apply
#%

# Source and destination
#
IMG_SOURCE="docker-registry.default.svc:5000/${PROJ_TOOLS}/${NAME_APP}-${SUFFIX}:latest"
IMG_DEST="${NAME_APP}-${TAG_PROD}"

# Import to new image and retag, leaving the original tag in
#
OC_IMG_IMPORT="oc -n ${PROJ_TOOLS} import-image ${IMG_DEST}:${SUFFIX} --from=${IMG_SOURCE} --confirm"
OC_IMG_RETAG="oc -n ${PROJ_TOOLS} tag ${IMG_DEST}:${SUFFIX} ${IMG_DEST}:${TAG_PROD}"

# Execute commands
#
if [ "${APPLY}" ]; then
	eval "${OC_IMG_IMPORT}"
	eval "${OC_IMG_RETAG}"
fi

# Provide oc command instruction
#
display_helper "${OC_IMG_IMPORT}" "${OC_IMG_RETAG}"
