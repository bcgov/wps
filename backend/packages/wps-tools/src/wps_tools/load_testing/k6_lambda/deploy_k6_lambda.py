"""
Build and run a k6-on-Lambda load generator: k6 itself, running inside a Lambda function,
invoked with high concurrency to get many distinct source IPs.

The DLT (Distributed Load Testing on AWS) stack in ../manage_dlt.py runs
its load-tester as ECS Fargate tasks inside this account's Prod-App-A/Prod-App-B subnets.
Those subnets have no Internet Gateway or NAT Gateway of their own -- 0.0.0.0/0 routes
through a Transit Gateway to a centralized landing-zone egress account, so every Fargate
task, regardless of --task-count, egresses through the same small, fixed set of NAT IPs.
That makes Fargate/DLT useless for testing a gateway that rate-limits per source IP.

A Lambda function *without* VPC configuration bypasses this VPC's networking entirely and
uses AWS's own shared, region-wide Lambda IP pool instead -- giving genuine source-IP
diversity that scales with invocation concurrency, the same role --task-count played for
Fargate. See README.md for the full picture, quotas to check, and known gotchas.

Usage:
    # Fan out across multiple regions -- each has its own separate Lambda IP pool, so this
    # multiplies source-IP diversity beyond what --concurrency alone gets in one region:
    python3 -m wps_tools.load_testing.k6_lambda.deploy_k6_lambda deploy \\
        ../k6_scripts/asa_go_peak_burst.js --regions ca-central-1,ca-west-1,us-west-1,us-west-2
    python3 -m wps_tools.load_testing.k6_lambda.deploy_k6_lambda run \\
        --concurrency 250 --regions ca-central-1,ca-west-1,us-west-1,us-west-2

    # Or target a single region with --region instead:
    python3 -m wps_tools.load_testing.k6_lambda.deploy_k6_lambda deploy \\
        ../k6_scripts/asa_go_peak_burst.js --region ca-central-1
    python3 -m wps_tools.load_testing.k6_lambda.deploy_k6_lambda run \\
        --concurrency 250 --region ca-central-1
"""

import argparse
import hashlib
import io
import json
import logging
import sys
import tarfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
import requests
from botocore.config import Config
from mypy_boto3_iam.client import IAMClient
from mypy_boto3_lambda.client import LambdaClient

from wps_tools.load_testing import REQUEST_TIMEOUT

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

HANDLER_PATH = Path(__file__).parent / "handler.py"

# Pinned to a specific release and checksummed below so a compromised or rewritten upstream
# artifact can't be silently downloaded and made executable -- same rationale as
# manage_dlt.py's DLT_CLI_SHA256 pin.
K6_VERSION = "v2.2.0"
K6_TARBALL_URL = f"https://github.com/grafana/k6/releases/download/{K6_VERSION}/k6-{K6_VERSION}-linux-amd64.tar.gz"
K6_TARBALL_SHA256 = "b5a8003c86f35f5cd5ceef1490312c48e587696c94d998cefc6d7b3b4cb1597d"
K6_TARBALL_MEMBER = f"k6-{K6_VERSION}-linux-amd64/k6"

DEFAULT_LAYER_NAME = "k6-runtime"
DEFAULT_FUNCTION_NAME = "k6-lambda-load-gen"
DEFAULT_ROLE_NAME = "k6-lambda-load-gen-role"

LAMBDA_TRUST_POLICY = json.dumps(
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
)
BASIC_EXECUTION_POLICY_ARN = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    region_group = common.add_mutually_exclusive_group(required=True)
    region_group.add_argument("--region", help="AWS region to deploy/invoke in")
    region_group.add_argument(
        "--regions",
        help="Comma-separated AWS regions to fan out across instead of a single --region -- "
        "each region has its own separate Lambda IP pool, so this multiplies source-IP "
        "diversity (and concurrent-execution quota) beyond what --concurrency alone gets you "
        "in one region (e.g. ca-central-1,ca-west-1,us-west-1,us-west-2)",
    )
    common.add_argument("--aws-profile", help="AWS named profile to use")
    common.add_argument("--function-name", default=DEFAULT_FUNCTION_NAME)

    deploy_parser = subparsers.add_parser(
        "deploy", parents=[common], help="Build the k6 layer and deploy the Lambda function"
    )
    deploy_parser.add_argument("script", help="Path to the k6 script (.js) to bundle and run")
    deploy_parser.add_argument("--layer-name", default=DEFAULT_LAYER_NAME)
    deploy_parser.add_argument("--role-name", default=DEFAULT_ROLE_NAME)
    deploy_parser.add_argument(
        "--memory-mb",
        type=int,
        default=512,
        help="Function memory in MB (default: 512 -- this only runs k6 for one slice of "
        "the aggregate load, not the full peak, so it doesn't need much)",
    )
    deploy_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=150,
        help="Function timeout (default: 150s -- must exceed the k6 script's own total "
        "ramp/hold/ramp-down duration, or invocations will be killed mid-run)",
    )

    run_parser = subparsers.add_parser(
        "run", parents=[common], help="Fan out concurrent invocations of the deployed function"
    )
    run_parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent Lambda invocations to fire per region (default: 10 -- this "
        "is the analog of manage_dlt.py's --task-count; start small). With --regions, this "
        "many invocations are fired in EACH region, so total invocations scale with region "
        "count too",
    )
    run_parser.add_argument(
        "--target-rps",
        type=float,
        help="Per-invocation target requests/second, forwarded to the k6 script's TARGET_RPS "
        "env var (default: whatever the script itself defaults to)",
    )

    return parser


def resolve_regions(args: argparse.Namespace) -> list[str]:
    if args.regions:
        regions = [r.strip() for r in args.regions.split(",") if r.strip()]
        if not regions:
            raise ValueError("--regions was given but contained no region names")
        return regions
    return [args.region]


def download_k6_binary() -> bytes:
    logger.info("Downloading k6 %s", K6_VERSION)
    response = requests.get(K6_TARBALL_URL, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    digest = hashlib.sha256(response.content).hexdigest()
    if digest != K6_TARBALL_SHA256:
        raise RuntimeError(
            f"k6 download from {K6_TARBALL_URL} has unexpected SHA256 {digest} "
            f"(expected {K6_TARBALL_SHA256}). Refusing to use it -- if upstream genuinely "
            "published a new build at this tag, verify it and update K6_TARBALL_SHA256."
        )
    with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz") as tar:
        extracted = tar.extractfile(K6_TARBALL_MEMBER)
        if extracted is None:
            raise RuntimeError(f"{K6_TARBALL_MEMBER} not found in downloaded tarball")
        return extracted.read()


def build_layer_zip(k6_binary: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        info = zipfile.ZipInfo("opt/k6")
        info.external_attr = 0o755 << 16  # preserve the executable bit inside the zip
        zip_file.writestr(info, k6_binary)
    return buffer.getvalue()


def build_function_zip(handler_source: bytes, script_bytes: bytes, script_name: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("handler.py", handler_source)
        zip_file.writestr(script_name, script_bytes)
    return buffer.getvalue()


def ensure_execution_role(iam_client: IAMClient, role_name: str) -> str:
    try:
        role = iam_client.get_role(RoleName=role_name)
        logger.info("Using existing IAM role %s", role_name)
        return role["Role"]["Arn"]
    except iam_client.exceptions.NoSuchEntityException:
        pass

    logger.info("Creating IAM role %s", role_name)
    role = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=LAMBDA_TRUST_POLICY,
        Description="Execution role for the k6-on-Lambda load generator",
    )
    iam_client.attach_role_policy(RoleName=role_name, PolicyArn=BASIC_EXECUTION_POLICY_ARN)
    return role["Role"]["Arn"]


def publish_k6_layer(lambda_client: LambdaClient, layer_name: str, zip_bytes: bytes) -> str:
    logger.info("Publishing layer %s (%d bytes)", layer_name, len(zip_bytes))
    response = lambda_client.publish_layer_version(
        LayerName=layer_name,
        Content={"ZipFile": zip_bytes},
        CompatibleRuntimes=["python3.13"],
        CompatibleArchitectures=["x86_64"],
    )
    return response["LayerVersionArn"]


def _function_exists(lambda_client: LambdaClient, function_name: str) -> bool:
    try:
        lambda_client.get_function(FunctionName=function_name)
        return True
    except lambda_client.exceptions.ResourceNotFoundException:
        return False


def _create_function_with_retry(
    lambda_client: LambdaClient,
    *,
    function_name: str,
    zip_bytes: bytes,
    role_arn: str,
    layer_arn: str | None,
    memory_mb: int,
    timeout_seconds: int,
    script_name: str,
    attempts: int = 6,
    delay_seconds: int = 5,
) -> None:
    # A newly-created IAM role isn't always immediately assumable by Lambda -- IAM's
    # eventual consistency means the very first create_function call can fail even though
    # the role genuinely exists. Retry rather than failing outright.
    for attempt in range(1, attempts + 1):
        try:
            lambda_client.create_function(
                FunctionName=function_name,
                Runtime="python3.13",
                Role=role_arn,
                Handler="handler.handler",
                Code={"ZipFile": zip_bytes},
                Layers=[layer_arn] if layer_arn else [],
                MemorySize=memory_mb,
                Timeout=timeout_seconds,
                # SCRIPT_NAME lets 'run' rediscover which bundled script to invoke without
                # having to pass it on every call -- the handler falls back to this env var
                # when the invoke payload doesn't set script_name explicitly.
                Environment={"Variables": {"SCRIPT_NAME": script_name}},
                # Deliberately no VpcConfig -- see the module docstring for why.
            )
            return
        except lambda_client.exceptions.InvalidParameterValueException:
            if attempt == attempts:
                raise
            logger.info("Role not yet assumable by Lambda, retrying (%d/%d)...", attempt, attempts)
            time.sleep(delay_seconds)


def deploy_function(
    lambda_client: LambdaClient,
    *,
    function_name: str,
    zip_bytes: bytes,
    role_arn: str,
    layer_arn: str | None,
    memory_mb: int,
    timeout_seconds: int,
    script_name: str,
) -> str:
    if _function_exists(lambda_client, function_name):
        logger.info("Updating function %s", function_name)
        lambda_client.update_function_code(FunctionName=function_name, ZipFile=zip_bytes)
        lambda_client.get_waiter("function_updated").wait(FunctionName=function_name)
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Role=role_arn,
            Layers=[layer_arn] if layer_arn else [],
            MemorySize=memory_mb,
            Timeout=timeout_seconds,
            Environment={"Variables": {"SCRIPT_NAME": script_name}},
        )
        lambda_client.get_waiter("function_updated").wait(FunctionName=function_name)
    else:
        logger.info("Creating function %s", function_name)
        _create_function_with_retry(
            lambda_client,
            function_name=function_name,
            zip_bytes=zip_bytes,
            role_arn=role_arn,
            layer_arn=layer_arn,
            memory_mb=memory_mb,
            timeout_seconds=timeout_seconds,
            script_name=script_name,
        )
        lambda_client.get_waiter("function_active").wait(FunctionName=function_name)

    config = lambda_client.get_function(FunctionName=function_name)["Configuration"]
    return config["FunctionArn"]


def invoke_once(lambda_client: LambdaClient, function_name: str, payload: dict) -> dict:
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode(),
    )
    body = json.loads(response["Payload"].read())
    if response.get("FunctionError"):
        logger.error("Invocation error: %s", body)
    return body


def build_fan_out_lambda_client(session: boto3.Session, concurrency: int) -> LambdaClient:
    """boto3's default connection pool is 10 -- run_fan_out spins up one thread per
    --concurrency, all sharing one client, so at any concurrency above ~10 threads start
    contending for pooled connections. Confirmed live: at --concurrency 250 this produced a
    transient DNS resolution failure (Failed to resolve 'lambda.<region>.amazonaws.com')
    that crashed the entire run before the fix here and in run_fan_out's per-future error
    handling. Sized to concurrency (with a floor at boto3's own default) so every thread can
    hold its own connection instead of queueing for one.

    read_timeout is also raised past Lambda's own 900s hard per-invocation ceiling.
    Confirmed live: botocore's default read_timeout is only 60s, so a synchronous
    (RequestResponse) invoke() of anything that legitimately takes longer than that (e.g.
    verify_ip_diversity.py's --hold-seconds, or a real k6 script's ramp/hold/ramp-down) gets
    a spurious client-side timeout well before the Lambda invocation itself could possibly
    finish -- every one of --concurrency threads hitting that at once is itself what produced
    the flood of connection errors, not a real AWS-side failure."""
    return session.client(
        "lambda",
        config=Config(max_pool_connections=max(concurrency, 10), read_timeout=910),
    )


def run_fan_out(
    lambda_client: LambdaClient,
    function_name: str,
    concurrency: int,
    payload: dict,
) -> list[dict]:
    logger.info("Firing %d concurrent invocations of %s", concurrency, function_name)
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(invoke_once, lambda_client, function_name, payload)
            for _ in range(concurrency)
        ]
        results = []
        for future in futures:
            try:
                results.append(future.result())
            except Exception as e:
                # A single transient failure (e.g. a connection/DNS hiccup under high thread
                # concurrency) must not discard every other invocation's result -- confirmed
                # live: firing this many threads through one client can produce exactly that.
                logger.error("Invocation failed: %s", e)
                results.append({"exit_code": None, "error": str(e)})
        return results


def aggregate_summaries(results: list[dict]) -> dict:
    """Sums k6's per-invocation --summary-export output across every invocation.

    Schema confirmed by actually running this handler locally against the real AWS Lambda
    Python base image via podman + its built-in Runtime Interface Emulator (see README.md),
    not assumed: metrics are keyed by name under metrics.<name>.count for Counter-type
    metrics (http_reqs, and our custom rate_limited_responses counter); per-check pass/fail
    counts live under root_group.checks.<check name>.{passes,fails}.

    One important, confirmed-live gotcha this relies on: a Counter that's never incremented
    (e.g. an invocation that saw zero 429s) is OMITTED from metrics entirely -- it does NOT
    appear with count=0. Every metrics.get(...) below defaults missing keys to {} / 0 for
    exactly this reason; a KeyError here would mean the happy path (no rate limiting hit)
    breaks aggregation, which defeats the point of tracking it.

    This is intentionally specific to asa_go_peak_burst.js's own checks/counter names, not a
    generic k6-summary parser -- reasonable since this module always runs a known script.
    """
    total_requests = 0
    total_rate_limited = 0
    checks: dict[str, dict[str, int]] = {}

    for result in results:
        summary = result.get("summary")
        if not summary:
            continue
        metrics = summary.get("metrics", {})
        total_requests += metrics.get("http_reqs", {}).get("count", 0)
        total_rate_limited += metrics.get("rate_limited_responses", {}).get("count", 0)

        for name, check in summary.get("root_group", {}).get("checks", {}).items():
            bucket = checks.setdefault(name, {"passes": 0, "fails": 0})
            bucket["passes"] += check.get("passes", 0)
            bucket["fails"] += check.get("fails", 0)

    succeeded = sum(1 for r in results if r.get("exit_code") == 0)
    return {
        "invocations": len(results),
        "succeeded_invocations": succeeded,
        "failed_invocations": len(results) - succeeded,
        "total_requests": total_requests,
        "total_rate_limited": total_rate_limited,
        "checks": checks,
    }


def run_deploy(args: argparse.Namespace) -> None:
    script_path = Path(args.script)
    if not script_path.is_file():
        logger.error("Script not found: %s", script_path)
        sys.exit(1)

    regions = resolve_regions(args)

    k6_binary = download_k6_binary()
    layer_zip = build_layer_zip(k6_binary)
    function_zip = build_function_zip(
        HANDLER_PATH.read_bytes(), script_path.read_bytes(), script_path.name
    )

    # IAM has no per-region endpoint -- one role, created via whichever region's session,
    # is a valid Role ARN for every region's function below. No need to recreate it per region.
    iam_session = boto3.Session(profile_name=args.aws_profile, region_name=regions[0])
    role_arn = ensure_execution_role(iam_session.client("iam"), args.role_name)

    def deploy_to_region(region: str) -> str:
        session = boto3.Session(profile_name=args.aws_profile, region_name=region)
        lambda_client: LambdaClient = session.client("lambda")
        layer_arn = publish_k6_layer(lambda_client, args.layer_name, layer_zip)
        return deploy_function(
            lambda_client,
            function_name=args.function_name,
            zip_bytes=function_zip,
            role_arn=role_arn,
            layer_arn=layer_arn,
            memory_mb=args.memory_mb,
            timeout_seconds=args.timeout_seconds,
            script_name=script_path.name,
        )

    failed_regions: list[str] = []
    with ThreadPoolExecutor(max_workers=len(regions)) as executor:
        future_to_region = {executor.submit(deploy_to_region, r): r for r in regions}
        for future, region in future_to_region.items():
            try:
                logger.info("Deployed %s in %s", future.result(), region)
            except Exception as e:
                # One region's deploy failing (e.g. a quota or permissions issue specific to
                # that region) shouldn't abort the others -- report every region's outcome.
                logger.error("Deploy failed in %s: %s", region, e)
                failed_regions.append(region)

    if failed_regions:
        logger.error(
            "Deploy failed in %d/%d region(s): %s",
            len(failed_regions),
            len(regions),
            ", ".join(failed_regions),
        )
        sys.exit(1)

    logger.info(
        "Run it with: python3 -m wps_tools.load_testing.k6_lambda.deploy_k6_lambda run "
        "--function-name %s --%s %s --concurrency <N>",
        args.function_name,
        "regions" if args.regions else "region",
        ",".join(regions),
    )


def run_run(args: argparse.Namespace) -> None:
    regions = resolve_regions(args)

    def run_in_region(region: str) -> list[dict]:
        session = boto3.Session(profile_name=args.aws_profile, region_name=region)
        lambda_client = build_fan_out_lambda_client(session, args.concurrency)

        # Fail fast with a clear error if the function doesn't exist in this region or was
        # never deployed with a bundled script (SCRIPT_NAME), rather than letting every one
        # of --concurrency invocations fail individually with a less obvious handler error.
        config = lambda_client.get_function(FunctionName=args.function_name)["Configuration"]
        script_name = config.get("Environment", {}).get("Variables", {}).get("SCRIPT_NAME")
        if not script_name:
            raise RuntimeError(
                f"{args.function_name} in {region} has no SCRIPT_NAME set -- deploy it first "
                "with the 'deploy' command"
            )

        # No script_name in the payload -- the handler falls back to the function's own
        # SCRIPT_NAME env var (set at deploy time), which is all a normal run needs.
        payload: dict = {}
        if args.target_rps is not None:
            payload["target_rps"] = args.target_rps

        return run_fan_out(lambda_client, args.function_name, args.concurrency, payload)

    per_region: dict[str, list[dict]] = {}
    with ThreadPoolExecutor(max_workers=len(regions)) as executor:
        future_to_region = {executor.submit(run_in_region, r): r for r in regions}
        for future, region in future_to_region.items():
            try:
                per_region[region] = future.result()
            except Exception as e:
                logger.error("Run failed in %s: %s", region, e)
                sys.exit(1)

    all_results = [result for results in per_region.values() for result in results]
    summary = aggregate_summaries(all_results)
    if len(regions) > 1:
        summary["by_region"] = {
            region: aggregate_summaries(results) for region, results in per_region.items()
        }
    print(json.dumps(summary, indent=2))
    if summary["failed_invocations"]:
        logger.warning(
            "%d/%d invocations did not exit cleanly -- see individual results for details",
            summary["failed_invocations"],
            summary["invocations"],
        )


def main() -> None:
    args = create_parser().parse_args()
    if args.command == "deploy":
        run_deploy(args)
    else:
        run_run(args)


if __name__ == "__main__":
    main()
