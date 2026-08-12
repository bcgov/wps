"""
Integration-style tests for run_k6_test's boto3/HTTP-calling functions. Kept separate from
test_run_k6_test.py, which covers pure logic only.

resolve_stack_outputs and upload_script are mocked with moto (real boto3 calls, fake AWS
backend). create_scenario/get_scenario_status hit the raw execute-api HTTPS endpoint directly
via `requests` rather than a boto3 client -- moto's API Gateway mock only covers the control
plane (creating/configuring APIs), not invoke URLs, so those are mocked with `responses` instead.
"""

import boto3
import pytest
import responses
from moto import mock_aws

from wps_tools.load_testing.run_k6_test import (
    DltCredentials,
    create_scenario,
    get_scenario_status,
    resolve_stack_outputs,
    upload_script,
)

REGION = "ca-central-1"

CREDENTIALS: DltCredentials = {
    "idToken": "id-token",
    "awsAccessKeyId": "AKIAEXAMPLE",
    "awsSecretAccessKey": "secret",
    "awsSessionToken": "session-token",
}


@pytest.fixture
def aws():
    with mock_aws():
        yield boto3.Session(region_name=REGION)


def test_resolve_stack_outputs(aws):
    cfn = aws.client("cloudformation")
    template = """{
        "Resources": {"B": {"Type": "AWS::S3::Bucket", "Properties": {}}},
        "Outputs": {
            "DLTApiEndpointD98B09AC": {"Value": "https://example.execute-api.ca-central-1.amazonaws.com/prod"},
            "ScenariosBucket": {"Value": "my-scenarios-bucket"}
        }
    }"""
    cfn.create_stack(StackName="my-stack", TemplateBody=template)
    cfn.get_waiter("stack_create_complete").wait(StackName="my-stack")

    api_endpoint, scenarios_bucket = resolve_stack_outputs("my-stack", None, REGION)

    assert api_endpoint == "https://example.execute-api.ca-central-1.amazonaws.com/prod"
    assert scenarios_bucket == "my-scenarios-bucket"


def test_upload_script(aws, tmp_path):
    s3 = aws.client("s3")
    s3.create_bucket(Bucket="scenarios-bucket", CreateBucketConfiguration={"LocationConstraint": REGION})
    script = tmp_path / "smoke_test.js"
    script.write_text("// k6 script")

    upload_script(script, "scenarios-bucket", "public/test-scenarios/k6/smoke_test.js", CREDENTIALS, REGION)

    uploaded = s3.get_object(Bucket="scenarios-bucket", Key="public/test-scenarios/k6/smoke_test.js")
    assert uploaded["Body"].read().decode() == "// k6 script"


@responses.activate
def test_create_scenario_success():
    responses.add(
        responses.POST,
        "https://example.execute-api.ca-central-1.amazonaws.com/prod/scenarios",
        json={"testId": "abc-123"},
        status=200,
    )

    create_scenario(
        "https://example.execute-api.ca-central-1.amazonaws.com/prod",
        REGION,
        CREDENTIALS,
        {"testId": "abc-123"},
    )

    assert len(responses.calls) == 1
    assert "Authorization" in responses.calls[0].request.headers


@responses.activate
def test_create_scenario_failure_raises():
    responses.add(
        responses.POST,
        "https://example.execute-api.ca-central-1.amazonaws.com/prod/scenarios",
        json={"message": "bad request"},
        status=400,
    )

    with pytest.raises(RuntimeError, match="HTTP 400"):
        create_scenario(
            "https://example.execute-api.ca-central-1.amazonaws.com/prod",
            REGION,
            CREDENTIALS,
            {"testId": "abc-123"},
        )


@responses.activate
def test_get_scenario_status():
    responses.add(
        responses.GET,
        "https://example.execute-api.ca-central-1.amazonaws.com/prod/scenarios/abc-123",
        json={"status": "running"},
        status=200,
        match=[responses.matchers.query_param_matcher({"history": "false", "latest": "false"})],
    )

    status = get_scenario_status(
        "https://example.execute-api.ca-central-1.amazonaws.com/prod", REGION, CREDENTIALS, "abc-123"
    )

    assert status == "running"


@responses.activate
def test_get_scenario_status_failure_raises():
    responses.add(
        responses.GET,
        "https://example.execute-api.ca-central-1.amazonaws.com/prod/scenarios/abc-123",
        json={"message": "not found"},
        status=404,
    )

    with pytest.raises(RuntimeError, match="HTTP 404"):
        get_scenario_status(
            "https://example.execute-api.ca-central-1.amazonaws.com/prod", REGION, CREDENTIALS, "abc-123"
        )
