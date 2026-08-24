import subprocess
import os
import json
import yaml

# Paths are relative to this file, not the caller's working directory -- same convention
# as base/cronjobs/generate.py.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.normpath(os.path.join(THIS_DIR, "../../../templates"))
OUT_DIR = THIS_DIR

# Deployment (web + api containers) + 2 Services + 4 Routes, written as one multi-document
# YAML file -- see base/asa-go-api/generate.py for why.
#
# POSTGRES_USER is required by the template but never actually referenced in its objects
# (confirmed via grep) -- still passed since oc process fails without it.
#
# GUNICORN_WORKERS/CPU_REQUEST/MEMORY_REQUEST/MEMORY_LIMIT/REPLICAS/VANITY_DOMAIN/ENVIRONMENT
# all use prod's explicit call-site values here, since prod is the one call site that
# overrides every one of them (dev's call site overrides none of these -- it relies on
# oc_deploy.sh's own defaults, i.e. the template's defaults, for CPU/MEMORY/REPLICAS/
# GUNICORN_WORKERS). dev's overlay patches these back down to the template's original
# defaults (CPU_REQUEST=100m [same either way], MEMORY_REQUEST=3Gi, MEMORY_LIMIT=6Gi,
# REPLICAS=2, GUNICORN_WORKERS=4), plus VANITY_DOMAIN (dev's is per-PR, embeds __SUFFIX__)
# and ENVIRONMENT=development. SECOND_LEVEL_DOMAIN is identical in both today
# (apps.silver.devops.gov.bc.ca), so it's just a base constant, no patch needed.
PARAMS = {
    "SUFFIX": "__SUFFIX__",
    "PROJECT_NAMESPACE": "__NAMESPACE__",
    "POSTGRES_USER": "wps-crunchydb-16-__SUFFIX__",
    "POSTGRES_DATABASE": "wps",
    "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
    "VANITY_DOMAIN": "psu.nrs.gov.bc.ca",
    "SECOND_LEVEL_DOMAIN": "apps.silver.devops.gov.bc.ca",
    "ENVIRONMENT": "production",
    "GUNICORN_WORKERS": "8",
    "CPU_REQUEST": "100m",
    "MEMORY_REQUEST": "6Gi",
    "MEMORY_LIMIT": "8Gi",
    "REPLICAS": "3",
    "DEPLOY_VERSION": "__DEPLOY_VERSION__",
}

os.makedirs(OUT_DIR, exist_ok=True)
cmd = ["oc", "process", "-f", f"{TEMPLATE_DIR}/deploy.yaml", "--local", "-o", "json"]
for k, v in PARAMS.items():
    cmd += ["-p", f"{k}={v}"]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    raise SystemExit(f"FAILED: api\n{result.stderr}")

items = json.loads(result.stdout).get("items", [])

# Container order (web, api) has no semantic meaning to Kubernetes for regular containers --
# no start-order guarantee, nothing elsewhere references them by index, and `oc logs`/`-c`
# already require a container *name*, never falls back to "the first one". Swapped here
# (Kustomize-base-only, the source Template's own container order is untouched) so the api
# container lands at index 0, same as asa-go-api/sfms-fwi-api's single container -- letting
# all three share the exact same env-api-common/env-objectstore patches and labels instead
# of needing a separate index-1 variant just for this one Deployment.
for item in items:
    if item.get("kind") == "Deployment":
        containers = item["spec"]["template"]["spec"]["containers"]
        containers[0], containers[1] = containers[1], containers[0]

# PORT/POSTGRES_*/SENTRY_DSN and OBJECT_STORE_* are byte-identical to asa-go-api/
# sfms-fwi-api's copies of the same vars -- deduped into components/api-common-env/ instead
# of repeated here, one patch per semantic group rather than one lumped patch. See that
# component's generate.py for the full GROUPS list.
COMMON_ENV_GROUPS = {
    "app.wps/env-postgres": [
        "POSTGRES_READ_USER", "POSTGRES_WRITE_USER", "POSTGRES_PASSWORD",
        "POSTGRES_WRITE_HOST", "POSTGRES_READ_HOST", "POSTGRES_PORT", "POSTGRES_DATABASE",
    ],
    "app.wps/env-sentry": ["SENTRY_DSN"],
    "app.wps/env-objectstore": [
        "OBJECT_STORE_SERVER", "OBJECT_STORE_USER_ID", "OBJECT_STORE_SECRET", "OBJECT_STORE_BUCKET",
    ],
    # This Deployment-only (asa-go-api/sfms-fwi-api don't carry these vars at all) -- same
    # groups/values base/cronjobs already established, confirmed full-group byte-identical
    # match before adding.
    "app.wps/env-global": ["CHATOPS_URL", "CHATOPS_AUTH_TOKEN", "OPENSHIFT_CONSOLE_URL", "PROJECT_NAMESPACE"],
    "app.wps/env-redis": [
        "REDIS_HOST", "REDIS_PORT", "REDIS_USE", "REDIS_PASSWORD",
        "REDIS_STATION_CACHE_EXPIRY", "REDIS_AUTH_CACHE_EXPIRY",
    ],
    "app.wps/env-wfwx": ["WFWX_AUTH_URL", "WFWX_BASE_URL", "WFWX_USER", "WFWX_SECRET"],
    "app.wps/env-redis-dailies": ["REDIS_DAILIES_BY_STATION_CODE_CACHE_EXPIRY"],
    "app.wps/env-redis-cache-env-canada": ["REDIS_CACHE_ENV_CANADA"],
}
for item in items:
    if item.get("kind") != "Deployment":
        continue
    container = item["spec"]["template"]["spec"]["containers"][0]
    for label, var_names in COMMON_ENV_GROUPS.items():
        container["env"] = [e for e in container["env"] if e["name"] not in var_names]
        item.setdefault("metadata", {}).setdefault("labels", {})[label] = "true"

out_path = f"{OUT_DIR}/api.yaml"
with open(out_path, "w") as f:
    for i, item in enumerate(items):
        if i:
            f.write("---\n")
        yaml.dump(item, f, default_flow_style=False, sort_keys=False)

print(f"OK: api ({len(items)} objects)")
