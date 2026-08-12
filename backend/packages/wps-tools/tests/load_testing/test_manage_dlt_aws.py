"""
Integration-style tests for manage_dlt's boto3-calling functions, using moto to mock AWS
instead of hitting real infrastructure. Kept separate from test_manage_dlt.py, which covers
pure logic only -- these are heavier (spin up a mocked AWS backend per test) and test a
different thing: that our code calls the AWS APIs correctly, not just that our own logic is
right.

deploy_stack/teardown_stack are tested against a minimal synthetic template (one S3 bucket),
not the real bundled ~300KB production template -- moto's CloudFormation engine only
understands a subset of resource types, and the real template's Cognito/ECS/Step
Functions/Lambda/custom-resource mix is far beyond what it can simulate. The synthetic
template exists purely to exercise our own create/wait/describe and delete/wait orchestration.
"""

import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock

import boto3
import pytest
import responses
from botocore.exceptions import ClientError, WaiterError
from moto import mock_aws

from wps_tools.load_testing.manage_dlt import (
    DLT_CLI_URL,
    deploy_stack,
    empty_bucket,
    _ensure_sso_login,
    ensure_template_bucket,
    find_subnet_by_name,
    get_failure_reasons,
    _install_dlt_cli,
    resolve_existing_vpc,
    resolve_region,
    _run_dlt_command,
    set_permanent_password,
    stage_template,
    teardown_stack,
)

REGION = "ca-central-1"

MINIMAL_TEMPLATE = json.dumps(
    {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Resources": {"TestBucket": {"Type": "AWS::S3::Bucket", "Properties": {}}},
        "Outputs": {"BucketName": {"Value": {"Ref": "TestBucket"}}},
    }
)


@pytest.fixture
def aws():
    with mock_aws():
        yield boto3.Session(region_name=REGION)


def test_ensure_template_bucket_creates_when_missing(aws):
    s3 = aws.client("s3")

    ensure_template_bucket(s3, "my-new-bucket", REGION)

    s3.head_bucket(Bucket="my-new-bucket")  # raises if it doesn't exist


def test_ensure_template_bucket_reuses_existing(aws):
    s3 = aws.client("s3")
    s3.create_bucket(Bucket="already-there", CreateBucketConfiguration={"LocationConstraint": REGION})

    ensure_template_bucket(s3, "already-there", REGION)  # should not raise (e.g. BucketAlreadyOwnedByYou)

    s3.head_bucket(Bucket="already-there")


def test_stage_template(aws, tmp_path):
    s3 = aws.client("s3")
    s3.create_bucket(Bucket="staging-bucket", CreateBucketConfiguration={"LocationConstraint": REGION})
    template_file = tmp_path / "my.template"
    template_file.write_text(MINIMAL_TEMPLATE)

    url = stage_template(s3, "staging-bucket", "my-stack", template_file, REGION)

    assert url == f"https://staging-bucket.s3.{REGION}.amazonaws.com/my-stack/my.template"
    uploaded = s3.get_object(Bucket="staging-bucket", Key="my-stack/my.template")
    assert uploaded["Body"].read().decode() == MINIMAL_TEMPLATE


def test_empty_bucket_deletes_all_objects(aws):
    s3 = aws.client("s3")
    s3.create_bucket(Bucket="full-bucket", CreateBucketConfiguration={"LocationConstraint": REGION})
    s3.put_object(Bucket="full-bucket", Key="a.txt", Body=b"a")
    s3.put_object(Bucket="full-bucket", Key="b.txt", Body=b"b")

    empty_bucket(s3, "full-bucket")

    assert "Contents" not in s3.list_objects_v2(Bucket="full-bucket")


def test_empty_bucket_noop_when_already_empty(aws):
    s3 = aws.client("s3")
    s3.create_bucket(Bucket="empty-bucket", CreateBucketConfiguration={"LocationConstraint": REGION})

    empty_bucket(s3, "empty-bucket")  # should not raise


def _create_subnet(ec2, name: str, vpc_id: str, cidr: str) -> str:
    subnet = ec2.create_subnet(VpcId=vpc_id, CidrBlock=cidr)["Subnet"]
    ec2.create_tags(Resources=[subnet["SubnetId"]], Tags=[{"Key": "Name", "Value": name}])
    return subnet["SubnetId"]


def test_find_subnet_by_name(aws):
    ec2 = aws.client("ec2")
    vpc_id = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
    subnet_id = _create_subnet(ec2, "Prod-App-A", vpc_id, "10.0.1.0/24")

    found_subnet_id, found_vpc_id = find_subnet_by_name(ec2, "Prod-App-A")

    assert found_subnet_id == subnet_id
    assert found_vpc_id == vpc_id


def test_find_subnet_by_name_not_found_raises(aws):
    ec2 = aws.client("ec2")

    with pytest.raises(RuntimeError, match="No subnet found"):
        find_subnet_by_name(ec2, "Nonexistent")


def test_find_subnet_by_name_multiple_raises(aws):
    ec2 = aws.client("ec2")
    vpc_id = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
    _create_subnet(ec2, "Dupe", vpc_id, "10.0.1.0/24")
    _create_subnet(ec2, "Dupe", vpc_id, "10.0.2.0/24")

    with pytest.raises(RuntimeError, match="Multiple subnets"):
        find_subnet_by_name(ec2, "Dupe")


def test_resolve_existing_vpc(aws):
    ec2 = aws.client("ec2")
    vpc_id = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
    subnet_a_id = _create_subnet(ec2, "Prod-App-A", vpc_id, "10.0.1.0/24")
    subnet_b_id = _create_subnet(ec2, "Prod-App-B", vpc_id, "10.0.2.0/24")

    resolved_vpc_id, resolved_a, resolved_b = resolve_existing_vpc(ec2, "Prod-App-A", "Prod-App-B")

    assert resolved_vpc_id == vpc_id
    assert resolved_a == subnet_a_id
    assert resolved_b == subnet_b_id


def test_resolve_existing_vpc_mismatched_vpcs_raises(aws):
    ec2 = aws.client("ec2")
    vpc_a = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
    vpc_b = ec2.create_vpc(CidrBlock="10.1.0.0/16")["Vpc"]["VpcId"]
    _create_subnet(ec2, "Prod-App-A", vpc_a, "10.0.1.0/24")
    _create_subnet(ec2, "Prod-App-B", vpc_b, "10.1.1.0/24")

    with pytest.raises(RuntimeError, match="different VPCs"):
        resolve_existing_vpc(ec2, "Prod-App-A", "Prod-App-B")


def test_deploy_stack_creates_and_returns_stack(aws):
    cfn = aws.client("cloudformation")

    stack = deploy_stack(cfn, "test-stack", parameters=[], template_body=MINIMAL_TEMPLATE)

    assert stack["StackName"] == "test-stack"
    assert stack["StackStatus"] == "CREATE_COMPLETE"


def test_teardown_stack_deletes(aws):
    cfn = aws.client("cloudformation")
    s3 = aws.client("s3")
    cfn.create_stack(StackName="to-delete", TemplateBody=MINIMAL_TEMPLATE)
    cfn.get_waiter("stack_create_complete").wait(StackName="to-delete")

    teardown_stack(cfn, s3, "to-delete", empty_buckets=False)

    with pytest.raises(Exception, match="does not exist"):
        cfn.describe_stacks(StackName="to-delete")


def test_teardown_stack_empties_buckets_first(aws):
    cfn = aws.client("cloudformation")
    s3 = aws.client("s3")
    cfn.create_stack(StackName="to-delete-full", TemplateBody=MINIMAL_TEMPLATE)
    cfn.get_waiter("stack_create_complete").wait(StackName="to-delete-full")
    [bucket_name] = [
        o["OutputValue"]
        for o in cfn.describe_stacks(StackName="to-delete-full")["Stacks"][0]["Outputs"]
        if o["OutputKey"] == "BucketName"
    ]
    s3.put_object(Bucket=bucket_name, Key="leftover.txt", Body=b"data")

    teardown_stack(cfn, s3, "to-delete-full", empty_buckets=True)

    with pytest.raises(Exception, match="does not exist"):
        cfn.describe_stacks(StackName="to-delete-full")


def test_set_permanent_password(aws):
    cognito = aws.client("cognito-idp")
    pool_id = cognito.create_user_pool(PoolName="test-pool")["UserPool"]["Id"]
    cognito.admin_create_user(UserPoolId=pool_id, Username="conor", MessageAction="SUPPRESS")

    set_permanent_password(cognito, pool_id, "conor", "Wps-Loadtest1!")  # should not raise

    user = cognito.admin_get_user(UserPoolId=pool_id, Username="conor")
    assert user["UserStatus"] in ("CONFIRMED", "FORCE_CHANGE_PASSWORD")


def test_ensure_template_bucket_us_east_1_omits_location_constraint(aws):
    s3 = boto3.Session(region_name="us-east-1").client("s3")

    ensure_template_bucket(s3, "us-east-1-bucket", "us-east-1")

    s3.head_bucket(Bucket="us-east-1-bucket")


def test_ensure_template_bucket_invalid_region_raises(aws):
    s3 = aws.client("s3")

    with pytest.raises(ValueError, match="Not a valid S3 bucket region"):
        ensure_template_bucket(s3, "some-bucket", "mars-central-1")


def test_ensure_template_bucket_reraises_non_404_errors():
    s3 = MagicMock()
    s3.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "403", "Message": "Forbidden"}, "ResponseMetadata": {"HTTPStatusCode": 403}},
        "HeadBucket",
    )

    with pytest.raises(ClientError):
        ensure_template_bucket(s3, "some-bucket", REGION)


def test_get_failure_reasons_filters_to_failed_events():
    cfn = MagicMock()
    cfn.describe_stack_events.return_value = {
        "StackEvents": [
            {"LogicalResourceId": "Bucket", "ResourceStatus": "CREATE_FAILED", "ResourceStatusReason": "boom"},
            {"LogicalResourceId": "Role", "ResourceStatus": "CREATE_COMPLETE"},
        ]
    }

    assert get_failure_reasons(cfn, "my-stack") == ["Bucket: boom"]


def test_teardown_stack_wraps_waiter_error_with_failure_reasons():
    cfn = MagicMock()
    cfn.get_waiter.return_value.wait.side_effect = WaiterError(
        name="stack_delete_complete", reason="Waiter encountered a terminal failure state", last_response={}
    )
    cfn.describe_stack_events.return_value = {
        "StackEvents": [
            {
                "LogicalResourceId": "Bucket",
                "ResourceStatus": "DELETE_FAILED",
                "ResourceStatusReason": "bucket not empty",
            }
        ]
    }
    s3 = MagicMock()

    with pytest.raises(RuntimeError, match="bucket not empty"):
        teardown_stack(cfn, s3, "my-stack", empty_buckets=False)


def test_resolve_region_returns_session_region():
    session = MagicMock(region_name=REGION)

    assert resolve_region(session) == REGION


def test_resolve_region_exits_when_unresolvable():
    session = MagicMock(region_name=None)

    with pytest.raises(SystemExit):
        resolve_region(session)


def test_ensure_sso_login_noop_without_profile(mocker):
    subprocess_run = mocker.patch("wps_tools.load_testing.manage_dlt.subprocess.run")

    _ensure_sso_login(None)

    subprocess_run.assert_not_called()


def test_ensure_sso_login_runs_aws_sso_login(mocker):
    subprocess_run = mocker.patch("wps_tools.load_testing.manage_dlt.subprocess.run")

    _ensure_sso_login("my-profile")

    subprocess_run.assert_called_once_with(["aws", "sso", "login", "--profile", "my-profile"], check=True)


def test_ensure_sso_login_rejects_flag_like_profile_even_called_directly(mocker):
    """Defense in depth: argparse's type=cli_safe_value already rejects this on --aws-profile,
    but this function can also be called directly (bypassing argparse), so it re-checks."""
    subprocess_run = mocker.patch("wps_tools.load_testing.manage_dlt.subprocess.run")

    with pytest.raises(Exception, match="must not start with"):
        _ensure_sso_login("--endpoint-url=http://evil.example")

    subprocess_run.assert_not_called()


def test_run_dlt_command(mocker):
    subprocess_run = mocker.patch("wps_tools.load_testing.manage_dlt.subprocess.run")

    _run_dlt_command(Path("/tmp/dlt"), ["token", "status"])

    subprocess_run.assert_called_once_with(["/tmp/dlt", "token", "status"], check=True)


def test_run_dlt_command_allows_known_flags(mocker):
    subprocess_run = mocker.patch("wps_tools.load_testing.manage_dlt.subprocess.run")

    _run_dlt_command(Path("/tmp/dlt"), ["login", "--srp", "--username", "conor", "--password", "hunter2"])

    subprocess_run.assert_called_once_with(
        ["/tmp/dlt", "login", "--srp", "--username", "conor", "--password", "hunter2"], check=True
    )


def test_run_dlt_command_rejects_unexpected_flag(mocker):
    """Defense in depth: admin_name/admin_password are already validated by argparse's
    type=cli_safe_value before reaching here, but this re-checks in case a value slipping into
    a flag's position ever reaches _run_dlt_command by some other path."""
    subprocess_run = mocker.patch("wps_tools.load_testing.manage_dlt.subprocess.run")

    with pytest.raises(ValueError, match="unexpected flag-like"):
        _run_dlt_command(Path("/tmp/dlt"), ["login", "--srp", "--username", "--evil-flag"])

    subprocess_run.assert_not_called()


def test_install_dlt_cli_skips_when_already_present(tmp_path):
    dest = tmp_path / "dlt"
    dest.write_text("existing binary")

    with responses.RequestsMock():  # no routes registered -- any HTTP call would fail the test
        _install_dlt_cli(dest)

    assert dest.read_text() == "existing binary"


def test_install_dlt_cli_downloads_when_missing(tmp_path, mocker):
    dest = tmp_path / "nested" / "dlt"
    body = b"#!/usr/bin/env node\n"
    mocker.patch("wps_tools.load_testing.manage_dlt.DLT_CLI_SHA256", hashlib.sha256(body).hexdigest())

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, DLT_CLI_URL, body=body, status=200)
        _install_dlt_cli(dest)

    assert dest.read_bytes() == body
    assert dest.stat().st_mode & 0o777 == 0o755


def test_install_dlt_cli_rejects_checksum_mismatch(tmp_path):
    """Guards against a compromised/rewritten upstream file being silently installed and
    made executable -- content is verified against the pinned DLT_CLI_SHA256 before writing."""
    dest = tmp_path / "dlt"

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, DLT_CLI_URL, body=b"malicious content", status=200)
        with pytest.raises(RuntimeError, match="unexpected SHA256"):
            _install_dlt_cli(dest)

    assert not dest.exists()


def test_install_dlt_cli_rejects_symlink_dest_even_called_directly(tmp_path):
    """Defense in depth: argparse's type=resolved_path already rejects this on --dlt-cli-path,
    but this function can also be called directly (bypassing argparse), so it re-checks."""
    real_file = tmp_path / "real-dlt"
    real_file.write_text("existing binary")
    dest = tmp_path / "dlt-symlink"
    dest.symlink_to(real_file)

    with responses.RequestsMock():  # no routes registered -- any HTTP call would fail the test
        with pytest.raises(argparse.ArgumentTypeError, match="symlink"):
            _install_dlt_cli(dest)
