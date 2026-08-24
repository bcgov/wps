import os
import yaml

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
CRONJOBS_DIR = os.path.normpath(os.path.join(OUT_DIR, "../../base/cronjobs"))


def load_values(cronjob_patch_filename):
    """Pull the {var_name: value_payload} mapping straight out of an existing
    base/cronjobs/*.patch.yaml -- same secrets, same keys, just nested under
    spec.jobTemplate.spec.template instead of spec.template (CronJob vs Deployment), so the
    ops themselves can't be reused verbatim, but there's no reason to retype the values."""
    ops = yaml.safe_load(open(f"{CRONJOBS_DIR}/{cronjob_patch_filename}"))
    return {op["value"]["name"]: {k: v for k, v in op["value"].items() if k != "name"} for op in ops}


# SENTRY_DSN is API-specific -- no cronjob ever needed it, so it's the only value defined
# here rather than sourced from an existing cronjobs patch. PORT was here too until it turned
# out to be dead everywhere (start.sh hardcodes the bind address) -- removed from all three
# Templates, not just deduped away. REDIS_CACHE_NOAA similarly turned out to be dead on "api"
# specifically (only ever read by wps-jobs, a package never bundled into the api image) and
# was removed from openshift/templates/deploy.yaml -- its group is gone too, since keeping it
# would silently re-inject the var this Deployment no longer wants via the shared patch.
VALUES = {
    "SENTRY_DSN": {"valueFrom": {"secretKeyRef": {"key": "sentry-dsn", "name": "wps-global"}}},
    **load_values("env-postgres.patch.yaml"),
    **load_values("env-objectstore.patch.yaml"),
    **load_values("env-global.patch.yaml"),
    **load_values("env-redis.patch.yaml"),
    **load_values("env-wfwx.patch.yaml"),
    **load_values("env-redis-dailies.patch.yaml"),
    **load_values("env-redis-cache-env-canada.patch.yaml"),
}

# (patch filename, label, [var names]) -- one group per semantic concern, same breakdown
# style as base/cronjobs/generate.py's COMMON_ENV_GROUPS, not lumped together just because
# they happen to share membership today. env-postgres/env-objectstore reuse the exact label
# names base/cronjobs's own patches use (same meaning, different Kind -- target.kind keeps
# them from ever cross-matching); env-sentry is API-only, no cronjob equivalent.
#
# All three API Deployments' relevant container sits at index 0 -- asa-go-api/sfms-fwi-api
# are single-container, and the main "api" Deployment has its api/web containers swapped in
# base/api/generate.py specifically so it lines up with the other two instead of needing an
# index-1 variant.
GROUPS = [
    # asa-go-api + sfms-fwi-api + api.
    ("env-postgres.patch.yaml", "app.wps/env-postgres",
     ["POSTGRES_READ_USER", "POSTGRES_WRITE_USER", "POSTGRES_PASSWORD",
      "POSTGRES_WRITE_HOST", "POSTGRES_READ_HOST", "POSTGRES_PORT", "POSTGRES_DATABASE"]),
    ("env-sentry.patch.yaml", "app.wps/env-sentry", ["SENTRY_DSN"]),
    # sfms-fwi-api + api only (asa-go-api doesn't use object storage at all).
    ("env-objectstore.patch.yaml", "app.wps/env-objectstore",
     ["OBJECT_STORE_SERVER", "OBJECT_STORE_USER_ID", "OBJECT_STORE_SECRET", "OBJECT_STORE_BUCKET"]),
    # api only -- confirmed full-group byte-identical matches against base/cronjobs's own
    # canonical values; asa-go-api/sfms-fwi-api don't carry these vars at all. Same label
    # names as the cronjobs groups of the same name (same meaning, different Kind).
    ("env-global.patch.yaml", "app.wps/env-global",
     ["CHATOPS_URL", "CHATOPS_AUTH_TOKEN", "OPENSHIFT_CONSOLE_URL", "PROJECT_NAMESPACE"]),
    ("env-redis.patch.yaml", "app.wps/env-redis",
     ["REDIS_HOST", "REDIS_PORT", "REDIS_USE", "REDIS_PASSWORD",
      "REDIS_STATION_CACHE_EXPIRY", "REDIS_AUTH_CACHE_EXPIRY"]),
    ("env-wfwx.patch.yaml", "app.wps/env-wfwx",
     ["WFWX_AUTH_URL", "WFWX_BASE_URL", "WFWX_USER", "WFWX_SECRET"]),
    ("env-redis-dailies.patch.yaml", "app.wps/env-redis-dailies",
     ["REDIS_DAILIES_BY_STATION_CODE_CACHE_EXPIRY"]),
    ("env-redis-cache-env-canada.patch.yaml", "app.wps/env-redis-cache-env-canada",
     ["REDIS_CACHE_ENV_CANADA"]),
]

kustomization_patches = []
for filename, label, var_names in GROUPS:
    ops = [
        {
            "op": "add",
            "path": "/spec/template/spec/containers/0/env/-",
            "value": {"name": name, **VALUES[name]},
        }
        for name in var_names
    ]
    with open(f"{OUT_DIR}/{filename}", "w") as f:
        yaml.dump(ops, f, default_flow_style=False, sort_keys=False)
    kustomization_patches.append((filename, label))
    print(f"OK: {filename} ({len(ops)} vars)")

print("\nlabelSelectors for kustomization.yaml's patches:")
for filename, label in kustomization_patches:
    print(f"  {filename}: {label}=true")
