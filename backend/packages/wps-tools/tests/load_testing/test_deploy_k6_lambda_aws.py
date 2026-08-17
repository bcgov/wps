"""
Integration-style tests for deploy_k6_lambda's boto3-calling functions, using moto to mock
AWS. moto does not actually execute Lambda function code (no Docker in this environment), so
invoke_once/run_fan_out are tested against a MagicMock lambda client instead of moto -- these
verify our own request/response handling, not that a real invocation would succeed end to end.
"""

import json
from unittest.mock import MagicMock

import boto3
import pytest
from botocore.exceptions import EndpointConnectionError
from moto import mock_aws
from wps_tools.load_testing.k6_lambda.deploy_k6_lambda import (
    BASIC_EXECUTION_POLICY_ARN,
    deploy_function,
    ensure_execution_role,
    invoke_once,
    publish_k6_layer,
    run_fan_out,
)

REGION = "ca-central-1"

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


@pytest.fixture
def aws():
    with mock_aws():
        yield boto3.Session(region_name=REGION)


def _create_role(iam, role_name: str) -> str:
    """Creates a role directly (no policy attachment) -- for tests that just need a valid
    role ARN to pass around, not to exercise ensure_execution_role's own attach behavior."""
    return iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=LAMBDA_TRUST_POLICY)[
        "Role"
    ]["Arn"]


def test_ensure_execution_role_creates_when_missing(aws, mocker):
    # AWSLambdaBasicExecutionRole is a real AWS-managed policy, not one moto's simulated IAM
    # has pre-seeded -- attach_role_policy is mocked so create_role/get_role still get real
    # moto verification, and the attach call itself is checked via its arguments instead of
    # list_attached_role_policies (which would reflect moto's real, unmocked state).
    iam = aws.client("iam")
    attach_spy = mocker.patch.object(iam, "attach_role_policy")

    role_arn = ensure_execution_role(iam, "my-new-role")

    role = iam.get_role(RoleName="my-new-role")
    assert role["Role"]["Arn"] == role_arn
    attach_spy.assert_called_once_with(RoleName="my-new-role", PolicyArn=BASIC_EXECUTION_POLICY_ARN)


def test_ensure_execution_role_reuses_existing(aws):
    iam = aws.client("iam")
    _create_role(iam, "already-there")

    role_arn = ensure_execution_role(iam, "already-there")

    assert role_arn == iam.get_role(RoleName="already-there")["Role"]["Arn"]
    # should not have attached the basic execution policy a second time / raised
    attached = iam.list_attached_role_policies(RoleName="already-there")["AttachedPolicies"]
    assert attached == []


def test_publish_k6_layer(aws):
    lambda_client = aws.client("lambda")

    layer_arn = publish_k6_layer(lambda_client, "my-layer", b"fake zip contents")

    assert "my-layer" in layer_arn
    versions = lambda_client.list_layer_versions(LayerName="my-layer")["LayerVersions"]
    assert len(versions) == 1


def _minimal_function_zip() -> bytes:
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr("handler.py", "def handler(event, context):\n    return {}\n")
    return buffer.getvalue()


def test_deploy_function_creates_new(aws):
    lambda_client = aws.client("lambda")
    role_arn = _create_role(aws.client("iam"), "test-role")
    layer_arn = publish_k6_layer(lambda_client, "test-layer", b"fake layer zip")

    function_arn = deploy_function(
        lambda_client,
        function_name="new-function",
        zip_bytes=_minimal_function_zip(),
        role_arn=role_arn,
        layer_arn=layer_arn,
        memory_mb=256,
        timeout_seconds=60,
        script_name="my_test.js",
    )

    config = lambda_client.get_function(FunctionName="new-function")["Configuration"]
    assert config["FunctionArn"] == function_arn
    assert config["Environment"]["Variables"]["SCRIPT_NAME"] == "my_test.js"
    assert config["MemorySize"] == 256
    assert config["Timeout"] == 60
    assert "VpcConfig" not in config or not config["VpcConfig"].get("VpcId")


def test_deploy_function_without_layer(aws):
    """verify_ip_diversity.py's probe function needs no k6 layer at all -- layer_arn=None
    must produce a function with no Layers, not a TypeError or an empty-string layer ARN."""
    lambda_client = aws.client("lambda")
    role_arn = _create_role(aws.client("iam"), "test-role")

    deploy_function(
        lambda_client,
        function_name="no-layer-function",
        zip_bytes=_minimal_function_zip(),
        role_arn=role_arn,
        layer_arn=None,
        memory_mb=128,
        timeout_seconds=10,
        script_name="",
    )

    config = lambda_client.get_function(FunctionName="no-layer-function")["Configuration"]
    assert config.get("Layers", []) == []


def test_deploy_function_updates_existing(aws):
    lambda_client = aws.client("lambda")
    role_arn = _create_role(aws.client("iam"), "test-role")
    layer_arn = publish_k6_layer(lambda_client, "test-layer", b"fake layer zip")
    deploy_function(
        lambda_client,
        function_name="existing-function",
        zip_bytes=_minimal_function_zip(),
        role_arn=role_arn,
        layer_arn=layer_arn,
        memory_mb=256,
        timeout_seconds=60,
        script_name="old_script.js",
    )

    deploy_function(
        lambda_client,
        function_name="existing-function",
        zip_bytes=_minimal_function_zip(),
        role_arn=role_arn,
        layer_arn=layer_arn,
        memory_mb=512,
        timeout_seconds=120,
        script_name="new_script.js",
    )

    config = lambda_client.get_function(FunctionName="existing-function")["Configuration"]
    assert config["Environment"]["Variables"]["SCRIPT_NAME"] == "new_script.js"
    assert config["MemorySize"] == 512
    assert config["Timeout"] == 120


def test_invoke_once_parses_payload():
    lambda_client = MagicMock()
    lambda_client.invoke.return_value = {
        "Payload": MagicMock(read=lambda: json.dumps({"exit_code": 0}).encode())
    }

    result = invoke_once(lambda_client, "my-function", {"target_rps": 1.5})

    assert result == {"exit_code": 0}
    call_kwargs = lambda_client.invoke.call_args.kwargs
    assert call_kwargs["FunctionName"] == "my-function"
    assert call_kwargs["InvocationType"] == "RequestResponse"
    assert json.loads(call_kwargs["Payload"]) == {"target_rps": 1.5}


def test_invoke_once_sends_empty_payload():
    lambda_client = MagicMock()
    lambda_client.invoke.return_value = {
        "Payload": MagicMock(read=lambda: json.dumps({"exit_code": 0}).encode())
    }

    invoke_once(lambda_client, "my-function", {})

    call_kwargs = lambda_client.invoke.call_args.kwargs
    assert json.loads(call_kwargs["Payload"]) == {}


def test_run_fan_out_fires_requested_concurrency():
    lambda_client = MagicMock()
    lambda_client.invoke.return_value = {
        "Payload": MagicMock(read=lambda: json.dumps({"exit_code": 0}).encode())
    }

    results = run_fan_out(lambda_client, "my-function", concurrency=5, payload={})

    assert len(results) == 5
    assert lambda_client.invoke.call_count == 5


def test_run_fan_out_survives_individual_invocation_failures():
    """Confirmed live: firing enough concurrent threads through one client can produce a
    transient connection/DNS failure on some invocations. One failing invoke() must not
    crash the whole batch and discard every other invocation's result."""
    lambda_client = MagicMock()
    call_count = 0

    def flaky_invoke(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 3:
            raise EndpointConnectionError(endpoint_url="https://lambda.example.com/")
        return {"Payload": MagicMock(read=lambda: json.dumps({"exit_code": 0}).encode())}

    lambda_client.invoke.side_effect = flaky_invoke

    results = run_fan_out(lambda_client, "my-function", concurrency=5, payload={})

    assert len(results) == 5
    succeeded = [r for r in results if r.get("exit_code") == 0]
    failed = [r for r in results if "error" in r]
    assert len(succeeded) == 4
    assert len(failed) == 1
