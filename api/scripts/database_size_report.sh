#!/usr/bin/env bash

#   Runs a database table size query for all tables. 
#   Query is from: https://wiki.postgresql.org/wiki/Disk_Usage (General Table Size Information)
#
# Usage:
#
#   PROJECT=OPENSHIFT_PROJECT_NAME POD=OPENSHIFT_POD DATABASE=POSTGRESQL_DATABASE ${THIS_FILE}
#
# Example:
#
#   e.g. PROJECT=e1e498-prod POD=patroni-wps-prod-2 DATABASE=wps ./database_size_report.sh

set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"

source "$SCRIPT_DIR/common_oc_checks.sh"

# From https://wiki.postgresql.org/wiki/Disk_Usage
SIZE_REPORT_QUERY="SELECT *, pg_size_pretty(total_bytes) AS total
    , pg_size_pretty(index_bytes) AS index
    , pg_size_pretty(toast_bytes) AS toast
    , pg_size_pretty(table_bytes) AS table
  FROM (
  SELECT *, total_bytes-index_bytes-coalesce(toast_bytes,0) AS table_bytes FROM (
      SELECT c.oid,nspname AS table_schema, relname AS table_name
              , c.reltuples AS row_estimate
              , pg_total_relation_size(c.oid) AS total_bytes
              , pg_indexes_size(c.oid) AS index_bytes
              , pg_total_relation_size(reltoastrelid) AS toast_bytes
          FROM pg_class c
          LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE relkind = 'r'
  ) a
) a;"
SIZE_REPORT_COMMAND="${RSH} psql ${DATABASE} -c \"${SIZE_REPORT_QUERY}\""
eval "${SIZE_REPORT_COMMAND}"
