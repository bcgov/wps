"""
Verifies that concurrent Lambda invocations (no VPC config) actually get distinct source
IPs -- the core assumption the whole k6-on-Lambda approach in this package depends on --
before spending real time/cost on a full k6 burst run against production.

Deploys a tiny, throwaway function (no k6 layer, no bundled script -- ip_probe_handler.py
just calls a public IP-echo service and returns what it saw), fans out --concurrency
invocations at once via the same run_fan_out used for real k6 runs, and reports how many
distinct IPs came back. Does not touch the actual load-test target or its rate limiter.

Usage:
    python3 -m wps_tools.load_testing.k6_lambda.verify_ip_diversity \\
        --region ca-central-1 --concurrency 50
"""

import argparse
import io
import json
import logging
import zipfile
from collections import Counter
from pathlib import Path

import boto3
from mypy_boto3_iam.client import IAMClient
from mypy_boto3_lambda.client import LambdaClient

from wps_tools.load_testing.k6_lambda.deploy_k6_lambda import (
    DEFAULT_ROLE_NAME,
    build_fan_out_lambda_client,
    deploy_function,
    ensure_execution_role,
    run_fan_out,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

HANDLER_PATH = Path(__file__).parent / "ip_probe_handler.py"
DEFAULT_FUNCTION_NAME = "k6-lambda-ip-probe"


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--region", required=True, help="AWS region to deploy/invoke in")
    parser.add_argument("--aws-profile", help="AWS named profile to use")
    parser.add_argument("--function-name", default=DEFAULT_FUNCTION_NAME)
    parser.add_argument("--role-name", default=DEFAULT_ROLE_NAME)
    parser.add_argument(
        "--concurrency",
        type=int,
        default=50,
        help="Concurrent invocations to fire (default: 50)",
    )
    parser.add_argument(
        "--hold-seconds",
        type=float,
        default=0,
        help="Seconds each invocation sleeps after fetching its IP (default: 0, a fast/cheap "
        "check). A near-instant probe lets Lambda reuse already-warm environments within the "
        "same burst faster than genuinely new ones get created, understating real diversity --"
        " confirmed live at --concurrency 250 (10->85->91 distinct IPs at concurrency "
        "10/100/250, a clear plateau). Set close to the real k6 script's own duration "
        "(~105s for asa_go_peak_burst.js) for a more representative estimate.",
    )
    return parser


def build_probe_zip(handler_source: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("handler.py", handler_source)
    return buffer.getvalue()


def deploy_probe_function(
    lambda_client: LambdaClient,
    iam_client: IAMClient,
    function_name: str,
    role_name: str,
    hold_seconds: float,
) -> str:
    role_arn = ensure_execution_role(iam_client, role_name)
    zip_bytes = build_probe_zip(HANDLER_PATH.read_bytes())
    return deploy_function(
        lambda_client,
        function_name=function_name,
        zip_bytes=zip_bytes,
        role_arn=role_arn,
        layer_arn=None,
        memory_mb=128,
        # +10s buffer over hold_seconds so the sleep itself never gets cut off by the
        # function timeout before it can return a result.
        timeout_seconds=int(hold_seconds) + 10,
        script_name="",  # unused by ip_probe_handler.py; deploy_function always sets this env var
    )


def summarize_ip_diversity(results: list[dict]) -> dict:
    ips = [r["ip"] for r in results if r.get("ip")]
    counts = Counter(ips)
    return {
        "invocations": len(results),
        "responses_with_ip": len(ips),
        "distinct_ips": len(counts),
        "ip_counts": dict(counts.most_common()),
    }


def main() -> None:
    args = create_parser().parse_args()
    session = boto3.Session(profile_name=args.aws_profile, region_name=args.region)
    lambda_client = build_fan_out_lambda_client(session, args.concurrency)
    iam_client: IAMClient = session.client("iam")

    deploy_probe_function(
        lambda_client, iam_client, args.function_name, args.role_name, args.hold_seconds
    )
    payload = {"hold_seconds": args.hold_seconds} if args.hold_seconds else {}
    results = run_fan_out(lambda_client, args.function_name, args.concurrency, payload)
    summary = summarize_ip_diversity(results)
    print(json.dumps(summary, indent=2))

    diversity_pct = 100 * summary["distinct_ips"] / summary["invocations"] if results else 0
    logger.info(
        "%d distinct IPs across %d invocations (%.0f%% diversity)",
        summary["distinct_ips"],
        summary["invocations"],
        diversity_pct,
    )


if __name__ == "__main__":
    main()
