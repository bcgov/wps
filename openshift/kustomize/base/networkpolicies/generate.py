import subprocess
import os
import json
import yaml

# Paths are relative to this file, not the caller's working directory -- same convention
# as base/cronjobs/generate.py.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.normpath(os.path.join(THIS_DIR, "../../../templates"))
OUT_DIR = THIS_DIR

# Neither policy has a namespace field of its own -- both rely on the caller's -n flag
# today, and on Kustomize's namespace: transformer here, same as everything else.
RESOURCES = [
    ("allow-gateway-to-wps-asa-go-api", "allow_gateway_to_wps_asa_go_api.yaml", {
        "APP_NAME": "wps", "SUFFIX": "__SUFFIX__",
    }),
    ("allow-gateway-to-wps-sfms-fwi-api", "allow_gateway_to_wps_sfms_fwi_api.yaml", {
        "APP_NAME": "wps", "SUFFIX": "__SUFFIX__",
    }),
]

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
