#!/bin/sh -l
#
#% SFMS Daily FWI APS gateway config render helper
#%
#%   Render the declarative APS gateway config for a specific environment.
#%
#% Usage:
#%
#%   PROJECT_NAMESPACE=<namespace> APS_NAMESPACE=<aps-namespace> FWI_HOST=<host> \
#%   ${THIS_FILE} [SUFFIX] [OUTPUT_PATH]
#%
#% Examples:
#%
#%   PROJECT_NAMESPACE=e1e498-dev APS_NAMESPACE=dev FWI_HOST=sfms-fwi-pr-0.api.gov.bc.ca \
#%   ${THIS_FILE} pr-0
#%
#%   PROJECT_NAMESPACE=e1e498-prod APS_NAMESPACE=gw-313f6 FWI_HOST=sfms-fwi.api.gov.bc.ca \
#%   ${THIS_FILE} prod /tmp/sfms-fwi-gw-config-prod.yaml
#

set -euo pipefail
IFS=$'\n\t'

THIS_FILE="$(dirname "$0")/$(basename "$0")"
SUFFIX="${1:-}"
OUTPUT_PATH="${2:-$(dirname "$0")/../aps/rendered/sfms-fwi-gw-config-${SUFFIX}.yaml}"
TEMPLATE_PATH="${TEMPLATE_PATH:-$(dirname "$0")/../aps/sfms-fwi-gw-config.yaml}"

[ -n "${SUFFIX}" ] || {
	sed -n \
		-e "s|\${THIS_FILE}|${THIS_FILE}|g" \
		-e 's|^#%||p' \
		"${THIS_FILE}"
	exit
}

[ -n "${PROJECT_NAMESPACE:-}" ] || {
	echo "PROJECT_NAMESPACE is required" >&2
	exit 1
}

[ -n "${APS_NAMESPACE:-}" ] || {
	echo "APS_NAMESPACE is required" >&2
	exit 1
}

[ -n "${FWI_HOST:-}" ] || {
	echo "FWI_HOST is required" >&2
	exit 1
}

[ -n "$(command -v envsubst)" ] || {
	echo "envsubst is required" >&2
	exit 1
}

FWI_SERVICE_NAME="${FWI_SERVICE_NAME:-psu-sfms-fwi-${SUFFIX}}"

mkdir -p "$(dirname "${OUTPUT_PATH}")"

export SUFFIX
export PROJECT_NAMESPACE
export APS_NAMESPACE
export FWI_HOST
export FWI_SERVICE_NAME

envsubst \
	'${SUFFIX} ${PROJECT_NAMESPACE} ${APS_NAMESPACE} ${FWI_HOST} ${FWI_SERVICE_NAME}' \
	<"${TEMPLATE_PATH}" >"${OUTPUT_PATH}"

echo "${OUTPUT_PATH}"
