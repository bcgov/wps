#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% GHCR Image Promotion Helper
#%
#%   Promotes a PR-tagged image on GHCR to a "prod" tag, via a registry-side copy
#%   (no rebuild). Requires the caller to already be logged into ghcr.io
#%   (docker/podman) with push access.
#%
#%   If the PR image doesn't exist on GHCR (e.g. this package wasn't changed in this
#%   PR, so nothing was built), this leaves the existing "prod" tag alone and exits
#%   0 -- there was nothing to promote, which is an expected outcome, not a failure.
#%   Any non-zero exit means the promotion was attempted and failed (registry/auth/
#%   network error), and should not be treated as tolerable.
#%
#%   Prints the resulting image reference to stdout as the only stdout output, so
#%   callers can capture it via command substitution:
#%
#%       IMAGE=$(PACKAGE=wps-weather bash oc_promote_gh.sh ${SUFFIX} apply)
#%
#% Usage:
#%
#%    PACKAGE=[package] ${THIS_FILE} [SUFFIX] [apply]
#%
#% Examples:
#%
#%   PACKAGE=wps-weather ${THIS_FILE} pr-123 apply
#%

PACKAGE="${PACKAGE:?PACKAGE must be set, e.g. PACKAGE=wps-weather}"
GH_ORG="${GH_ORG:-bcgov}"
GH_REPO="${GH_REPO:-wps}"

PR_IMAGE="ghcr.io/${GH_ORG}/${GH_REPO}/${PACKAGE}:${SUFFIX}"
PROD_IMAGE="ghcr.io/${GH_ORG}/${GH_REPO}/${PACKAGE}:${TAG_PROD}"

if ! docker manifest inspect "${PR_IMAGE}" >/dev/null 2>&1; then
    echo "GHCR image ${PR_IMAGE} not found -- nothing to promote." >&2
    exit 0
fi

if [ "${APPLY}" ]; then
    echo "Promoting GHCR image ${PR_IMAGE} -> ${PROD_IMAGE}" >&2
    if ! docker buildx imagetools create --tag "${PROD_IMAGE}" "${PR_IMAGE}" >&2; then
        echo "ERROR: failed to promote ${PR_IMAGE} -> ${PROD_IMAGE}" >&2
        exit 1
    fi
else
    echo "Dry-run: would promote ${PR_IMAGE} -> ${PROD_IMAGE}" >&2
fi

echo "${PROD_IMAGE}"
