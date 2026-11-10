"""Check requested memory in dev before provisioning a PR environment."""

import json
import os
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

NAMESPACE = "e1e498-dev"
# new environments need their full allocation; updates only need rollout headroom
NEW_ENVIRONMENT_GI = 20
EXISTING_ENVIRONMENT_GI = 8


def memory_bytes(value):
    match = re.fullmatch(r"(\d+(?:\.\d+)?)(Ki|Mi|Gi|Ti)?", str(value))
    if not match:
        raise ValueError(f"Unsupported memory quantity: {value}")
    power = {None: 0, "Ki": 1, "Mi": 2, "Gi": 3, "Ti": 4}[match[2]]
    return Decimal(match[1]) * 1024**power


def oc_get(*args):
    result = subprocess.run(
        ["oc", "-n", NAMESPACE, "get", *args, "-o", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else None


def has_ready_application(deployment):
    # a database or partial deployment alone does not qualify for the smaller update budget
    if not deployment:
        return False
    desired = deployment["spec"].get("replicas", 1)
    return desired > 0 and deployment.get("status", {}).get("readyReplicas", 0) >= desired


def check_capacity(quota, existing):
    # quota admission counts requested memory, not measured usage or container limits
    used = quota["status"]["used"]["requests.memory"]
    limit = quota["status"]["hard"]["requests.memory"]
    available_gi = (memory_bytes(limit) - memory_bytes(used)) / 1024**3
    required_gi = EXISTING_ENVIRONMENT_GI if existing else NEW_ENVIRONMENT_GI
    allowed = available_gi >= required_gi
    report = (
        f"Dev requested memory: {used} of {limit}. "
        f"Available: {available_gi:.2f}Gi. Required headroom: {required_gi}Gi.\n"
    )
    if not allowed:
        report += (
            "Insufficient memory. The workflow will add `skip-dev-deploy`. "
            "Existing resources remain. Remove the label to retry.\n"
        )
    return allowed, report


def main():
    if len(sys.argv) != 2 or not re.fullmatch(r"[1-9]\d*", sys.argv[1]):
        raise ValueError("Usage: check_dev_capacity.py <positive PR number>")
    quota = oc_get("resourcequota/compute-long-running-quota")
    deployment = oc_get(f"deployment/wps-pr-{sys.argv[1]}", "--ignore-not-found=true")
    allowed, report = check_capacity(quota, has_ready_application(deployment))
    print(report)
    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a") as stream:
            stream.write(f"deploy={str(allowed).lower()}\n")
    if output := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(output).open("a") as stream:
            stream.write(report)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(f"Could not read dev resources: {error.stderr.strip()}")
    except (KeyError, TypeError, ValueError, OSError) as error:
        sys.exit(f"Could not check dev memory: {error}")
