# Adding a New Fuel Raster

Use this checklist near the start of each fire season when a new SFMS fuel grid is ready.

The install job does the static setup for one fuel grid:

1. Copies the staged raster to the versioned fuel raster location.
2. Inserts one `fuel_type_raster` row.
3. Generates the fuel-masked classified TPI raster.
4. Populates static advisory data for that raster:
   - `advisory_fuel_types`
   - `advisory_shape_fuels`
   - `combustible_area`
   - `tpi_fuel_area`
5. Verifies the derived row counts before the DB transaction commits.
6. Marks the `fuel_type_raster` row as `ready`.

The install job does not reprocess date-based advisory or SFMS outputs. Reprocess those separately
for the operational date range that should use the new fuel grid.

## 1. Stage the Raster

Upload the source GeoTIFF to object storage under `sfms/static/`.

For example, for the 2026 grid:

```text
sfms/static/fbp2026.tif
```

The job receives only the object name:

```text
fbp2026.tif
```

## 2. Update the Job Template

Update the defaults in `openshift/templates/fuel_grid_install_job.yaml`:

```yaml
- name: FUEL_RASTER_YEAR
  value: "2026"
- name: FUEL_RASTER_KEY
  value: fbp2026.tif
- name: FUEL_RASTER_JOB_SUFFIX
  value: fbp2026
```

Commit this change with the PR. Git history is the record of what raster the seasonal install job
was configured to install.

## 3. Deploy the Suspended Job

The deployment workflow provisions the fuel grid install job. The job is created suspended, so it
does not consume CPU or memory until it is unsuspended.

For a PR/dev deployment, the job name looks like:

```text
fuel-grid-install-wps-pr-5495-2026-fbp2026
```

For production, the name looks like:

```text
fuel-grid-install-wps-prod-2026-fbp2026
```

## 4. Run the Job

Unsuspend the job when the staged raster, image tag, database target, and object-store target are
confirmed.

```bash
oc -n <namespace> patch job/<job-name> --type=merge -p '{"spec":{"suspend":false}}'
```

Follow logs:

```bash
oc -n <namespace> logs -f job/<job-name> --all-containers
```

To rerun, delete and recreate the job, then unsuspend it again:

```bash
oc -n <namespace> delete job/<job-name> --ignore-not-found
PROJ_TARGET=<namespace> bash openshift/scripts/oc_provision_fuel_grid_install_job.sh <suffix> apply
oc -n <namespace> patch job/<job-name> --type=merge -p '{"spec":{"suspend":false}}'
```

## 5. Verify the Install

The job logs should include:

```text
Fuel grid install complete
fuel_type_raster_id: <id>
year: 2026
version: 1
install_status: ready
processed_raster_key: sfms/static/fuel/2026/fbp2026_v1.tif
fuel_masked_tpi_key: dem/tpi/<classified_tpi_base>_fuel_masked_2026_v1.tif
advisory_fuel_types_count: <count>
advisory_shape_fuels_count: <count>
combustible_area_count: <count>
tpi_fuel_area_count: <count>
advisory_shape_fuels_duplicate_count: 0
```

You can also verify in SQL:

```sql
SELECT id, year, version, object_store_path, content_hash, create_timestamp
FROM fuel_type_raster
WHERE year = 2026
  AND install_status = 'ready'
ORDER BY version DESC;
```

Check the static table counts for the installed raster:

```sql
WITH target AS (
    SELECT id
    FROM fuel_type_raster
    WHERE year = 2026
      AND version = 1
)
SELECT 'advisory_fuel_types' AS table_name, count(*) FROM advisory_fuel_types WHERE fuel_type_raster_id IN (SELECT id FROM target)
UNION ALL
SELECT 'advisory_shape_fuels', count(*) FROM advisory_shape_fuels WHERE fuel_type_raster_id IN (SELECT id FROM target)
UNION ALL
SELECT 'combustible_area', count(*) FROM combustible_area WHERE fuel_type_raster_id IN (SELECT id FROM target)
UNION ALL
SELECT 'tpi_fuel_area', count(*) FROM tpi_fuel_area WHERE fuel_type_raster_id IN (SELECT id FROM target);
```

## 6. Reprocess Date-Based Data

After the static fuel-grid install is complete, reprocess any advisory or SFMS stats for dates that
should use the new grid. The date range is an operational decision and is intentionally outside this
install job.

## Failure Behavior

The job stages all DB rows in one transaction. If verification fails, the transaction rolls back.
Normal read paths only select fuel rasters with `install_status = 'ready'`.

Object-store writes cannot roll back with the database, so the job makes a best-effort attempt to
delete the processed fuel raster and generated fuel-masked TPI raster on failure.
