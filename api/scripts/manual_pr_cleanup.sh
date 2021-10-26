#!/bin/bash
#%
#% Manually cleanup PR resources
#% PR is of the form "pr-<pr-number>"
#%
#% Usage:
#%
#%    ${THIS_FILE} [PR]


set -euo pipefail

CURRENT_DIR="$(dirname "$0")"
PR="$1"

PROJ_TARGET=e1e498-dev PROJ_TOOLS=e1e498-tools PROJ_DEV=e1e498-dev "../.$CURRENT_DIR/openshift/scripts/oc_cleanup.sh" $PR apply
PROJ_TARGET=e1e498-dev PROJ_TOOLS=e1e498-tools PROJ_DEV=e1e498-dev  "../.$CURRENT_DIR/openshift/scripts/oc_cleanup_db.sh" $PR apply
PROJ_TARGET=e1e498-test PROJ_TOOLS=e1e498-tools PROJ_DEV=e1e498-dev  "../.$CURRENT_DIR/openshift/scripts/oc_cleanup.sh" $PR apply
PROJ_TARGET=e1e498-test PROJ_TOOLS=e1e498-tools PROJ_DEV=e1e498-dev  "../.$CURRENT_DIR/openshift/scripts/oc_cleanup_db.sh" $PR apply
# TODO S3 bucket cleanup
