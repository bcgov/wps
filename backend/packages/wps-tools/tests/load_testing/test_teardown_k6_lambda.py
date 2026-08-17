"""
Integration-style tests for teardown_k6_lambda's boto3-calling functions, using moto to mock
AWS -- same approach as test_deploy_k6_lambda_aws.py.
"""

import argparse
from unittest.mock import MagicMock

import boto3
import pytest
from moto import mock_aws
from wps_tools.load_testing.deploy_k6_lambda import (
    ensure_layer_bucket,
    publish_k6_layer,
)
from wps_tools.load_testing.teardown_k6_lambda import (
    delete_execution_role,
    delete_function_if_exists,
    delete_layer_versions,
    empty_and_delete_bucket,
    run_teardown,
)

REGION = "ca-central-1"

LAMBDA_TRUST_POLICY = """{
    "Version": "2012-10-17",
    "Statement": [
        {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}
    ]
}"""


@pytest.fixture
def aws():
    with mock_aws():
        yield boto3.Session(region_name=REGION)


def _minimal_function_zip() -> bytes:
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr("handler.py", "def handler(event, context):\n    return {}\n")
    return buffer.getvalue()


def test_delete_function_if_exists_deletes(aws):
    lambda_client = aws.client("lambda")
    role_arn = aws.client("iam").create_role(
        RoleName="test-role", AssumeRolePolicyDocument=LAMBDA_TRUST_POLICY
    )["Role"]["Arn"]
    lambda_client.create_function(
        FunctionName="my-function",
        Runtime="python3.13",
        Role=role_arn,
        Handler="handler.handler",
        Code={"ZipFile": _minimal_function_zip()},
    )

    delete_function_if_exists(lambda_client, "my-function")

    with pytest.raises(lambda_client.exceptions.ResourceNotFoundException):
        lambda_client.get_function(FunctionName="my-function")


def test_delete_function_if_exists_missing_is_noop(aws):
    lambda_client = aws.client("lambda")

    delete_function_if_exists(lambda_client, "does-not-exist")  # should not raise


def test_delete_layer_versions_removes_every_version(aws):
    lambda_client = aws.client("lambda")
    s3_client = aws.client("s3")
    ensure_layer_bucket(s3_client, "my-bucket", REGION)
    publish_k6_layer(lambda_client, s3_client, "my-bucket", "my-layer", b"first zip")
    publish_k6_layer(lambda_client, s3_client, "my-bucket", "my-layer", b"second zip")

    delete_layer_versions(lambda_client, "my-layer")

    versions = lambda_client.list_layer_versions(LayerName="my-layer")["LayerVersions"]
    assert versions == []


def test_empty_and_delete_bucket_removes_objects_and_bucket(aws):
    s3_client = aws.client("s3")
    ensure_layer_bucket(s3_client, "my-bucket", REGION)
    s3_client.put_object(Bucket="my-bucket", Key="my-layer.zip", Body=b"contents")

    empty_and_delete_bucket(s3_client, "my-bucket")

    from botocore.exceptions import ClientError

    with pytest.raises(ClientError):
        s3_client.head_bucket(Bucket="my-bucket")


def test_empty_and_delete_bucket_missing_is_noop(aws):
    s3_client = aws.client("s3")

    empty_and_delete_bucket(s3_client, "does-not-exist")  # should not raise


def test_delete_execution_role_detaches_and_deletes(aws):
    # Created directly rather than via ensure_execution_role: moto doesn't have
    # AWSLambdaBasicExecutionRole pre-seeded as an attachable managed policy (same
    # limitation test_deploy_k6_lambda_aws.py works around), and delete_execution_role's
    # detach step is expected to tolerate a role that was never attached the policy anyway.
    iam_client = aws.client("iam")
    iam_client.create_role(RoleName="my-role", AssumeRolePolicyDocument=LAMBDA_TRUST_POLICY)

    delete_execution_role(iam_client, "my-role")

    with pytest.raises(iam_client.exceptions.NoSuchEntityException):
        iam_client.get_role(RoleName="my-role")


def test_delete_execution_role_missing_is_noop(aws):
    iam_client = aws.client("iam")

    delete_execution_role(iam_client, "does-not-exist")  # should not raise


def test_run_teardown_aborts_without_confirmation(mocker):
    """No --yes and an input() answer other than 'y' must not touch AWS at all."""
    mocker.patch("builtins.input", return_value="n")
    session_spy = mocker.patch("wps_tools.load_testing.teardown_k6_lambda.boto3.Session")

    args = argparse.Namespace(
        region="ca-central-1",
        regions=None,
        aws_profile=None,
        function_name="k6-lambda-load-gen",
        probe_function_name="k6-lambda-ip-probe",
        layer_name="k6-runtime",
        role_name="k6-lambda-load-gen-role",
        yes=False,
    )

    run_teardown(args)

    session_spy.assert_not_called()


def test_run_teardown_skips_prompt_with_yes_flag(mocker):
    input_spy = mocker.patch("builtins.input")
    mocker.patch(
        "wps_tools.load_testing.teardown_k6_lambda.boto3.Session",
        return_value=MagicMock(),
    )
    mocker.patch("wps_tools.load_testing.teardown_k6_lambda.delete_function_if_exists")
    mocker.patch("wps_tools.load_testing.teardown_k6_lambda.delete_layer_versions")
    mocker.patch("wps_tools.load_testing.teardown_k6_lambda.empty_and_delete_bucket")
    mocker.patch("wps_tools.load_testing.teardown_k6_lambda.delete_execution_role")

    args = argparse.Namespace(
        region="ca-central-1",
        regions=None,
        aws_profile=None,
        function_name="k6-lambda-load-gen",
        probe_function_name="k6-lambda-ip-probe",
        layer_name="k6-runtime",
        role_name="k6-lambda-load-gen-role",
        yes=True,
    )

    run_teardown(args)

    input_spy.assert_not_called()


def test_run_teardown_continues_after_one_region_fails(mocker):
    """Mirrors run_deploy/run_run's collect-and-continue handling -- one region's teardown
    failing must not stop the IAM role (shared, global) from still being cleaned up, and
    must still be reported via sys.exit(1)."""
    mocker.patch("builtins.input", return_value="y")

    good_client = MagicMock()
    bad_client = MagicMock()
    bad_client.delete_function.side_effect = RuntimeError("boom")
    clients_by_region = {"ca-central-1": good_client, "ca-west-1": bad_client}

    def fake_session(*, profile_name=None, region_name=None):
        session = MagicMock()

        def fake_client(service_name, **kwargs):
            if service_name == "sts":
                sts_client = MagicMock()
                sts_client.get_caller_identity.return_value = {"Account": "123456789012"}
                return sts_client
            if region_name in clients_by_region:
                return clients_by_region[region_name]
            return MagicMock()  # regions[0]'s iam client, before the per-region fan-out

        session.client.side_effect = fake_client
        return session

    mocker.patch(
        "wps_tools.load_testing.teardown_k6_lambda.boto3.Session", side_effect=fake_session
    )
    delete_role_spy = mocker.patch(
        "wps_tools.load_testing.teardown_k6_lambda.delete_execution_role"
    )

    args = argparse.Namespace(
        region=None,
        regions="ca-central-1,ca-west-1",
        aws_profile=None,
        function_name="k6-lambda-load-gen",
        probe_function_name="k6-lambda-ip-probe",
        layer_name="k6-runtime",
        role_name="k6-lambda-load-gen-role",
        yes=False,
    )

    with pytest.raises(SystemExit):
        run_teardown(args)

    delete_role_spy.assert_called_once()
