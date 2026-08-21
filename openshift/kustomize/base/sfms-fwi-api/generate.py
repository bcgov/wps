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
out_path = f"{OUT_DIR}/sfms-fwi-api.yaml"
with open(out_path, "w") as f:
    for i, item in enumerate(items):
        if i:
            f.write("---\n")
        yaml.dump(item, f, default_flow_style=False, sort_keys=False)

print(f"OK: sfms-fwi-api ({len(items)} objects)")
