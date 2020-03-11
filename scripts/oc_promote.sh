#!/bin/bash
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift ImageStreamTag Promotion Helper
#%
#%   Promote a passing imagestreamtag by labeling is as prod.
#%
#% Usage:
#%
#%   ${THIS_FILE} [PR_NUMBER] [apply]
#%
#% Examples:
#%
#%   Provide a PR number. Defaults to a dry-run.
#%   ${THIS_FILE} 0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} 0 apply
#%

# Vars
#
SUFFIX_FROM="pr-${PR_NO}"
SUFFIX_TO="$(echo ${PROJ_PROD} | cut -d'-' -f2)"
# The tag for labeling the most recent imagestreatag as PROD
TAG_TO="${NAME}:${SUFFIX_TO}"
# Long name for the DEV imagestreamtag to import to PROD
SOURCE_IMG="docker-registry.default.svc:5000/${PROJ_TOOLS}/${NAME}:${SUFFIX_FROM}"

# Delete previous prod label
OC_IMG_DELETE="oc -n ${PROJ_TOOLS} delete istag ${TAG_TO}"
# Full copy imagestream into prod tag (not a pointer)
OC_IMG_IMPORT="oc -n ${PROJ_TOOLS} import-image ${TAG_TO} --from=${SOURCE_IMG}"

# Process commands
#
if [ "${APPLY}" ]; then
	# Only delete the imagestreamtag if applying
	eval "${OC_IMG_DELETE}"
	eval "${OC_IMG_IMPORT}"
fi

# Provide oc command instruction
#
display_helper "${OC_IMG_DELETE}" "${OC_IMG_IMPORT}"
