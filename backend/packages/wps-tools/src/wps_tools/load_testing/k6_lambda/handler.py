"""
Lambda entry point that runs a k6 script (bundled alongside this file at deploy time) via
the k6 binary from the layer at /opt/k6.

This function deliberately has no VPC configuration -- that's the entire reason it exists.
Fargate tasks in this account's Prod-App-A/Prod-App-B subnets all egress through the same
handful of NAT IPs behind a Transit Gateway (see ../k6_lambda/README.md), which makes them
useless for a test that needs many distinct source IPs. A Lambda function *without* VPC
config uses AWS's own shared, region-wide Lambda networking instead, which isn't bound by
this account's landing-zone routing at all.
"""

import json
import os
import subprocess

K6_BINARY = "/opt/k6"


def handler(event: dict, context) -> dict:
    # SCRIPT_NAME is set as a function-level env var at deploy time (deploy_k6_lambda.py's
    # deploy_function); the event payload can override it per-invocation if needed, but
    # normal 'run' invocations don't need to pass it at all.
    script_name = event.get("script_name") or os.environ.get("SCRIPT_NAME")
    if not script_name:
        raise ValueError(
            "No script_name in the event payload and no SCRIPT_NAME env var set -- redeploy "
            "with deploy_k6_lambda.py's 'deploy' command, or pass script_name explicitly"
        )
    script_path = f"/var/task/{script_name}"

    env = {
        **os.environ,
        # Lambda's filesystem is read-only except /tmp -- k6 needs a writable $HOME for its
        # own config/cache, which otherwise defaults somewhere unwritable and fails outright.
        "HOME": "/tmp",
        # Skip k6's own outbound update-check/telemetry ping on startup -- irrelevant here
        # and one less unrelated outbound call per cold start.
        "K6_DISABLE_USAGE_REPORT": "true",
    }
    target_rps = event.get("target_rps")
    if target_rps is not None:
        env["TARGET_RPS"] = str(target_rps)

    summary_path = "/tmp/summary.json"
    # Leave a buffer before Lambda's own timeout kills the invocation, so k6 gets a chance
    # to exit and write its summary rather than being hard-killed mid-write.
    remaining_seconds = context.get_remaining_time_in_millis() / 1000
    subprocess_timeout = max(remaining_seconds - 5, 1)

    try:
        result = subprocess.run(
            [K6_BINARY, "run", "--summary-export", summary_path, script_path],
            env=env,
            capture_output=True,
            text=True,
            timeout=subprocess_timeout,
        )
        exit_code = result.returncode
        stdout_tail = result.stdout[-2000:]
        stderr_tail = result.stderr[-2000:]
    except subprocess.TimeoutExpired as e:
        exit_code = None
        stdout_tail = (e.stdout or "")[-2000:]
        stderr_tail = "k6 did not exit before the Lambda timeout buffer"

    summary = None
    if os.path.exists(summary_path):
        with open(summary_path) as f:
            summary = json.load(f)

    return {
        "exit_code": exit_code,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "summary": summary,
    }
