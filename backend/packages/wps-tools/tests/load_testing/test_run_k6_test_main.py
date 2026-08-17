"""
Tests for run_k6_test's create_parser, load_dlt_credentials, wait_for_completion, and main --
the pieces test_run_k6_test.py (pure logic) and test_run_k6_test_aws.py (individual AWS/HTTP
calls) don't reach, since they need argv/env/filesystem/multi-call wiring.
"""

import json
import sys

import boto3
import pytest
import responses
from moto import mock_aws

from wps_tools.load_testing import run_k6_test
from wps_tools.load_testing.run_k6_test import (
    create_parser,
    load_dlt_credentials,
    main,
    wait_for_completion,
)

REGION = "ca-central-1"
API_ENDPOINT = "https://example.execute-api.ca-central-1.amazonaws.com/prod"

VALID_CREDENTIALS = {
    "idToken": "id-token",
    "awsAccessKeyId": "AKIAEXAMPLE",
    "awsSecretAccessKey": "secret",
    "awsSessionToken": "session-token",
}


@pytest.fixture
def aws():
    with mock_aws():
        yield boto3.Session(region_name=REGION)


@pytest.fixture
def dlt_credentials_file(tmp_path, monkeypatch):
    credentials_file = tmp_path / "credentials.json"
    monkeypatch.setattr(run_k6_test, "DLT_CREDENTIALS_FILE", credentials_file)
    return credentials_file


def test_create_parser_defaults():
    args = create_parser().parse_args(["script.js", "--region", REGION])

    assert args.script == "script.js"
    assert args.region == REGION
    assert args.task_count == 1
    assert args.concurrency == 10
    assert args.ramp_up == "30s"
    assert args.poll_interval == 15
    assert args.max_wait == 1800


def test_create_parser_requires_region():
    with pytest.raises(SystemExit):
        create_parser().parse_args(["script.js"])


def test_load_dlt_credentials_missing_file_raises(dlt_credentials_file):
    with pytest.raises(RuntimeError, match="Run 'dlt login'"):
        load_dlt_credentials()


def test_load_dlt_credentials_missing_fields_raises(dlt_credentials_file):
    dlt_credentials_file.write_text(json.dumps({"idToken": "abc"}))

    with pytest.raises(RuntimeError, match="missing"):
        load_dlt_credentials()


def test_load_dlt_credentials_success(dlt_credentials_file):
    dlt_credentials_file.write_text(json.dumps(VALID_CREDENTIALS))

    assert load_dlt_credentials() == VALID_CREDENTIALS


@responses.activate
def test_wait_for_completion_returns_on_terminal_status():
    responses.add(responses.GET, f"{API_ENDPOINT}/scenarios/abc-123", json={"status": "complete"}, status=200)

    status = wait_for_completion(API_ENDPOINT, REGION, VALID_CREDENTIALS, "abc-123", poll_interval=0, max_wait=60)

    assert status == "complete"


@responses.activate
def test_wait_for_completion_times_out():
    responses.add(responses.GET, f"{API_ENDPOINT}/scenarios/abc-123", json={"status": "running"}, status=200)

    with pytest.raises(TimeoutError):
        wait_for_completion(API_ENDPOINT, REGION, VALID_CREDENTIALS, "abc-123", poll_interval=0, max_wait=0)


def test_main_script_not_found_exits(monkeypatch, tmp_path, dlt_credentials_file):
    monkeypatch.setattr(sys, "argv", ["run_k6_test.py", str(tmp_path / "missing.js"), "--region", REGION])

    with pytest.raises(SystemExit):
        main()


def test_main_missing_endpoint_args_exits(monkeypatch, tmp_path, dlt_credentials_file):
    script = tmp_path / "smoke.js"
    script.write_text("// k6 script")
    monkeypatch.setattr(sys, "argv", ["run_k6_test.py", str(script), "--region", REGION])

    with pytest.raises(SystemExit):
        main()


def test_main_nonexistent_stack_exits_cleanly(aws, tmp_path, monkeypatch, dlt_credentials_file):
    """A stale/misspelled --stack-name must produce a clean sys.exit(1), not a raw
    botocore ClientError traceback from describe_stacks."""
    script = tmp_path / "smoke.js"
    script.write_text("// k6 script")
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_k6_test.py", str(script), "--stack-name", "does-not-exist", "--region", REGION],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def _setup_stack_and_bucket(aws, bucket_name="test-scenarios-bucket"):
    cfn = aws.client("cloudformation")
    s3 = aws.client("s3")
    s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": REGION})
    template = json.dumps(
        {
            "Resources": {"Topic": {"Type": "AWS::SNS::Topic", "Properties": {}}},
            "Outputs": {
                "DLTApiEndpointD98B09AC": {"Value": API_ENDPOINT},
                "ScenariosBucket": {"Value": bucket_name},
            },
        }
    )
    cfn.create_stack(StackName="my-stack", TemplateBody=template)
    cfn.get_waiter("stack_create_complete").wait(StackName="my-stack")


@responses.activate
def test_main_full_success(aws, tmp_path, monkeypatch, dlt_credentials_file):
    _setup_stack_and_bucket(aws)
    dlt_credentials_file.write_text(json.dumps(VALID_CREDENTIALS))
    script = tmp_path / "smoke.js"
    script.write_text("// k6 script")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_k6_test.py",
            str(script),
            "--stack-name",
            "my-stack",
            "--region",
            REGION,
            "--test-id",
            "smoke-test-123",
            "--max-wait",
            "0",
        ],
    )
    responses.add(responses.POST, f"{API_ENDPOINT}/scenarios", json={"testId": "smoke-test-123"}, status=200)
    responses.add(
        responses.GET, f"{API_ENDPOINT}/scenarios/smoke-test-123", json={"status": "complete"}, status=200
    )

    main()  # should not raise / sys.exit


@responses.activate
def test_main_failed_status_exits(aws, tmp_path, monkeypatch, dlt_credentials_file):
    _setup_stack_and_bucket(aws)
    dlt_credentials_file.write_text(json.dumps(VALID_CREDENTIALS))
    script = tmp_path / "smoke.js"
    script.write_text("// k6 script")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_k6_test.py",
            str(script),
            "--stack-name",
            "my-stack",
            "--region",
            REGION,
            "--test-id",
            "smoke-test-123",
            "--max-wait",
            "0",
        ],
    )
    responses.add(responses.POST, f"{API_ENDPOINT}/scenarios", json={"testId": "smoke-test-123"}, status=200)
    responses.add(responses.GET, f"{API_ENDPOINT}/scenarios/smoke-test-123", json={"status": "failed"}, status=200)

    with pytest.raises(SystemExit):
        main()
