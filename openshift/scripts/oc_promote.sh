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
IMG_SOURCE="${IMAGE_REGISTRY}/${PROJ_TOOLS}/${NAME_APP}-${SUFFIX}:${SUFFIX}"
IMG_DEST="${NAME_APP}-${TAG_PROD}"

# Import to new image and retag, leaving the original tag in
#
OC_IMG_IMPORT="oc -n ${PROJ_TOOLS} import-image ${IMG_DEST}:${SUFFIX} --from=${IMG_SOURCE} --confirm"
OC_IMG_RETAG="oc -n ${PROJ_TOOLS} tag ${IMG_DEST}:${SUFFIX} ${IMG_DEST}:${TAG_PROD}"

# Get list of images to prune.
#
TAGS=$(oc -n ${PROJ_TOOLS} get is/${IMG_DEST} --output=json | python $(dirname ${0})/prune.py)
declare -a OC_IMG_PRUNE=()
for TAG in ${TAGS}; do
	OC_IMG_PRUNE+=("oc -n ${PROJ_TOOLS} tag -d ${IMG_DEST}:${TAG}")
done

# Execute commands
#
if [ "${APPLY}" ]; then
	eval "${OC_IMG_IMPORT}"
	eval "${OC_IMG_RETAG}"

	for PRUNE in "${OC_IMG_PRUNE[@]}"; do
		eval "${PRUNE}"
	done
fi

# Provide oc command instruction
#
display_helper "${OC_IMG_IMPORT}" "${OC_IMG_RETAG}" "${OC_IMG_PRUNE[@]}"
