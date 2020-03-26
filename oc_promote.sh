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

# Delete previous prod label
#
OC_IMG_DELETE="oc -n ${PROJ_TOOLS} delete istag ${NAME_APP}:${TAG_PROD}"

# Full copy imagestream into prod tag (not a pointer)
#
SOURCE_IMG="docker-registry.default.svc:5000/${PROJ_TOOLS}/${NAME_APP}:${SUFFIX}"
OC_IMG_IMPORT="oc -n ${PROJ_TOOLS} import-image ${NAME_APP}:${TAG_PROD} --from=${SOURCE_IMG}"

# Execute commands
#
if [ "${APPLY}" ]; then
	eval "${OC_IMG_DELETE}"
	eval "${OC_IMG_IMPORT}"
fi

# Provide oc command instruction
#
display_helper "${OC_IMG_DELETE}" "${OC_IMG_IMPORT}"
