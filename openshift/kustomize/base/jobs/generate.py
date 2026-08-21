import subprocess
import os
import json
import yaml

# Paths are relative to this file, not the caller's working directory -- same convention
# as base/cronjobs/generate.py.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.normpath(os.path.join(THIS_DIR, "../../../templates"))
OUT_DIR = THIS_DIR
IMAGE_REGISTRY = "image-registry.openshift-image-registry.svc:5000"
PROJ_TOOLS = "e1e498-tools"

# fuel_grid_install_job.yaml's FUEL_RASTER_YEAR/FUEL_RASTER_KEY are constants today (both
# call sites pass "2026"/derived "fbp2026.tif"), same as every other baked-in value here --
# bump these and regenerate if the year changes. FUEL_GRID_INSTALL_SUSPEND from the real
# script never reaches the template at all (spec.suspend is hardcoded true, see the
# template); it only controls whether the caller runs a follow-up `oc patch
# job/... suspend:false` after applying, so it stays an external step, not a param here.
RESOURCES = [
    ("fuel-grid-install", "fuel_grid_install_job.yaml", {
        "NAME": "wps", "SUFFIX": "__SUFFIX__", "GLOBAL_NAME": "wps-global",
        "PROJ_TOOLS": PROJ_TOOLS, "IMAGE_REGISTRY": IMAGE_REGISTRY,
        "CRUNCHYDB_USER": "wps-crunchydb-16-__SUFFIX__-pguser-wps-crunchydb-16-__SUFFIX__",
        "PROJECT_NAMESPACE": "__NAMESPACE__",
        "FUEL_RASTER_YEAR": "2026", "FUEL_RASTER_KEY": "fbp2026.tif",
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
