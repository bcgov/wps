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

IMG_DEST="${APP_NAME}-${MODULE_NAME}-${TAG_PROD}"
PR_IMAGE="${APP_NAME}-${MODULE_NAME}-${SUFFIX}:${SUFFIX}"
PROD_IMAGE="${IMG_DEST}:${SUFFIX}"
PROD_TAG_IMAGE="${IMG_DEST}:${TAG_PROD}"

# Get list of images to prune.
#
TAGS=$(oc -n ${PROJ_TOOLS} get is/${IMG_DEST} --output=json --ignore-not-found=true | python $(dirname ${0})/prune.py)
declare -a PRUNE_TAGS=()
for TAG in ${TAGS}; do
	PRUNE_TAGS+=("${IMG_DEST}:${TAG}")
done

# Tag the PR image into the prod stream as both its PR tag and the prod tag, then delete the
# pruned tags, one oc call each. oc tag fails if the PR image doesn't exist.
#
OC_TAG="oc -n ${PROJ_TOOLS} tag ${PR_IMAGE} ${PROD_IMAGE} ${PROD_TAG_IMAGE}"
OC_PRUNE=""
# (printf joins with spaces; IFS is newline/tab here, so ${PRUNE_TAGS[*]} would join with newlines)
[ "${#PRUNE_TAGS[@]}" -eq 0 ] || OC_PRUNE="oc -n ${PROJ_TOOLS} tag -d $(printf '%s ' "${PRUNE_TAGS[@]}")"

if [ "${APPLY}" ]; then
	eval "${OC_TAG}"
	[ -z "${OC_PRUNE}" ] || eval "${OC_PRUNE}"
fi

# Provide oc command instruction
#
display_helper "${OC_TAG}" ${OC_PRUNE:+"${OC_PRUNE}"}
