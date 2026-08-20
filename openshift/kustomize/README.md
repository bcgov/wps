# Kustomize deploys

Phase 0 of the Templates → Kustomize migration (see the strategy doc). Currently covers
the 20 independent CronJobs previously provisioned individually via `oc process | oc apply`
(and, before that, batched by hand on `harden-oc-deploys`).

## Layout

```
base/cronjobs/       plain manifests, one per resource, real default values
overlays/dev/        namespace: e1e498-dev, dev-specific memory patches
overlays/prod/       namespace: e1e498-prod, prod-specific memory patches
```

## The `__SUFFIX__` / `__NAMESPACE__` placeholders

Every value that's genuinely static per environment (namespace, memory, schedule) is a
real value baked in at generation time or an overlay patch. `SUFFIX` (e.g. `pr-1234`)
isn't static -- it's computed fresh on every CI run, in both dev and prod -- so it's left
as the literal placeholder token `__SUFFIX__` everywhere it appears (resource names,
labels, the CrunchyDB secret reference). `__NAMESPACE__` is used the same way for the one
field (`PROJECT_NAMESPACE`, a container env var) that Kustomize's own `namespace:`
transformer doesn't reach, since that only sets `metadata.namespace`.

Both get substituted with a plain `sed` pass on the built output, immediately before
applying:

```bash
oc kustomize openshift/kustomize/overlays/prod \
  | sed "s/__SUFFIX__/${SUFFIX}/g; s/__NAMESPACE__/e1e498-prod/g" \
  | oc apply -f -
```

## Not yet migrated

- `oc_provision_backup_s3_postgres_cronjob.sh` -- its parameter wiring doesn't follow the
  same pattern as every other script (`JOB_NAME`/`IMAGE_NAMESPACE`/`CLUSTER_NAME`/`TAG_NAME`
  come from env vars not derived the usual way) and needs individual investigation before
  converting.
- `oc_provision_eccc_grib_consumer.sh` and `oc_provision_fuel_grid_install_job.sh` -- each
  does a real imperative step (`rollout restart`, `patch`) after applying, so only their
  render half would move to Kustomize; not done in this phase.
- The three Deployment-backed services (API, ASA Go API, SFMS FWI API) -- see
  `base/asa-go-api/` and `base/sfms-fwi-api/` (Phase 1) and the strategy doc for why the
  main API deployment is deliberately structural-only for now.
