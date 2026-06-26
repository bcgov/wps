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

echo "=== Metabase User Restore ==="
echo ""

find_db_pod
ensure_restore_pod "$BACKUP_IMAGE"
select_and_download_backup "$TMP_DIR"

echo ""
read -rp "User IDs to restore (space-separated): " USER_IDS_STR
read -ra USER_IDS <<< "$USER_IDS_STR"

read -rp "Clear passwords so users must reset via 'Forgot password'? [y/N]: " RESET_PW
RESET_FLAG=""
if [[ "${RESET_PW,,}" == "y" ]]; then
  RESET_FLAG="--reset-password"
fi

RESTORE_SQL="$TMP_DIR/metabase_user_restore.sql"
echo ""
echo "Generating restore SQL..."
python3 "$SCRIPT_DIR/metabase_user_restore_extract.py" \
  "$LOCAL_SQL" "${USER_IDS[@]}" $RESET_FLAG --output "$RESTORE_SQL"

apply_restore_sql "$RESTORE_SQL" "$SCRIPT_DIR/last_user_restore.sql"

echo ""
echo "Done. Users restored — they can now log in or use 'Forgot password' if passwords were cleared."
