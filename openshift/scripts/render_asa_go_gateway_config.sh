#!/bin/sh -l
#
#% ASA Go APS gateway config render helper
#%
#%   Render the declarative APS gateway config for a specific environment.
#%
#% Usage:
#%
#%   PROJECT_NAMESPACE=<namespace> APS_NAMESPACE=<aps-namespace> ASA_GO_HOST=<host> \
#%   ${THIS_FILE} [SUFFIX] [OUTPUT_PATH]
#%
#% Examples:
#%
#%   PROJECT_NAMESPACE=e1e498-dev APS_NAMESPACE=dev ASA_GO_HOST=asa-go-pr-0.example.ca \
#%   ${THIS_FILE} pr-0
#%
#%   PROJECT_NAMESPACE=e1e498-prod APS_NAMESPACE=prod ASA_GO_HOST=asa-go.example.ca \
#%   ${THIS_FILE} prod /tmp/asa-go-gw-config-prod.yaml
#

set -euo pipefail
IFS=$'\n\t'

THIS_FILE="$(dirname "$0")/$(basename "$0")"
SUFFIX="${1:-}"
OUTPUT_PATH="${2:-$(dirname "$0")/../aps/rendered/asa-go-gw-config-${SUFFIX}.yaml}"
TEMPLATE_PATH="${TEMPLATE_PATH:-$(dirname "$0")/../aps/asa-go-gw-config.yaml}"

[ -n "${SUFFIX}" ] || {
	# print the script header as usage text when no suffix is provided.
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

[ -n "${ASA_GO_HOST:-}" ] || {
	echo "ASA_GO_HOST is required" >&2
	exit 1
}

[ -n "$(command -v envsubst)" ] || {
	echo "envsubst is required" >&2
	exit 1
}

# keep the defaults here so the template can be rendered with only the required inputs.
ASA_GO_SERVICE_NAME="${ASA_GO_SERVICE_NAME:-psu-asa-${SUFFIX}}"

mkdir -p "$(dirname "${OUTPUT_PATH}")"

export SUFFIX
export PROJECT_NAMESPACE
export APS_NAMESPACE
export ASA_GO_HOST
export ASA_GO_SERVICE_NAME

# only substitute the placeholders this template owns, so unrelated ${...} text is left alone.
envsubst \
	'${SUFFIX} ${PROJECT_NAMESPACE} ${APS_NAMESPACE} ${ASA_GO_HOST} ${ASA_GO_SERVICE_NAME}' \
	<"${TEMPLATE_PATH}" >"${OUTPUT_PATH}"

echo "${OUTPUT_PATH}"
