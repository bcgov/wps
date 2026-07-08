#!/bin/sh -l
#
#% SFMS Daily FWI APS dataset and product resource render helper
#%
#%   Render DraftDataset and Product YAML for a specific environment.
#%   Output files are written to OUTPUT_DIR (default: openshift/aps/rendered/).
#%
#% Usage:
#%
#%   ${THIS_FILE} [SUFFIX] [OUTPUT_DIR]
#%
#% Examples:
#%
#%   ${THIS_FILE} pr-123
#%   ${THIS_FILE} prod /tmp/rendered
#

set -euo pipefail
IFS=$'\n\t'

THIS_FILE="$(dirname "$0")/$(basename "$0")"
SUFFIX="${1:-}"
OUTPUT_DIR="${2:-$(dirname "$0")/../aps/rendered}"

[ -n "${SUFFIX}" ] || {
	sed -n \
		-e "s|\${THIS_FILE}|${THIS_FILE}|g" \
		-e 's|^#%||p' \
		"${THIS_FILE}"
	exit
}

[ -n "$(command -v envsubst)" ] || {
	echo "envsubst is required" >&2
	exit 1
}

DATASET_TEMPLATE="${DATASET_TEMPLATE:-$(dirname "$0")/../aps/sfms-fwi-dataset.yaml}"
PRODUCT_TEMPLATE="${PRODUCT_TEMPLATE:-$(dirname "$0")/../aps/sfms-fwi-product.yaml}"

# DISPLAY_SUFFIX is empty for prod so directory titles stay clean.
# ENV_TIER is the APS product environment tier shown to consumers (fixed set: dev/test/sandbox/prod).
# DOCS_HOST is plain descriptive text embedded in the dataset notes' markdown link, not a
# Kong route hosts: field -- unlike GW_HOST (see aps-publish/action.yml), nothing on the
# platform auto-remaps it, so it must be computed here as the final, already-test-ified
# public domain: the production-style hostname with every dot replaced by a dash, then
# .test.api.gov.bc.ca appended -- confirmed against a real working /api/docs URL.
if [ "${SUFFIX}" = "prod" ]; then
	DISPLAY_SUFFIX=""
	ENV_TIER="prod"
	DOCS_HOST="psu.api.gov.bc.ca"
else
	DISPLAY_SUFFIX=" (${SUFFIX})"
	ENV_TIER="dev"
	PROD_STYLE_HOST="psu-${SUFFIX}.api.gov.bc.ca"
	DOCS_HOST="$(echo "${PROD_STYLE_HOST}" | tr '.' '-').test.api.gov.bc.ca"
fi

mkdir -p "${OUTPUT_DIR}"

DATASET_OUT="${OUTPUT_DIR}/sfms-fwi-dataset-${SUFFIX}.yaml"
PRODUCT_OUT="${OUTPUT_DIR}/sfms-fwi-product-${SUFFIX}.yaml"

export SUFFIX
export DISPLAY_SUFFIX
export ENV_TIER
export DOCS_HOST

envsubst '${SUFFIX} ${DISPLAY_SUFFIX} ${DOCS_HOST}' <"${DATASET_TEMPLATE}" >"${DATASET_OUT}"
envsubst '${SUFFIX} ${DISPLAY_SUFFIX} ${ENV_TIER}' <"${PRODUCT_TEMPLATE}" >"${PRODUCT_OUT}"

echo "${DATASET_OUT}"
echo "${PRODUCT_OUT}"
