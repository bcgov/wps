# Metabase Restore

Procedures for restoring accidentally deleted Metabase users and dashboards from the automated backup.

## Background

Metabase is backed up every 4 hours by a CronJob using the [BC Gov backup container](https://github.com/BCDevOps/backup-container). Backups are stored as compressed pg_dump files on a PVC and retained for 7 daily, 4 weekly, and 1 monthly snapshot.

Deleting a Metabase user via the database cascades to their dashboards, cards, and dashboardcards. These procedures restore specific users or dashboards without affecting the rest of the database.

---

## Restoring Users

```bash
./oc_restore_metabase_users.sh \
  --namespace <namespace> \
  --db-name <database> \
  --backup-pvc <pvc-name> \
  --restore-pod <pod-name>
```

The script will prompt for:
1. A backup file to restore from (most recent shown first)
2. User IDs to restore
3. Whether to clear passwords (forces users to reset via "Forgot password")

### What Gets Restored

| Table | What |
|---|---|
| `core_user` | The user record |
| `permissions_group_membership` | Group memberships |

### Finding User IDs

```sql
SELECT id, email, is_active FROM core_user;
```

### Password Handling

If you choose to clear passwords, users must use "Forgot password" to set a new one. If you keep the original password hash, users can log in with their previous password.

> **Note:** Metabase has a known issue where its auto-generated passwords can fail its own "too common" password check. If you need to reset a user's password programmatically, set it manually via the API rather than using the admin UI's reset flow.

---

## Restoring Dashboards

```bash
./oc_restore_metabase_dashboards.sh \
  --namespace <namespace> \
  --db-name <database> \
  --backup-pvc <pvc-name> \
  --restore-pod <pod-name>
```

The script will prompt for:
1. A backup file to restore from (most recent shown first)
2. Dashboard IDs to restore (visible in the Metabase URL: `/dashboard/3`)
3. A Metabase user ID to assign as owner
4. Confirmation before applying

You need `oc` CLI access to the namespace and Python 3.

### What Gets Restored

| Table | What |
|---|---|
| `report_dashboard` | The dashboard itself |
| `dashboard_tab` | Any tabs on the dashboard |
| `report_card` | All questions/cards used by the dashboard |
| `report_dashboardcard` | The card placements on the dashboard |

Sequences are reset after the restore to prevent future ID collisions.

### Creator ID Reassignment

Cards and dashboards originally created by deleted users are reassigned to the owner ID you provide. The `made_public_by_id` field is nulled out for deleted users (removing the public sharing link).

### Finding Dashboard IDs

Dashboard IDs are visible in the Metabase URL when viewing a dashboard:
```
https://your-metabase/dashboard/3-wps-dashboard  →  ID is 3
```

Or query the database directly:
```sql
SELECT id, name, creator_id FROM report_dashboard;
```

### Backup Selection

The script lists all available backups from the PVC, most recent first. Choose a backup that predates the deletion. Backup timestamps are in UTC.

---

## Manual Steps (if the script fails)

**1. Download a backup:**
```bash
# Spin up a pod with access to the backup PVC (see oc_restore_metabase_dashboards.sh for full pod spec)
oc cp <namespace>/<restore-pod>:/backups/daily/YYYY-MM-DD/<file>.sql.gz ~/Downloads/metabase-backup.sql.gz
gunzip ~/Downloads/metabase-backup.sql.gz
```

**2. Generate restore SQL for dashboards:**
```bash
python3 metabase_dashboard_restore_extract.py \
  ~/Downloads/metabase-backup.sql \
  <dashboard-id> [<dashboard-id> ...] \
  --owner <user-id> \
  --output ~/Downloads/metabase_restore.sql
```

**2. Generate restore SQL for users:**
```bash
python3 metabase_user_restore_extract.py \
  ~/Downloads/metabase-backup.sql \
  <user-id> [<user-id> ...] \
  [--reset-password] \
  --output ~/Downloads/metabase_user_restore.sql
```

**3. Apply to the database:**
```bash
DB_POD=$(oc get pods -n <namespace> --no-headers | grep "mb-database-prod" | grep Running | awk '{print $1}')
oc cp ~/Downloads/metabase_restore.sql <namespace>/$DB_POD:/tmp/metabase_restore.sql
oc exec -it $DB_POD -n <namespace> -- psql -U <db-user> -d <database> -f /tmp/metabase_restore.sql
```

A successful restore ends with `COMMIT`. If you see `ROLLBACK`, the transaction was aborted — check the error output.

## Cleanup

The restore pod is left running after the script completes (it auto-terminates after 1 hour). Delete it manually if needed:

```bash
oc delete pod <restore-pod> -n <namespace>
```
