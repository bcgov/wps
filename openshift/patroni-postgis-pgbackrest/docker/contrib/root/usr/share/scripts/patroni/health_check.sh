#!/usr/bin/env bash
set -Eeu
set -o pipefail

# check for disk space. Fails if usage hits above 90%
df "${PATRONI_POSTGRESQL_DATA_DIR:-/home/postgres/pgdata}" --output=pcent | tail -n 1 | awk '{if ($1+0 > 90) exit 1; else exit 0;}'

pg_isready -q && patronictl list --format=json | jq -e ".[] | select(.Member == \"$(hostname)\" and .State == \"running\")"
