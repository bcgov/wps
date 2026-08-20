import subprocess
import os
import json
import yaml

# Paths are relative to this file, not the caller's working directory, so this runs
# correctly whether invoked as `python3 generate.py` from this directory or via a full
# path from anywhere else (e.g. repo root).
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.normpath(os.path.join(THIS_DIR, "../../../templates"))
OUT_DIR = THIS_DIR
IMAGE_REGISTRY = "image-registry.openshift-image-registry.svc:5000"
PROJ_TOOLS = "e1e498-tools"

# name, template file, params (with __SUFFIX__/__NAMESPACE__ placeholders already embedded)
RESOURCES = [
    ("s3-data-retention", "s3_retention.cronjob.yaml", {
        "JOB_NAME": "s3-retention-wps-__SUFFIX__",
        "APP_LABEL": "wps-__SUFFIX__",
        "SUFFIX": "__SUFFIX__",
        "SCHEDULE": "20 * * * *",
    }),
    ("env-canada-gdps", "env_canada_gdps.cronjob.yaml", {
        "JOB_NAME": "env-canada-gdps-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "9 * * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "PROJECT_NAMESPACE": "__NAMESPACE__",
    }),
    ("env-canada-hrdps", "env_canada_hrdps.cronjob.yaml", {
        "JOB_NAME": "env-canada-hrdps-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "14 * * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "PROJECT_NAMESPACE": "__NAMESPACE__",
    }),
    ("env-canada-rdps", "env_canada_rdps.cronjob.yaml", {
        "JOB_NAME": "env-canada-rdps-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "19 * * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "PROJECT_NAMESPACE": "__NAMESPACE__",
    }),
    ("noaa-gfs", "noaa_gfs.cronjob.yaml", {
        "JOB_NAME": "noaa-gfs-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "24 */4 * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "PROJECT_NAMESPACE": "__NAMESPACE__",
    }),
    ("noaa-nam", "noaa_nam.cronjob.yaml", {
        "JOB_NAME": "noaa-nam-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "29 */4 * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "PROJECT_NAMESPACE": "__NAMESPACE__",
    }),
    ("ecmwf", "ecmwf.cronjob.yaml", {
        "JOB_NAME": "ecmwf-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "34 * * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "PROJECT_NAMESPACE": "__NAMESPACE__",
    }),
    ("viirs-snow", "viirs_snow.cronjob.yaml", {
        "JOB_NAME": "viirs-snow-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "39 * * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "PROJECT_NAMESPACE": "__NAMESPACE__",
    }),
    ("grass-curing", "grass_curing.cronjob.yaml", {
        "JOB_NAME": "grass-curing-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "44 * * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "PROJECT_NAMESPACE": "__NAMESPACE__",
    }),
    ("rdps-sfms", "rdps_sfms.cronjob.yaml", {
        "JOB_NAME": "rdps-sfms-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "49 * * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "PROJECT_NAMESPACE": "__NAMESPACE__",
    }),
    ("sfms-fwi-calc", "sfms_calculations.cronjob.yaml", {
        "JOB_NAME": "sfms-fwi-calc-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "54 * * * *",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "PROJECT_NAMESPACE": "__NAMESPACE__",
    }),
    ("sfms-daily-actuals", "sfms_daily_actuals.cronjob.yaml", {
        "JOB_NAME": "sfms-daily-actuals-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "59 * * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJECT_NAMESPACE": "__NAMESPACE__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
    }),
    ("sfms-forecast-8am", "sfms_daily_forecasts.cronjob.yaml", {
        # JOB_NAME_SUFFIX in the original script is "${SUFFIX}${JOB_SUFFIX:+-${JOB_SUFFIX}}",
        # not just JOB_SUFFIX alone -- confirmed by reading the script directly, since a
        # first pass at this got it wrong and would have made every PR collide on the same
        # CronJob name.
        "JOB_NAME": "sfms-forecast-wps-__SUFFIX__-8am", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "0 15 * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJECT_NAMESPACE": "__NAMESPACE__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
    }),
    ("sfms-forecast-545pm", "sfms_daily_forecasts.cronjob.yaml", {
        "JOB_NAME": "sfms-forecast-wps-__SUFFIX__-545pm", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "45 0 * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJECT_NAMESPACE": "__NAMESPACE__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
    }),
    ("fire-watch-weather", "fire_watch_weather.cronjob.yaml", {
        "JOB_NAME": "fire-watch-weather-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "4 * * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "PROJECT_NAMESPACE": "__NAMESPACE__",
    }),
    ("wfwx-noon-forecasts", "wfwx_noon_forecasts.cronjob.yaml", {
        "JOB_NAME": "wfwx-noon-forecasts-wps-__SUFFIX__", "NAME": "wps-api", "APP_LABEL": "wps-__SUFFIX__",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "30 * * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "PROJECT_NAMESPACE": "__NAMESPACE__",
    }),
    ("wfwx-hourly-actuals", "wfwx_hourly_actuals.cronjob.yaml", {
        "JOB_NAME": "wfwx-hourly-actuals-wps-__SUFFIX__", "NAME": "wps-api", "APP_LABEL": "wps-__SUFFIX__",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "15 * * * *", "POSTGRES_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "PROJECT_NAMESPACE": "__NAMESPACE__",
    }),
    ("partitioner", "partitioner.cronjob.yaml", {
        "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "0 6 1 * *",
        "PG_DATABASE": "wps",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJ_TOOLS": PROJ_TOOLS,
    }),
    ("hourly-prune", "prune_hourlies_cronjob.yaml", {
        "SUFFIX": "__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "SCHEDULE": "0 2 * * *",
        "PROJ_TOOLS": PROJ_TOOLS,
    }),
    ("wx-4panel-charts-gdps", "wx_4panel_charts.cronjob.yaml", {
        "JOB_NAME": "wx-4panel-charts-gdps-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "9 * * * *",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "END_HOUR": "240", "STEP": "6", "MODEL": "GDPS",
        "WEATHER_IMAGE": "ghcr.io/bcgov/wps/wps-weather:prod",
    }),
    ("wx-4panel-charts-rdps", "wx_4panel_charts.cronjob.yaml", {
        "JOB_NAME": "wx-4panel-charts-rdps-wps-__SUFFIX__", "APP_LABEL": "wps-__SUFFIX__", "NAME": "wps",
        "SUFFIX": "__SUFFIX__", "SCHEDULE": "9 * * * *",
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "END_HOUR": "84", "STEP": "3", "MODEL": "RDPS",
        "WEATHER_IMAGE": "ghcr.io/bcgov/wps/wps-weather:prod",
    }),
]
# backup-s3-postgres-cronjob.sh has non-standard param wiring (JOB_NAME/IMAGE_NAMESPACE/CLUSTER_NAME/
# TAG_NAME come from undocumented env vars, not derived the way every other script does it) --
# skipped from this generation pass; needs individual investigation, noted in the summary.

# Groups of env vars baked identically into several Templates (same wps-global/wps-redis/
# wps-crunchydb secrets, referenced the same way). Deduped here into shared Kustomize
# patches (see COMMON_ENV_PATCH_DIR below) instead of repeated in every base file. A group
# is only stripped from a resource when every var in it is present with a byte-identical
# value to every other resource that has it -- a resource missing part of a group, or with
# a differing value, keeps its own copy untouched and doesn't get the label.
COMMON_ENV_GROUPS = {
    "wps.bcgov/env-global": ["CHATOPS_URL", "CHATOPS_AUTH_TOKEN", "OPENSHIFT_CONSOLE_URL", "PROJECT_NAMESPACE"],
    "wps.bcgov/env-uv": ["UV_NO_CACHE"],
    "wps.bcgov/env-postgres": [
        "POSTGRES_READ_USER", "POSTGRES_WRITE_USER", "POSTGRES_PASSWORD",
        "POSTGRES_WRITE_HOST", "POSTGRES_READ_HOST", "POSTGRES_PORT", "POSTGRES_DATABASE",
    ],
    "wps.bcgov/env-redis": [
        "REDIS_HOST", "REDIS_PORT", "REDIS_USE", "REDIS_PASSWORD",
        "REDIS_STATION_CACHE_EXPIRY", "REDIS_AUTH_CACHE_EXPIRY",
    ],
    "wps.bcgov/env-wfwx": ["WFWX_AUTH_URL", "WFWX_BASE_URL", "WFWX_USER", "WFWX_SECRET"],
    "wps.bcgov/env-objectstore": [
        "OBJECT_STORE_SERVER", "OBJECT_STORE_USER_ID", "OBJECT_STORE_SECRET", "OBJECT_STORE_BUCKET",
    ],
    # Narrower membership than env-redis above (env-canada/noaa/wfwx only), so it can't
    # fold into that group without also matching everything else in it.
    "wps.bcgov/env-redis-dailies": ["REDIS_DAILIES_BY_STATION_CODE_CACHE_EXPIRY"],
    # env-canada-* plus rdps-sfms, which also consumes RDPS data and shares the same cache.
    "wps.bcgov/env-redis-cache-env-canada": ["REDIS_CACHE_ENV_CANADA"],
    "wps.bcgov/env-redis-cache-noaa": ["REDIS_CACHE_NOAA"],
    # env-canada-* and noaa-* share the same grib-retention config; other consumers don't.
    "wps.bcgov/env-data-retention": ["DATA_RETENTION_THRESHOLD"],
    # s3-data-retention + wx-4panel-charts-*: same object store, WX_-prefixed var names.
    "wps.bcgov/env-wx-objectstore": [
        "OBJECT_STORE_SERVER", "WX_OBJECT_STORE_USER_ID", "WX_OBJECT_STORE_SECRET", "WX_OBJECT_STORE_BUCKET",
    ],
    "wps.bcgov/env-wx-cartopy": ["WX_CARTOPY_DATA_DIR"],
    # hourly-prune + partitioner: same object-store secret, AWS_-prefixed var names, plus
    # the same literal SUFFIX placeholder (still substituted by the caller's sed pass
    # wherever it ends up, base file or patch, so deduping it here is safe).
    "wps.bcgov/env-aws": ["AWS_ACCESS_KEY", "AWS_BUCKET", "AWS_HOSTNAME", "AWS_SECRET_KEY", "SUFFIX"],
}

# wx_4panel_charts.cronjob.yaml has no POSTGRES_DATABASE parameter or env entry at all --
# unlike every other Postgres-using Template, which all default it to "wps". Injected here,
# Kustomize-base-only (the Template itself is untouched), purely so these two resources
# match env-postgres's full 7-var group instead of keeping all 7 as their own local copy.
EXTRA_ENV = {
    "wx-4panel-charts-gdps": [{"name": "POSTGRES_DATABASE", "value": "wps"}],
    "wx-4panel-charts-rdps": [{"name": "POSTGRES_DATABASE", "value": "wps"}],
}

os.makedirs(OUT_DIR, exist_ok=True)
rendered = []
for name, template, params in RESOURCES:
    cmd = ["oc", "process", "-f", f"{TEMPLATE_DIR}/{template}", "--local", "-o", "json"]
    for k, v in params.items():
        cmd += ["-p", f"{k}={v}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAILED: {name}\n{result.stderr}")
        continue
    doc = json.loads(result.stdout)
    items = doc.get("items", [])
    if len(items) != 1:
        print(f"WARNING: {name} rendered {len(items)} items, expected 1")
    item = items[0]
    if name in EXTRA_ENV:
        item["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][0]["env"] += EXTRA_ENV[name]
    rendered.append((name, item))

# First pass: record the canonical (first-seen) value of every candidate common env var.
canonical = {}
for _, item in rendered:
    env = item["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][0].get("env", [])
    by_name = {e["name"]: e for e in env}
    for names in COMMON_ENV_GROUPS.values():
        for var in names:
            if var in by_name and var not in canonical:
                canonical[var] = by_name[var]

# Second pass: strip each group from a resource's env only if every var in it matches
# canonical exactly, and record which group patches are actually used by anything.
groups_in_use = set()
for name, item in rendered:
    container = item["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][0]
    env = container.get("env", [])
    by_name = {e["name"]: e for e in env}
    for label, names in COMMON_ENV_GROUPS.items():
        if all(var in by_name and by_name[var] == canonical[var] for var in names):
            container["env"] = [e for e in container["env"] if e["name"] not in names]
            item.setdefault("metadata", {}).setdefault("labels", {})[label] = "true"
            groups_in_use.add(label)

resource_names = []
for name, item in rendered:
    # oc process wraps single objects in a List; unwrap to the bare object for a cleaner base
    # file. Written as YAML to match every other manifest in openshift/ -- pyyaml is already
    # a backend dependency (see backend/uv.lock), so this doesn't add a new one.
    out_path = f"{OUT_DIR}/{name}.yaml"
    with open(out_path, "w") as f:
        yaml.dump(item, f, default_flow_style=False, sort_keys=False)
    resource_names.append(name)
    print(f"OK: {name}")

# Emit one JSON6902 patch per group actually used, appending its env vars back onto
# whichever resources the label-selector target matches -- see kustomization.yaml's
# `patches:` list, which references these by filename. JSON6902 "add to array" ops work by
# index, not by container name, so this doesn't run into strategic-merge's container-name
# mergeKey (which differs per resource and would silently add a second container instead of
# merging). Not regenerated for groups nothing uses, so an empty/unused patch file never
# lingers if a future Template change removes the last resource that needed it.
for label, names in COMMON_ENV_GROUPS.items():
    patch_path = f"{OUT_DIR}/{label.split('/')[-1]}.patch.yaml"
    if label not in groups_in_use:
        if os.path.exists(patch_path):
            os.remove(patch_path)
        continue
    ops = [
        {
            "op": "add",
            "path": "/spec/jobTemplate/spec/template/spec/containers/0/env/-",
            "value": canonical[var],
        }
        for var in names
    ]
    with open(patch_path, "w") as f:
        yaml.dump(ops, f, default_flow_style=False, sort_keys=False)
    print(f"PATCH: {patch_path}")

print(f"\n{len(resource_names)} base files generated, {len(groups_in_use)} common-env patches emitted")
print(resource_names)
