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

os.makedirs(OUT_DIR, exist_ok=True)
resource_names = []
for name, template, params in RESOURCES:
    cmd = ["oc", "process", "-f", f"{TEMPLATE_DIR}/{template}", "--local", "-o", "json"]
    for k, v in params.items():
        cmd += ["-p", f"{k}={v}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAILED: {name}\n{result.stderr}")
        continue
    # oc process wraps single objects in a List; unwrap to the bare object for a cleaner base
    # file. Written as YAML to match every other manifest in openshift/ -- pyyaml is already
    # a backend dependency (see backend/uv.lock), so this doesn't add a new one.
    doc = json.loads(result.stdout)
    items = doc.get("items", [])
    if len(items) != 1:
        print(f"WARNING: {name} rendered {len(items)} items, expected 1")
    out_path = f"{OUT_DIR}/{name}.yaml"
    with open(out_path, "w") as f:
        yaml.dump(items[0], f, default_flow_style=False, sort_keys=False)
    resource_names.append(name)
    print(f"OK: {name}")

print(f"\n{len(resource_names)} base files generated")
print(resource_names)
