#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=metabase_restore_common.sh
source "$SCRIPT_DIR/metabase_restore_common.sh"

usage() {
  echo "Usage: $0 --namespace NS --db-name DB --backup-pvc PVC --restore-pod POD"
  echo ""
  echo "Options:"
  echo "  --namespace    OpenShift namespace"
  echo "  --db-name      Metabase database name"
  echo "  --backup-pvc   PVC name containing backups"
  echo "  --restore-pod  Name for the temporary restore pod"
  return 1
}

parse_common_args "$@" || usage

BACKUP_IMAGE="docker.io/bcgovimages/backup-container:latest"
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

echo "=== Metabase Dashboard Restore ==="
echo ""

find_db_pod
ensure_restore_pod "$BACKUP_IMAGE"
select_and_download_backup "$TMP_DIR"

echo ""
read -rp "Dashboard IDs to restore (space-separated): " DASHBOARD_IDS_STR
read -ra DASHBOARD_IDS <<< "$DASHBOARD_IDS_STR"

read -rp "Assign ownership to Metabase user ID: " OWNER_ID

RESTORE_SQL="$TMP_DIR/metabase_restore.sql"
echo ""
echo "Generating restore SQL..."
python3 "$SCRIPT_DIR/metabase_dashboard_restore_extract.py" \
  "$LOCAL_SQL" "${DASHBOARD_IDS[@]}" --owner "$OWNER_ID" --output "$RESTORE_SQL"

apply_restore_sql "$RESTORE_SQL" "$SCRIPT_DIR/last_dashboard_restore.sql"

echo ""
echo "Done. Check Metabase to verify the dashboards are restored."
