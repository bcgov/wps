import subprocess
import os
import json
import yaml

# Paths are relative to this file, not the caller's working directory -- same convention
# as base/cronjobs/generate.py.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.normpath(os.path.join(THIS_DIR, "../../../templates"))
OUT_DIR = THIS_DIR

# Deployment + Service, written as one multi-document YAML file -- see
# base/asa-go-api/generate.py for why. No PROJECT_NAMESPACE param exists on this template
# (confirmed against the template's parameter list), unlike asa-go-api/deploy.yaml.
#
# CPU/MEMORY/REPLICAS intentionally NOT overridden -- prod's call site doesn't override them
# either, so the base matches prod's effective config (the template's own defaults).
# ENVIRONMENT=production is set explicitly since prod's call site does set that one. dev's
# overlay patches REPLICAS down to 1 and ENVIRONMENT to development.
PARAMS = {
    "APP_NAME": "wps",
    "SUFFIX": "__SUFFIX__",
    "POSTGRES_DATABASE": "wps",
    "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
    "ENVIRONMENT": "production",
    "DEPLOY_VERSION": "__DEPLOY_VERSION__",
}

os.makedirs(OUT_DIR, exist_ok=True)
cmd = ["oc", "process", "-f", f"{TEMPLATE_DIR}/sfms_fwi_api.yaml", "--local", "-o", "json"]
for k, v in PARAMS.items():
    cmd += ["-p", f"{k}={v}"]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    raise SystemExit(f"FAILED: sfms-fwi-api\n{result.stderr}")

items = json.loads(result.stdout).get("items", [])

# Values (and the container-index reasoning) live in
# components/api-common-env/generate.py, which emits the patches these labels select.
# ENVIRONMENT deliberately NOT deduped -- see base/asa-go-api/generate.py for why.
COMMON_ENV_GROUPS = {
    "app.wps/env-postgres": [
        "POSTGRES_READ_USER", "POSTGRES_WRITE_USER", "POSTGRES_PASSWORD",
        "POSTGRES_WRITE_HOST", "POSTGRES_READ_HOST", "POSTGRES_PORT", "POSTGRES_DATABASE",
    ],
    "app.wps/env-sentry": ["SENTRY_DSN"],
    "app.wps/env-objectstore": [
        "OBJECT_STORE_SERVER", "OBJECT_STORE_USER_ID", "OBJECT_STORE_SECRET", "OBJECT_STORE_BUCKET",
    ],
}
for item in items:
    if item.get("kind") != "Deployment":
        continue
    container = item["spec"]["template"]["spec"]["containers"][0]
    for label, var_names in COMMON_ENV_GROUPS.items():
        container["env"] = [e for e in container["env"] if e["name"] not in var_names]
        item.setdefault("metadata", {}).setdefault("labels", {})[label] = "true"

out_path = f"{OUT_DIR}/sfms-fwi-api.yaml"
with open(out_path, "w") as f:
    for i, item in enumerate(items):
        if i:
            f.write("---\n")
        yaml.dump(item, f, default_flow_style=False, sort_keys=False)

print(f"OK: sfms-fwi-api ({len(items)} objects)")
