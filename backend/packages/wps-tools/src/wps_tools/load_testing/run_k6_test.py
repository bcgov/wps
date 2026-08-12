"""
Create a k6 scenario on a deployed Distributed Load Testing on AWS (headless) stack,
upload the k6 script, and start a run, polling until it finishes.

Auth: this script does not implement Cognito login itself. Run `dlt login`
(or `dlt login --srp` / `dlt login --iam`) first using the DLT CLI -- it caches
an ID token plus AWS Identity Pool credentials in ~/.dlt/credentials.json, which
this script reads.

Note: POST /scenarios starts the run immediately, it is NOT a separate step
from `dlt scenarios start`. Do not call `dlt scenarios start` after this script
runs; that creates a second, competing run of the same test that races the first
one for the same ECS service name and both fail. This script polls for
completion itself for exactly that reason, instead of shelling out to
`dlt scenarios start --wait`.

Usage:
    python3 run_k6_test.py path/to/test.js --stack-name distributed-load-testing --region ca-central-1
    python3 run_k6_test.py path/to/test.js --api-endpoint https://xxx.execute-api.ca-central-1.amazonaws.com/prod \
        --scenarios-bucket my-scenarios-bucket --region ca-central-1
"""

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any, TypedDict

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
from mypy_boto3_cloudformation.client import CloudFormationClient
from mypy_boto3_s3.client import S3Client

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

DLT_CREDENTIALS_FILE = Path.home() / ".dlt" / "credentials.json"


class DltCredentials(TypedDict):
    idToken: str
    awsAccessKeyId: str
    awsSecretAccessKey: str
    awsSessionToken: str


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("script", help="Path to the k6 script (.js) to upload")
    parser.add_argument(
        "--stack-name",
        help="CloudFormation stack name; resolves --api-endpoint and --scenarios-bucket",
    )
    parser.add_argument("--api-endpoint", help="API Gateway base URL (overrides stack lookup)")
    parser.add_argument("--scenarios-bucket", help="ScenariosBucket name (overrides stack lookup)")
    parser.add_argument("--test-id", help="defaults to <script name>-<timestamp>")
    parser.add_argument("--test-name", help="defaults to --test-id")
    parser.add_argument("--test-description", default="k6 test created by run_k6_test.py")
    parser.add_argument("--region", required=True, help="AWS region to run the load test task in")
    parser.add_argument(
        "--task-count", type=int, default=1, help="Fargate tasks in that region (default: 1)"
    )
    parser.add_argument(
        "--concurrency", type=int, default=10, help="virtual users per task (default: 10)"
    )
    parser.add_argument("--ramp-up", default="30s", help="Taurus ramp-up (default: 30s)")
    parser.add_argument("--hold-for", default="2m", help="Taurus hold-for (default: 2m)")
    parser.add_argument(
        "--poll-interval", type=int, default=15, help="seconds between status checks (default: 15)"
    )
    parser.add_argument(
        "--max-wait",
        type=int,
        default=1800,
        help="give up waiting after this many seconds (default: 1800)",
    )
    parser.add_argument(
        "--aws-profile", help="AWS named profile to use for CloudFormation/S3 calls"
    )
    return parser


def extract_stack_outputs(outputs: dict[str, str]) -> tuple[str, str]:
    api_endpoint = next((v for k, v in outputs.items() if k.startswith("DLTApiEndpoint")), None)
    scenarios_bucket = outputs.get("ScenariosBucket")

    if not api_endpoint or not scenarios_bucket:
        raise RuntimeError(
            f"Could not resolve DLTApiEndpoint/ScenariosBucket from stack outputs: {outputs}"
        )

    return api_endpoint, scenarios_bucket


def resolve_stack_outputs(stack_name: str, aws_profile: str | None, region: str) -> tuple[str, str]:
    session = boto3.Session(profile_name=aws_profile, region_name=region)
    cfn: CloudFormationClient = session.client("cloudformation")
    [stack] = cfn.describe_stacks(StackName=stack_name)["Stacks"]
    outputs = {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}
    return extract_stack_outputs(outputs)


def load_dlt_credentials() -> DltCredentials:
    if not DLT_CREDENTIALS_FILE.exists():
        raise RuntimeError(f"No {DLT_CREDENTIALS_FILE} found. Run 'dlt login' first.")

    credentials = json.loads(DLT_CREDENTIALS_FILE.read_text())
    required = ["idToken", "awsAccessKeyId", "awsSecretAccessKey", "awsSessionToken"]
    missing = [field for field in required if not credentials.get(field)]
    if missing:
        raise RuntimeError(f"{DLT_CREDENTIALS_FILE} is missing {missing}. Run 'dlt login' again.")

    return credentials


def upload_script(
    script_path: Path, bucket: str, key: str, credentials: DltCredentials, region: str
) -> None:
    logger.info("Uploading %s to s3://%s/%s", script_path, bucket, key)
    s3: S3Client = boto3.client(
        "s3",
        region_name=region,
        aws_access_key_id=credentials["awsAccessKeyId"],
        aws_secret_access_key=credentials["awsSecretAccessKey"],
        aws_session_token=credentials["awsSessionToken"],
    )
    s3.upload_file(str(script_path), bucket, key)


def build_scenario_payload(
    test_id: str,
    test_name: str,
    test_description: str,
    region: str,
    task_count: int,
    concurrency: int,
    ramp_up: str,
    hold_for: str,
    script_file_name: str,
) -> dict[str, Any]:
    return {
        "testId": test_id,
        "testName": test_name,
        "testDescription": test_description,
        "testType": "k6",
        "fileType": "script",
        # Required despite being optional in the create-scenario validation schema: the backend's
        # DynamoDB update (updateTestDBEntry) references a ":sl" (showLive) placeholder in its
        # UpdateExpression unconditionally, so omitting this field entirely causes a 500
        # ("Invalid UpdateExpression... attribute value: :sl") even though creation validates fine.
        # We don't use the web console, so this is never actually true -- just present.
        "showLive": False,
        "testTaskConfigs": [
            {"region": region, "taskCount": task_count, "concurrency": concurrency}
        ],
        # Informational in the console (real Fargate quota check); the API only requires
        # dltAvailableTasks to be present, so this just reflects what we're requesting.
        "regionalTaskDetails": {region: {"dltAvailableTasks": task_count}},
        "testScenario": {
            "execution": [
                {
                    "executor": "k6",
                    "concurrency": concurrency,
                    "ramp-up": ramp_up,
                    "hold-for": hold_for,
                    "scenario": test_name,
                }
            ],
            "scenarios": {test_name: {"script": script_file_name}},
        },
    }


def sanitize_test_id(value: str) -> str:
    """testId must contain only alphanumeric characters and hyphens."""
    return re.sub(r"[^A-Za-z0-9-]", "-", value)


def derive_test_names(
    script_path: Path, test_id: str | None, test_name: str | None
) -> tuple[str, str, str]:
    resolved_test_id = test_id or sanitize_test_id(f"{script_path.stem}-{int(time.time())}")
    resolved_test_name = test_name or resolved_test_id
    script_file_name = f"{resolved_test_id}{script_path.suffix}"
    return resolved_test_id, resolved_test_name, script_file_name


def sign_request(
    method: str, url: str, region: str, credentials: DltCredentials, body: bytes
) -> dict[str, str]:
    """SigV4-sign a request for API Gateway's AWS_IAM authorizer, using the Cognito Identity Pool's
    temporary credentials -- the /scenarios endpoint requires execute-api:Invoke, not a bearer token."""
    aws_credentials = Credentials(
        access_key=credentials["awsAccessKeyId"],
        secret_key=credentials["awsSecretAccessKey"],
        token=credentials["awsSessionToken"],
    )
    request = AWSRequest(
        method=method, url=url, data=body, headers={"Content-Type": "application/json"}
    )
    SigV4Auth(aws_credentials, "execute-api", region).add_auth(request)
    return dict(request.headers)


def create_scenario(
    api_endpoint: str, region: str, credentials: DltCredentials, payload: dict[str, Any]
) -> None:
    test_id = payload["testId"]
    logger.info("Creating scenario %s", test_id)
    url = f"{api_endpoint.rstrip('/')}/scenarios"
    body = json.dumps(payload).encode()
    headers = sign_request("POST", url, region, credentials, body)

    response = requests.post(url, data=body, headers=headers)
    if not response.ok:
        raise RuntimeError(
            f"POST /scenarios failed with HTTP {response.status_code}: {response.text}"
        )
    logger.info("Scenario %s created.", test_id)


# The backend has more transient statuses than any allowlist we've observed so far
# (queued, provisioning, running, "cleaning up", "parsing results", ...), so treat only
# these known-final statuses as terminal and everything else as still in progress.
TERMINAL_STATUSES = {"complete", "success", "failed", "cancelled", "canceled"}


def is_terminal_status(status: str | None) -> bool:
    return status is not None and status.lower() in TERMINAL_STATUSES


def get_scenario_status(
    api_endpoint: str, region: str, credentials: DltCredentials, test_id: str
) -> str | None:
    url = f"{api_endpoint.rstrip('/')}/scenarios/{test_id}?history=false&latest=false"
    headers = sign_request("GET", url, region, credentials, b"")
    response = requests.get(url, headers=headers)
    if not response.ok:
        raise RuntimeError(
            f"GET /scenarios/{test_id} failed with HTTP {response.status_code}: {response.text}"
        )
    status: str | None = response.json().get("status")
    return status


def wait_for_completion(
    api_endpoint: str,
    region: str,
    credentials: DltCredentials,
    test_id: str,
    poll_interval: int,
    max_wait: int,
) -> str | None:
    elapsed = 0
    while True:
        status = get_scenario_status(api_endpoint, region, credentials, test_id)
        logger.info("Test %s status: %s", test_id, status)
        if is_terminal_status(status):
            return status
        if elapsed >= max_wait:
            raise TimeoutError(
                f"Test {test_id} did not reach a terminal status within {max_wait}s (last seen: {status})"
            )
        time.sleep(poll_interval)
        elapsed += poll_interval


def main() -> None:
    args = create_parser().parse_args()

    script_path = Path(args.script)
    if not script_path.is_file():
        logger.error("Script file not found: %s", script_path)
        sys.exit(1)

    api_endpoint = args.api_endpoint
    scenarios_bucket = args.scenarios_bucket
    if not api_endpoint or not scenarios_bucket:
        if not args.stack_name:
            logger.error("Provide --stack-name, or both --api-endpoint and --scenarios-bucket")
            sys.exit(1)
        resolved_endpoint, resolved_bucket = resolve_stack_outputs(
            args.stack_name, args.aws_profile, args.region
        )
        api_endpoint = api_endpoint or resolved_endpoint
        scenarios_bucket = scenarios_bucket or resolved_bucket

    test_id, test_name, script_file_name = derive_test_names(
        script_path, args.test_id, args.test_name
    )

    credentials = load_dlt_credentials()

    # The Cognito authenticated role's IAM policy scopes s3:PutObject to ScenariosBucket/public/*,
    # matching Amplify Storage's "public" access level, which the web console uploads through.
    upload_script(
        script_path,
        scenarios_bucket,
        f"public/test-scenarios/k6/{script_file_name}",
        credentials,
        args.region,
    )

    payload = build_scenario_payload(
        test_id,
        test_name,
        args.test_description,
        args.region,
        args.task_count,
        args.concurrency,
        args.ramp_up,
        args.hold_for,
        script_file_name,
    )
    create_scenario(api_endpoint, args.region, credentials, payload)

    # create_scenario's POST /scenarios already started the run -- do not also call
    # `dlt scenarios start`, which would start a second, competing run of the same test.
    status = wait_for_completion(
        api_endpoint, args.region, credentials, test_id, args.poll_interval, args.max_wait
    )
    logger.info("Test %s finished with status: %s", test_id, status)
    if status is None or status.lower() not in {"complete", "success"}:
        sys.exit(1)


if __name__ == "__main__":
    main()
