import subprocess
import os
import json
import yaml

# Paths are relative to this file, not the caller's working directory -- same convention
# as base/cronjobs/generate.py.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.normpath(os.path.join(THIS_DIR, "../../../templates"))
OUT_DIR = THIS_DIR

# Unlike the CronJob templates (one object each), this renders a Deployment + Service --
# written as one multi-document YAML file (Kustomize accepts a file with multiple `---`
# documents as a single resource entry), rather than split into one-object files.
#
# CPU/MEMORY/REPLICAS/ENVIRONMENT intentionally NOT overridden here even though
# oc_deploy_asa_go_api.sh supports them -- prod's call site never overrides them either
# (falls back to the template's own defaults below), so the base matches prod's effective
# config; ENVIRONMENT=production is set explicitly since prod's call site does set that one.
# dev's overlay patches these down to its own values (REPLICAS=1, MEMORY_REQUEST=700Mi,
# MEMORY_LIMIT=1Gi, ENVIRONMENT=development).
PARAMS = {
    "APP_NAME": "wps",
    "SUFFIX": "__SUFFIX__",
    "PROJECT_NAMESPACE": "__NAMESPACE__",
    "POSTGRES_DATABASE": "wps",
    "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
    "ENVIRONMENT": "production",
    "DEPLOY_VERSION": "__DEPLOY_VERSION__",
}

os.makedirs(OUT_DIR, exist_ok=True)
cmd = ["oc", "process", "-f", f"{TEMPLATE_DIR}/asa_go_api.yaml", "--local", "-o", "json"]
for k, v in PARAMS.items():
    cmd += ["-p", f"{k}={v}"]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    raise SystemExit(f"FAILED: asa-go-api\n{result.stderr}")

items = json.loads(result.stdout).get("items", [])

# PORT/POSTGRES_*/SENTRY_DSN are byte-identical to sfms-fwi-api's (and api's) copies of the
# same vars -- deduped into a shared Kustomize Component
# (openshift/kustomize/components/api-common-env/), one patch per semantic group rather than
# one lumped patch, same breakdown style as base/cronjobs. See that component's generate.py
# for the full GROUPS list and why POSTGRES_*/OBJECT_STORE_*'s op path can't be shared with
# base/cronjobs's patches of the same name even though the values are.
COMMON_ENV_GROUPS = {
    "app.wps/env-postgres": [
        "POSTGRES_READ_USER", "POSTGRES_WRITE_USER", "POSTGRES_PASSWORD",
        "POSTGRES_WRITE_HOST", "POSTGRES_READ_HOST", "POSTGRES_PORT", "POSTGRES_DATABASE",
    ],
    "app.wps/env-sentry": ["SENTRY_DSN"],
}
# ENVIRONMENT deliberately NOT included even though its value matches too -- dev's overlay
# needs to override it per-environment, and Kustomize's JSON6902 targets env entries by
# array index, not name. Keeping it local (at a stable, known index in this base) is far
# simpler than computing where it'd land after a shared component appends other vars.
for item in items:
    if item.get("kind") != "Deployment":
        continue
    container = item["spec"]["template"]["spec"]["containers"][0]
    for label, var_names in COMMON_ENV_GROUPS.items():
        container["env"] = [e for e in container["env"] if e["name"] not in var_names]
        item.setdefault("metadata", {}).setdefault("labels", {})[label] = "true"

out_path = f"{OUT_DIR}/asa-go-api.yaml"
with open(out_path, "w") as f:
    for i, item in enumerate(items):
        if i:
            f.write("---\n")
        yaml.dump(item, f, default_flow_style=False, sort_keys=False)

print(f"OK: asa-go-api ({len(items)} objects)")
