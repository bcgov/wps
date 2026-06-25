#!/usr/bin/env bash
# Sourced by oc_restore_metabase_dashboards.sh and oc_restore_metabase_users.sh

parse_common_args() {
  NAMESPACE=""
  DB_NAME=""
  BACKUP_PVC=""
  RESTORE_POD=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --namespace)   NAMESPACE="$2";   shift 2 ;;
      --db-name)     DB_NAME="$2";     shift 2 ;;
      --backup-pvc)  BACKUP_PVC="$2";  shift 2 ;;
      --restore-pod) RESTORE_POD="$2"; shift 2 ;;
      --help|-h)     return 1 ;;
      *) echo "Unknown option: $1"; return 1 ;;
    esac
  done

  if [[ -z "$NAMESPACE" || -z "$DB_NAME" || -z "$BACKUP_PVC" || -z "$RESTORE_POD" ]]; then
    echo "ERROR: --namespace, --db-name, --backup-pvc, and --restore-pod are all required"
    return 1
  fi
}

find_db_pod() {
  echo "Finding database pod..."
  DB_POD=$(oc get pods -n "$NAMESPACE" --no-headers | grep "mb-database-prod" | grep Running | awk '{print $1}' | head -1)
  if [[ -z "$DB_POD" ]]; then
    echo "ERROR: No running mb-database-prod pod found in namespace $NAMESPACE"
    exit 1
  fi
  echo "  DB pod: $DB_POD"

  DB_USER=$(oc exec "$DB_POD" -n "$NAMESPACE" -- env 2>/dev/null | grep -iE "^POSTGRES_USER=|^PGUSER=" | cut -d= -f2 | head -1 || true)
  if [[ -z "$DB_USER" ]]; then
    read -rp "Enter DB username: " DB_USER
  fi
  echo "  DB user: $DB_USER"
}

ensure_restore_pod() {
  local image="$1"

  if oc get pod "$RESTORE_POD" -n "$NAMESPACE" &>/dev/null; then
    POD_PHASE=$(oc get pod "$RESTORE_POD" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
    if [[ "$POD_PHASE" != "Running" ]]; then
      echo "Removing stale restore pod ($POD_PHASE)..."
      oc delete pod "$RESTORE_POD" -n "$NAMESPACE" --wait=true
    fi
  fi

  if ! oc get pod "$RESTORE_POD" -n "$NAMESPACE" &>/dev/null; then
    echo "Creating restore pod..."
    oc apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: $RESTORE_POD
  namespace: $NAMESPACE
spec:
  restartPolicy: Never
  volumes:
  - name: backup
    persistentVolumeClaim:
      claimName: $BACKUP_PVC
  containers:
  - name: $RESTORE_POD
    image: $image
    command: ["sleep", "3600"]
    volumeMounts:
    - mountPath: /backups/
      name: backup
EOF
    echo "Waiting for restore pod to be ready..."
    oc wait "pod/$RESTORE_POD" -n "$NAMESPACE" --for=condition=Ready --timeout=120s
  fi
}

select_and_download_backup() {
  local tmp_dir="$1"

  echo ""
  echo "Available backups:"
  BACKUPS=()
  while IFS= read -r line; do
    BACKUPS+=("$line")
  done < <(oc exec "$RESTORE_POD" -n "$NAMESPACE" -- find /backups -name "*.sql.gz" | sort -r)

  if [[ ${#BACKUPS[@]} -eq 0 ]]; then
    echo "ERROR: No backup files found on restore pod"
    exit 1
  fi

  for i in "${!BACKUPS[@]}"; do
    echo "  $((i+1))) ${BACKUPS[$i]}"
  done

  read -rp "Select backup [1]: " BACKUP_CHOICE
  BACKUP_CHOICE=${BACKUP_CHOICE:-1}
  local backup_file="${BACKUPS[$((BACKUP_CHOICE-1))]}"
  echo "Using: $backup_file"

  echo "Downloading backup (this may take a moment)..."
  local local_gz="$tmp_dir/metabase-backup.sql.gz"
  oc cp "$NAMESPACE/$RESTORE_POD:$backup_file" "$local_gz"
  echo "Decompressing..."
  gunzip "$local_gz"
  LOCAL_SQL="${local_gz%.gz}"
}

apply_restore_sql() {
  local restore_sql="$1"
  local fallback_path="$2"

  echo ""
  read -rp "Apply to $DB_NAME in $NAMESPACE? [y/N]: " CONFIRM
  if [[ "${CONFIRM,,}" != "y" ]]; then
    cp "$restore_sql" "$fallback_path"
    echo "Aborted. Restore SQL saved to $fallback_path"
    exit 0
  fi

  echo "Copying SQL to DB pod..."
  oc cp "$restore_sql" "$NAMESPACE/$DB_POD:/tmp/restore.sql"
  echo "Running restore..."
  oc exec -it "$DB_POD" -n "$NAMESPACE" -- psql -U "$DB_USER" -d "$DB_NAME" -f /tmp/restore.sql
}
