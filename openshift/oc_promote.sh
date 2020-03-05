#!/bin/bash
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift DEV-PROD ImageStreamTag Promotion Helper
#%
#%   Promote a passing imagestreamtag from DEV to PROD environments.
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
SUFFIX_DEV="pr-${PR_NO}"
SUFFIX_PROD="$(echo ${PROJ_PROD} | cut -d'-' -f2)"
# The tag for the imagestream being imported from DEV to PROD
TAG_IMPORT="${NAME}:${SUFFIX_DEV}"
# The tag for labeling the most recent imagestreatag as PROD
TAG_CURRENT="${NAME}:${SUFFIX_PROD}"
# Long name for the DEV imagestreamtag to import to PROD
SOURCE_IMG="docker-registry.default.svc:5000/${PROJ_TOOLS}/${NAME}-${SUFFIX_DEV}-s2i:latest"

# Create OpenShift commands to consume
#
# Import DEV image into an imagestream in PROD namespace
OC_IMG_IMPORT="oc -n ${PROJ_TOOLS} import-image ${TAG_IMPORT} --from=${SOURCE_IMG}"
# Apply the PROD label to that imagestreamtag
OC_IMG_TAG="oc -n ${PROJ_TOOLS} tag ${TAG_IMPORT} ${TAG_CURRENT}"
# Process a template (mostly variable substition)
#
OC_PROCESS="oc -n ${PROJ_TOOLS} process -f ${PATH_DC} -p NAME=${NAME} -p SUFFIX=${SUFFIX_DEV}"
# Apply a template (can use --dry-run)
OC_APPLY="oc -n ${PROJ_PROD} apply -f -"
# Pipe the first command into the second
OC_COMMAND="${OC_PROCESS} | ${OC_APPLY}"

# Process commands
#
if [ "${APPLY}" ]; then
	# Only delete the imagestreamtag if applying
	eval "${OC_IMG_IMPORT}"
	eval "${OC_IMG_TAG}"
else
	OC_COMMAND+=" --dry-run"
fi
eval "${OC_COMMAND}"

# Provide oc command instruction
#
display_helper "${OC_IMG_IMPORT}" "${OC_IMG_TAG}" "${OC_COMMAND}"
