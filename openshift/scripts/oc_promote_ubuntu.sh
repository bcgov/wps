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
IMAGE_REGISTRY="${IMAGE_REGISTRY:-'image-registry.openshift-image-registry.svc:5000'}"
IMG_SOURCE="${IMAGE_REGISTRY}/${PROJ_TOOLS}/${NAME_APP}-ubuntu-${SUFFIX}:${SUFFIX}"
IMG_DEST="${NAME_APP}-ubuntu-${TAG_PROD}"

# Import to new image and retag, leaving the original tag in
#
# TODO: importing the image in this way, results in previous tags persisting - we need to get rid of them!
#
# lets say we have wps-pr-1564:pr-1564, and we want to promote it to production.
# keep in mind, that we're going to delete wps-pr-1564 when we clean up that PR, so we need to copy it.
# we import it into wps-prod as wps-prod:pr-1564
# it's now safe to delete wps-pr-1564:pr-1564 - we have a copy.
# we can no tag this new image as our prod tag, so we mark it as wps-prod:prod
# but hold - we can't keep all these old tags forever!
#
#  oc get is/wps-pr-1561 --output=json
#  oc get is/wps-pr-1561 -o jsonpath='{.status.tags[*].items[0].created}'
#
#
# TAG_N
# TAG_N-1 = 
# TAG_N-2 = TAG_N-1
# TAG_N-3 = TAG_N-2
# e.g. wps-ubuntu-ubuntu-prod:pr-123 --from=image-registry.openshift-image-registry.svc:5000/e1e498-tools/wps-ubuntu-ubuntu-pr-123:pr-123
OC_IMG_IMPORT="oc -n ${PROJ_TOOLS} import-image ${IMG_DEST}:${SUFFIX} --from=${IMG_SOURCE} --confirm"
# e.g. wps-ubuntu-ubuntu-prod:pr-123 image-registry.openshift-image-registry.svc:5000/e1e498-tools/wps-ubuntu-ubuntu-pr-123:prod
OC_IMG_RETAG="oc -n ${PROJ_TOOLS} tag ${IMG_DEST}:${SUFFIX} ${IMG_DEST}:${TAG_PROD}"
# TODO: now get rid of the source image!

# Execute commands
#
if [ "${APPLY}" ]; then
	eval "${OC_IMG_IMPORT}"
	eval "${OC_IMG_RETAG}"
fi

# Provide oc command instruction
#
display_helper "${OC_IMG_IMPORT}" "${OC_IMG_RETAG}"
