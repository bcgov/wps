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

tag_if_exists_or_fail() {
    SOURCE="$1"
    DEST="$2"

    if oc -n "${PROJ_TOOLS}" get istag "${SOURCE}" >/dev/null 2>&1; then
        oc -n "${PROJ_TOOLS}" tag "${SOURCE}" "${DEST}"
    else
		# We don't always build the weather image if nothing has changed, so allow it to be missing.
        if [ "${MODULE_NAME}" = "weather" ]; then
            echo "Image ${SOURCE} not found (allowed for weather module) — skipping."
        else
            echo "ERROR: Image ${SOURCE} not found."
            exit 1
        fi
    fi
}

IMG_DEST="${APP_NAME}-${MODULE_NAME}-${TAG_PROD}"
PR_IMAGE="${APP_NAME}-${MODULE_NAME}-${SUFFIX}:${SUFFIX}"
PROD_IMAGE="${IMG_DEST}:${SUFFIX}"
PROD_TAG_IMAGE="${IMG_DEST}:${TAG_PROD}"

# Get list of images to prune.
#
TAGS=$(oc -n ${PROJ_TOOLS} get is/${IMG_DEST} --output=json --ignore-not-found=true | python $(dirname ${0})/prune.py)
declare -a OC_IMG_PRUNE=()
for TAG in ${TAGS}; do
	OC_IMG_PRUNE+=("oc -n ${PROJ_TOOLS} tag -d ${IMG_DEST}:${TAG}")
done


# Promote images
if [ "${APPLY}" ]; then
    # Tag PR image to prod stream
    tag_if_exists_or_fail "${PR_IMAGE}" "${PROD_IMAGE}"

    # Tag prod stream to prod latest
    tag_if_exists_or_fail "${PROD_IMAGE}" "${PROD_TAG_IMAGE}"

	if [ "${#OC_IMG_PRUNE[@]}" -gt 0 ]; then
		for PRUNE in "${OC_IMG_PRUNE[@]}"; do
			eval "${PRUNE}"
		done
	fi
fi

# Provide oc command instruction
#
DISPLAY_STREAM="oc -n ${PROJ_TOOLS} tag ${PR_IMAGE} ${PROD_IMAGE}"
DISPLAY_LATEST="oc -n ${PROJ_TOOLS} tag ${PROD_IMAGE} ${PROD_TAG_IMAGE}"

if [ "${#OC_IMG_PRUNE[@]}" -gt 0 ]; then
    display_helper "${DISPLAY_STREAM}" "${DISPLAY_LATEST}" "${OC_IMG_PRUNE[@]}"
else
    display_helper "${DISPLAY_STREAM}" "${DISPLAY_LATEST}"
fi
