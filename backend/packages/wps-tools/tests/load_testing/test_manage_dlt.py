import argparse
from pathlib import Path

import pytest
from wps_tools.load_testing.manage_dlt import (
    SafeArg,
    SafePath,
    build_aws_exports,
    build_delete_batch,
    build_parameters,
    build_template_bucket_name,
    build_template_url,
    filter_bucket_names,
)


def test_build_parameters():
    parameters = build_parameters("Jane Doe", "jane@example.com")

    assert parameters == [
        {"ParameterKey": "AdminName", "ParameterValue": "Jane Doe"},
        {"ParameterKey": "AdminEmail", "ParameterValue": "jane@example.com"},
    ]


def test_build_parameters_with_existing_vpc():
    parameters = build_parameters("Jane Doe", "jane@example.com", "vpc-123", "subnet-a", "subnet-b")

    assert parameters == [
        {"ParameterKey": "AdminName", "ParameterValue": "Jane Doe"},
        {"ParameterKey": "AdminEmail", "ParameterValue": "jane@example.com"},
        {"ParameterKey": "ExistingVPCId", "ParameterValue": "vpc-123"},
        {"ParameterKey": "ExistingSubnetA", "ParameterValue": "subnet-a"},
        {"ParameterKey": "ExistingSubnetB", "ParameterValue": "subnet-b"},
    ]


@pytest.mark.parametrize(
    "existing_vpc_id,existing_subnet_a,existing_subnet_b",
    [
        ("vpc-123", None, None),
        (None, "subnet-a", None),
        (None, None, "subnet-b"),
        ("vpc-123", "subnet-a", None),
    ],
)
def test_build_parameters_partial_existing_vpc_raises(
    existing_vpc_id, existing_subnet_a, existing_subnet_b
):
    with pytest.raises(ValueError):
        build_parameters(
            "Jane Doe", "jane@example.com", existing_vpc_id, existing_subnet_a, existing_subnet_b
        )


STACK_OUTPUTS = {
    "DLTApiEndpointD98B09AC": "https://example.execute-api.ca-central-1.amazonaws.com/prod",
    "CognitoUserPoolID": "ca-central-1_abc123",
    "CognitoAppClientID": "clientid123",
    "CognitoIdentityPoolID": "ca-central-1:identitypool123",
    "ScenariosBucket": "my-scenarios-bucket",
    "SolutionUUID": "abcd1234",
}


def test_build_aws_exports():
    aws_exports = build_aws_exports(STACK_OUTPUTS, "ca-central-1")

    assert aws_exports == {
        "ApiEndpoint": "https://example.execute-api.ca-central-1.amazonaws.com/prod",
        "UserPoolId": "ca-central-1_abc123",
        "PoolClientId": "clientid123",
        "IdentityPoolId": "ca-central-1:identitypool123",
        "UserFilesBucket": "my-scenarios-bucket",
        "UserPoolDomain": "dlt-abcd1234.auth.ca-central-1.amazoncognito.com",
    }


@pytest.mark.parametrize("missing_key", list(STACK_OUTPUTS.keys()))
def test_build_aws_exports_missing_output_raises(missing_key):
    outputs = {k: v for k, v in STACK_OUTPUTS.items() if k != missing_key}

    with pytest.raises(RuntimeError):
        build_aws_exports(outputs, "ca-central-1")


def test_build_template_url():
    url = build_template_url("my-bucket", "distributed-load-testing/my.template", "ca-central-1")

    assert (
        url
        == "https://my-bucket.s3.ca-central-1.amazonaws.com/distributed-load-testing/my.template"
    )


def test_build_template_bucket_name():
    assert (
        build_template_bucket_name("123456789012", "ca-central-1")
        == "dlt-template-staging-123456789012-ca-central-1"
    )


def test_filter_bucket_names():
    resources = [
        {"ResourceType": "AWS::S3::Bucket", "PhysicalResourceId": "my-scenarios-bucket"},
        {"ResourceType": "AWS::S3::Bucket", "PhysicalResourceId": "my-console-assets-bucket"},
        {"ResourceType": "AWS::IAM::Role", "PhysicalResourceId": "some-role"},
        {"ResourceType": "AWS::DynamoDB::Table", "PhysicalResourceId": "some-table"},
    ]

    assert filter_bucket_names(resources) == ["my-scenarios-bucket", "my-console-assets-bucket"]


def test_filter_bucket_names_skips_missing_physical_id():
    resources = [{"ResourceType": "AWS::S3::Bucket", "PhysicalResourceId": None}]

    assert filter_bucket_names(resources) == []


def test_build_delete_batch():
    versions = [{"Key": "a.txt", "VersionId": "v1"}, {"Key": "b.txt", "VersionId": "v1"}]
    delete_markers = [{"Key": "c.txt", "VersionId": "v2"}]

    assert build_delete_batch(versions, delete_markers) == [
        {"Key": "a.txt", "VersionId": "v1"},
        {"Key": "b.txt", "VersionId": "v1"},
        {"Key": "c.txt", "VersionId": "v2"},
    ]


def test_build_delete_batch_empty():
    assert build_delete_batch([], []) == []


def test_safe_arg_passes_through_normal_values():
    assert SafeArg("my-profile") == "my-profile"


def test_safe_arg_rejects_flag_like_values():
    with pytest.raises(argparse.ArgumentTypeError, match="must not start with"):
        SafeArg("--endpoint-url=http://evil.example")


def test_safe_path_resolves_relative_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert SafePath.validate("some-file.json") == tmp_path.resolve() / "some-file.json"


def test_safe_path_expands_home():
    assert SafePath.validate("~/dlt") == (Path.home() / "dlt").resolve()


def test_safe_path_rejects_symlinks(tmp_path):
    real_file = tmp_path / "real.json"
    real_file.write_text("{}")
    symlink = tmp_path / "link.json"
    symlink.symlink_to(real_file)

    with pytest.raises(argparse.ArgumentTypeError, match="symlink"):
        SafePath.validate(str(symlink))
