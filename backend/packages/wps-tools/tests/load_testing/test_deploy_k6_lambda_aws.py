"""
Integration-style tests for deploy_k6_lambda's boto3-calling functions, using moto to mock
AWS. moto does not actually execute Lambda function code (no Docker in this environment), so
invoke_once/run_fan_out are tested against a MagicMock lambda client instead of moto -- these
verify our own request/response handling, not that a real invocation would succeed end to end.
"""

import argparse
import json
from unittest.mock import MagicMock

import boto3
import pytest
from botocore.exceptions import EndpointConnectionError
from moto import mock_aws
from wps_tools.load_testing.deploy_k6_lambda import (
    BASIC_EXECUTION_POLICY_ARN,
    deploy_function,
    deploy_region,
    ensure_execution_role,
    ensure_layer_bucket,
    invoke_once,
    publish_k6_layer,
    run_deploy,
    run_fan_out,
    run_run,
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


def _ensure_bucket(aws: boto3.Session, bucket_name: str = "test-bucket"):
    s3_client = aws.client("s3")
    ensure_layer_bucket(s3_client, bucket_name, REGION)
    return s3_client


def test_ensure_layer_bucket_creates_when_missing(aws):
    s3_client = aws.client("s3")

    ensure_layer_bucket(s3_client, "my-new-bucket", REGION)

    # head_bucket doesn't raise if the bucket exists
    s3_client.head_bucket(Bucket="my-new-bucket")


def test_ensure_layer_bucket_reuses_existing(aws):
    s3_client = aws.client("s3")
    ensure_layer_bucket(s3_client, "already-there", REGION)

    ensure_layer_bucket(s3_client, "already-there", REGION)  # should not raise BucketAlreadyOwnedByYou

    s3_client.head_bucket(Bucket="already-there")


def test_ensure_layer_bucket_rejects_invalid_region(aws):
    s3_client = aws.client("s3")

    with pytest.raises(ValueError, match="Not a valid S3 bucket region"):
        ensure_layer_bucket(s3_client, "my-bucket", "not-a-real-region")


def test_publish_k6_layer(aws):
    lambda_client = aws.client("lambda")
    s3_client = _ensure_bucket(aws)

    layer_arn = publish_k6_layer(lambda_client, s3_client, "test-bucket", "my-layer", b"fake zip contents")

    assert "my-layer" in layer_arn
    versions = lambda_client.list_layer_versions(LayerName="my-layer")["LayerVersions"]
    assert len(versions) == 1


def test_deploy_region_prunes_old_layer_versions_after_function_updated(aws):
    """Every deploy publishes a new immutable layer version -- without cleanup, repeated
    deploys accumulate versions without bound. Only the version just published should
    remain afterward."""
    lambda_client = aws.client("lambda")
    s3_client = _ensure_bucket(aws)
    role_arn = _create_role(aws.client("iam"), "test-role")
    kwargs = dict(
        layer_bucket="test-bucket",
        layer_name="my-layer",
        function_name="my-function",
        role_arn=role_arn,
        memory_mb=256,
        timeout_seconds=60,
        script_name="my_test.js",
    )

    deploy_region(lambda_client, s3_client, layer_zip=b"first zip contents", function_zip=_minimal_function_zip(), **kwargs)
    deploy_region(lambda_client, s3_client, layer_zip=b"second zip contents", function_zip=_minimal_function_zip(), **kwargs)

    versions = lambda_client.list_layer_versions(LayerName="my-layer")["LayerVersions"]
    assert [v["Version"] for v in versions] == [2]


def test_deploy_region_keeps_old_layer_version_if_function_deploy_fails(aws, mocker):
    """Pruning must happen only after deploy_function succeeds -- if it fails partway
    through (e.g. a transient API error), the previously-deployed function is still
    configured to use the old layer version, so that version must not be deleted."""
    lambda_client = aws.client("lambda")
    s3_client = _ensure_bucket(aws)
    role_arn = _create_role(aws.client("iam"), "test-role")
    kwargs = dict(
        layer_bucket="test-bucket",
        layer_name="my-layer",
        function_name="my-function",
        role_arn=role_arn,
        memory_mb=256,
        timeout_seconds=60,
        script_name="my_test.js",
    )

    deploy_region(lambda_client, s3_client, layer_zip=b"first zip contents", function_zip=_minimal_function_zip(), **kwargs)

    mocker.patch(
        "wps_tools.load_testing.deploy_k6_lambda.deploy_function", side_effect=RuntimeError("boom")
    )
    with pytest.raises(RuntimeError):
        deploy_region(lambda_client, s3_client, layer_zip=b"second zip contents", function_zip=_minimal_function_zip(), **kwargs)

    versions = lambda_client.list_layer_versions(LayerName="my-layer")["LayerVersions"]
    assert {v["Version"] for v in versions} == {1, 2}


def _minimal_function_zip() -> bytes:
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr("handler.py", "def handler(event, context):\n    return {}\n")
    return buffer.getvalue()


def test_deploy_function_creates_new(aws):
    lambda_client = aws.client("lambda")
    s3_client = _ensure_bucket(aws)
    role_arn = _create_role(aws.client("iam"), "test-role")
    layer_arn = publish_k6_layer(lambda_client, s3_client, "test-bucket", "test-layer", b"fake layer zip")

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
    s3_client = _ensure_bucket(aws)
    role_arn = _create_role(aws.client("iam"), "test-role")
    layer_arn = publish_k6_layer(lambda_client, s3_client, "test-bucket", "test-layer", b"fake layer zip")
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


def test_run_run_continues_after_one_region_fails(mocker, capsys):
    """One region failing (e.g. never deployed there) must not skip reporting results
    already collected from the other regions -- mirrors run_deploy's per-region
    collect-and-continue handling. The old code called sys.exit(1) from inside the
    results-collection loop, so the summary for regions that DID succeed was never
    aggregated or printed at all whenever any region failed."""
    good_client = MagicMock()
    good_client.get_function.return_value = {
        "Configuration": {"Environment": {"Variables": {"SCRIPT_NAME": "my_test.js"}}}
    }
    good_client.invoke.return_value = {
        "Payload": MagicMock(read=lambda: json.dumps({"exit_code": 0}).encode())
    }
    bad_client = MagicMock()
    bad_client.get_function.side_effect = RuntimeError("function not found in this region")
    clients_by_region = {"ca-central-1": good_client, "ca-west-1": bad_client}

    def fake_session(*, profile_name=None, region_name=None):
        session = MagicMock()
        session.client.return_value = clients_by_region[region_name]
        return session

    mocker.patch(
        "wps_tools.load_testing.deploy_k6_lambda.boto3.Session",
        side_effect=fake_session,
    )

    args = argparse.Namespace(
        region=None,
        regions="ca-central-1,ca-west-1",
        aws_profile=None,
        function_name="k6-lambda-load-gen",
        concurrency=1,
        target_rps=None,
    )

    with pytest.raises(SystemExit):
        run_run(args)

    printed = json.loads(capsys.readouterr().out)
    assert printed["invocations"] == 1
    assert printed["succeeded_invocations"] == 1


def test_run_deploy_continues_after_one_region_fails(mocker, tmp_path, caplog):
    """One region's deploy failing (e.g. a quota/permissions issue specific to that region)
    must not abort the others -- mirrors run_run's collect-and-continue handling. The old
    code called sys.exit(1) from inside the results-collection loop, so a region that DID
    deploy successfully was never logged whenever any region failed."""
    script = tmp_path / "script.js"
    script.write_text("export default function () {}")

    mocker.patch("wps_tools.load_testing.deploy_k6_lambda.download_k6_binary", return_value=b"k6")
    mocker.patch(
        "wps_tools.load_testing.deploy_k6_lambda.ensure_execution_role",
        return_value="arn:aws:iam::123456789012:role/test-role",
    )
    # ensure_layer_bucket does real work against whatever client session.client("s3") returns
    # below (a plain identity-marker string here, not a usable boto client) -- not what this
    # test is exercising, so it's mocked out rather than given a full fake S3 client.
    mocker.patch("wps_tools.load_testing.deploy_k6_lambda.ensure_layer_bucket")

    def fake_session(*, profile_name=None, region_name=None):
        session = MagicMock()

        def fake_client(service_name, **kwargs):
            if service_name == "sts":
                sts_client = MagicMock()
                sts_client.get_caller_identity.return_value = {"Account": "123456789012"}
                return sts_client
            return f"client-{region_name}"

        session.client.side_effect = fake_client
        return session

    mocker.patch(
        "wps_tools.load_testing.deploy_k6_lambda.boto3.Session", side_effect=fake_session
    )

    calls = []

    def fake_deploy_region(lambda_client, s3_client, **kwargs):
        calls.append(lambda_client)
        if lambda_client == "client-ca-west-1":
            raise RuntimeError("boom")
        return "arn:aws:lambda:ca-central-1:123456789012:function:k6-lambda-load-gen"

    mocker.patch(
        "wps_tools.load_testing.deploy_k6_lambda.deploy_region", side_effect=fake_deploy_region
    )

    args = argparse.Namespace(
        script=str(script),
        region=None,
        regions="ca-central-1,ca-west-1",
        aws_profile=None,
        function_name="k6-lambda-load-gen",
        layer_name="k6-runtime",
        role_name="k6-lambda-load-gen-role",
        memory_mb=512,
        timeout_seconds=150,
    )

    with caplog.at_level("INFO"), pytest.raises(SystemExit):
        run_deploy(args)

    assert set(calls) == {"client-ca-central-1", "client-ca-west-1"}
    assert "Deployed" in caplog.text
    assert "ca-central-1" in caplog.text
    assert "ca-west-1" in caplog.text
