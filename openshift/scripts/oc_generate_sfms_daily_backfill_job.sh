#!/usr/bin/env bash
#
# Generate a one-off SFMS daily backfill Job from the deployed actuals CronJob.
#
# Usage:
#   PROJ_TARGET=e1e498-prod \
#   START_DATE=2026-06-25 \
#   END_DATE=2026-06-27 \
#   JOB_NAME=sfms-daily-backfill-20260625-to-20260627 \
#   bash openshift/scripts/oc_generate_sfms_daily_backfill_job.sh > /tmp/sfms-backfill.yaml
#
# Optional:
#   CRONJOB=cronjob/sfms-daily-actuals-wps-prod  # use an explicit source CronJob
#   CONTINUE_ON_ERROR=true                       # add --continue-on-error
#   bash openshift/scripts/oc_generate_sfms_daily_backfill_job.sh prod

set -euo pipefail
IFS=$'\n\t'

SUFFIX="${1:-}"
PROJ_TARGET="${PROJ_TARGET:-e1e498-dev}"
CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-false}"

usage() {
    cat >&2 <<EOF
Usage:
  PROJ_TARGET=e1e498-prod START_DATE=YYYY-MM-DD END_DATE=YYYY-MM-DD \\
    bash openshift/scripts/oc_generate_sfms_daily_backfill_job.sh > /tmp/sfms-backfill.yaml

Required environment variables:
  START_DATE   Inclusive first date to regenerate, YYYY-MM-DD.
  END_DATE     Inclusive last date to regenerate, YYYY-MM-DD.

Optional environment variables:
  PROJ_TARGET         OpenShift namespace. Defaults to e1e498-dev.
  CRONJOB             Explicit source CronJob, e.g. cronjob/sfms-daily-actuals-wps-prod.
  JOB_NAME            Output Job name. Defaults to sfms-daily-backfill-START_DATE-to-END_DATE.
  CONTINUE_ON_ERROR   true to add --continue-on-error. Defaults to false.

Optional positional argument:
  SUFFIX              Filter the discovered sfms-daily-actuals CronJob name.
EOF
}

fail() {
    echo "error: $*" >&2
    exit 1
}

validate_date() {
    local value="$1"
    [[ "${value}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || fail "date must use YYYY-MM-DD: ${value}"
}

discover_cronjob() {
    local pattern="sfms-daily-actuals"
    if [[ -n "${SUFFIX}" ]]; then
        pattern="${pattern}.*${SUFFIX}"
    fi

    oc -n "${PROJ_TARGET}" get cronjob -o name |
        grep "${pattern}" |
        head -1 ||
        true
}

require_oc_login() {
    oc whoami >/dev/null 2>&1 || fail "please verify oc login"
}

build_command_json() {
    local command_json
    command_json=$(
        printf '["uv","run","--package","wps-api","--no-sync","python","-m","app.jobs.sfms_daily_backfill","--start-date","%s","--end-date","%s"' \
            "${START_DATE}" \
            "${END_DATE}"
    )
    if [[ "${CONTINUE_ON_ERROR}" == "true" ]]; then
        command_json="${command_json},\"--continue-on-error\""
    fi
    printf '%s]' "${command_json}"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

[[ -n "${START_DATE:-}" ]] || {
    usage
    fail "START_DATE is required"
}
[[ -n "${END_DATE:-}" ]] || {
    usage
    fail "END_DATE is required"
}

validate_date "${START_DATE}"
validate_date "${END_DATE}"
[[ "${END_DATE}" > "${START_DATE}" || "${END_DATE}" == "${START_DATE}" ]] ||
    fail "END_DATE must be on or after START_DATE"
require_oc_login

START_ID="${START_DATE//-/}"
END_ID="${END_DATE//-/}"
JOB_NAME="${JOB_NAME:-sfms-daily-backfill-${START_ID}-to-${END_ID}}"
CRONJOB="${CRONJOB:-$(discover_cronjob)}"

[[ -n "${CRONJOB}" ]] || fail "could not find an sfms-daily-actuals CronJob in ${PROJ_TARGET}"

COMMAND_JSON="$(build_command_json)"
PATCH_JSON="[{\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/command\",\"value\":${COMMAND_JSON}}]"

oc -n "${PROJ_TARGET}" create job "${JOB_NAME}" \
    --from="${CRONJOB}" \
    --dry-run=client \
    -o yaml |
    oc -n "${PROJ_TARGET}" patch \
        --local \
        -f - \
        --type=json \
        -p "${PATCH_JSON}" \
        -o yaml
