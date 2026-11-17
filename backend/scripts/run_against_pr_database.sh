#!/usr/bin/env bash
#
# Run a backend script against a PR deployment's Postgres and object store tables.
#
# Opens a port-forward to the PR's database, points the POSTGRES_* settings and SUFFIX at that
# deployment, runs the script, and closes the port-forward afterwards. Object store settings
# still come from your .env, which must point at the dev bucket.
#
# Usage:
#
#   scripts/run_against_pr_database.sh SUFFIX SCRIPT [ARGS...]
#
# Example, from ./backend:
#
#   scripts/run_against_pr_database.sh pr-6073 scripts/morecast_by_time_parity_check.py --days-back 3
#
# You must be logged in with `oc`.
#
# From a git worktree with no .venv or .env of its own, set BACKEND_DIR to the backend directory
# of a checkout that has them. The script then runs in that environment, with wps-weather-data
# taken from this worktree:
#
#   BACKEND_DIR=~/projects/wps/backend scripts/run_against_pr_database.sh pr-6073 scripts/...
#
# Only scripts whose wps_shared imports exist on that checkout's branch work this way.
#
# Optional settings: PROJ_DEV (namespace), CRUNCHY_NAME, LOCAL_PORT, POSTGRES_DATABASE.

set -euo pipefail

if [ "$#" -lt 2 ]; then
    sed -n '3,28p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
fi

SUFFIX="$1"
SCRIPT="$2"
shift 2

THIS_BACKEND="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="${BACKEND_DIR:-${THIS_BACKEND}}"
NAMESPACE="${PROJ_DEV:-e1e498-dev}"
CLUSTER="${CRUNCHY_NAME:-wps-crunchydb-16}-${SUFFIX}"
SECRET="${CLUSTER}-pguser-${CLUSTER}"
LOCAL_PORT="${LOCAL_PORT:-5433}"

# A script path is relative to this backend directory unless it is absolute.
case "${SCRIPT}" in
    /*) ;;
    *) SCRIPT="${THIS_BACKEND}/${SCRIPT}" ;;
esac
[ -f "${SCRIPT}" ] || { echo "No such script: ${SCRIPT}" >&2; exit 2; }

if [ ! -d "${BACKEND_DIR}/.venv" ]; then
    echo "No .venv in ${BACKEND_DIR}." >&2
    echo "Set BACKEND_DIR to the backend directory of a checkout that has one." >&2
    exit 2
fi

port_is_open() {
    (exec 3<>"/dev/tcp/127.0.0.1/${LOCAL_PORT}") 2>/dev/null
}

if port_is_open; then
    echo "Local port ${LOCAL_PORT} is already in use. Set LOCAL_PORT to a free port." >&2
    exit 2
fi

secret_value() {
    oc -n "${NAMESPACE}" get secret "${SECRET}" -o "jsonpath={.data.$1}" | base64 -d
}

FORWARD_PID=""
FORWARD_LOG="$(mktemp "${TMPDIR:-/tmp}/port-forward.XXXXXX")"
cleanup() {
    if [ -n "${FORWARD_PID}" ]; then
        kill "${FORWARD_PID}" 2>/dev/null || true
        # Waiting on it stops the shell printing a "Terminated" notice.
        wait "${FORWARD_PID}" 2>/dev/null || true
    fi
    rm -f "${FORWARD_LOG}"
}
trap cleanup EXIT

# Forward to a target and wait for the local port to open. Returns 1 if it never does.
forward_to() {
    oc -n "${NAMESPACE}" port-forward "$1" "${LOCAL_PORT}:5432" >"${FORWARD_LOG}" 2>&1 &
    FORWARD_PID=$!
    for _ in $(seq 1 30); do
        port_is_open && return 0
        kill -0 "${FORWARD_PID}" 2>/dev/null || break
        sleep 0.5
    done
    kill "${FORWARD_PID}" 2>/dev/null || true
    FORWARD_PID=""
    return 1
}

echo "Forwarding localhost:${LOCAL_PORT} to ${CLUSTER} in ${NAMESPACE}"
if ! forward_to "svc/${CLUSTER}-pgbouncer"; then
    echo "Could not forward to pgbouncer, trying the primary pod"
    PRIMARY_POD="$(oc -n "${NAMESPACE}" get pod -o name \
        -l "postgres-operator.crunchydata.com/cluster=${CLUSTER},postgres-operator.crunchydata.com/role=master")"
    if [ -z "${PRIMARY_POD}" ] || ! forward_to "${PRIMARY_POD}"; then
        echo "Could not open a port-forward to ${CLUSTER}:" >&2
        cat "${FORWARD_LOG}" >&2
        exit 1
    fi
fi

POSTGRES_READ_USER="$(secret_value user)"
POSTGRES_PASSWORD="$(secret_value password)"
export POSTGRES_READ_USER POSTGRES_PASSWORD
export POSTGRES_WRITE_USER="${POSTGRES_READ_USER}"
export POSTGRES_READ_HOST=localhost POSTGRES_WRITE_HOST=localhost
export POSTGRES_PORT="${LOCAL_PORT}"
export POSTGRES_DATABASE="${POSTGRES_DATABASE:-wps}"
export SUFFIX

cd "${BACKEND_DIR}"
if [ "${BACKEND_DIR}" = "${THIS_BACKEND}" ]; then
    uv run python "${SCRIPT}" "$@"
else
    # Borrowing another checkout's environment: take wps-weather-data from this worktree and
    # add the libraries it needs, which that checkout may not have installed.
    export PYTHONPATH="${THIS_BACKEND}/packages/wps-weather-data/src${PYTHONPATH:+:${PYTHONPATH}}"
    uv run --with "deltalake>=1.6.6,<2" --with "pyarrow>=26,<27" python "${SCRIPT}" "$@"
fi
