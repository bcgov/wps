"""
Tests for manage_dlt's top-level orchestration: run_deploy/run_teardown (and, via
create_parser().parse_args, the argparse wiring itself). These call the already
directly-tested helpers (deploy_stack, build_aws_exports, install_dlt_cli, ...), so the
goal here isn't to re-verify those -- it's to cover run_deploy/run_teardown's own branching
(template-size routing, VPC auto-resolution, --skip-* flags, error -> sys.exit paths) which
unit tests on the helpers alone can't reach.

AWS calls go through moto (real boto3.Session()/clients, fake backend). subprocess ("aws sso
login", the dlt CLI) and the dlt-cli.mjs download are the only things mocked directly, since
those are genuinely external processes/hosts moto has no opinion on.
"""

import json
import subprocess

import boto3
import pytest
import responses
from moto import mock_aws

from wps_tools.load_testing.manage_dlt import DLT_CLI_URL, create_parser, run_deploy, run_teardown

REGION = "ca-central-1"
ADMIN_PASSWORD = "Wps-Loadtest1!"


@pytest.fixture
def aws():
    with mock_aws():
        yield boto3.Session(region_name=REGION)


def parse_deploy_args(*extra: str) -> object:
    return create_parser().parse_args(
        [
            "deploy",
            "--admin-name",
            "Jane Doe",
            "--admin-email",
            "jane@example.com",
            "--admin-password",
            ADMIN_PASSWORD,
            "--region",
            REGION,
            *extra,
        ]
    )


def small_template(pool_id: str) -> str:
    return json.dumps(
        {
            "Resources": {"Topic": {"Type": "AWS::SNS::Topic", "Properties": {}}},
            "Outputs": {
                "DLTApiEndpointD98B09AC": {"Value": "https://example.execute-api.ca-central-1.amazonaws.com/prod"},
                "CognitoUserPoolID": {"Value": pool_id},
                "CognitoAppClientID": {"Value": "clientid123"},
                "CognitoIdentityPoolID": {"Value": "ca-central-1:identitypool123"},
                "ScenariosBucket": {"Value": "my-scenarios-bucket"},
                "SolutionUUID": {"Value": "abcd1234"},
            },
        }
    )


def test_create_parser_deploy_defaults():
    args = parse_deploy_args()

    assert args.command == "deploy"
    assert args.stack_name == "distributed-load-testing"
    assert args.subnet_a_name == "Prod-App-A"
    assert args.subnet_b_name == "Prod-App-B"
    assert args.admin_password == ADMIN_PASSWORD
    assert args.skip_dlt_setup is False


def test_create_parser_deploy_requires_admin_password():
    with pytest.raises(SystemExit):
        create_parser().parse_args(["deploy", "--admin-name", "Jane", "--admin-email", "jane@example.com"])


def test_create_parser_teardown_defaults():
    args = create_parser().parse_args(["teardown"])

    assert args.command == "teardown"
    assert args.empty_buckets is False
    assert args.yes is False


def test_run_deploy_missing_template_exits(tmp_path):
    args = parse_deploy_args("--template", str(tmp_path / "missing.template"))

    with pytest.raises(SystemExit):
        run_deploy(args)


def test_run_deploy_small_template_skip_dlt_setup(aws, tmp_path):
    template_file = tmp_path / "small.template"
    template_file.write_text(small_template("ca-central-1_fakepool"))
    aws_exports_file = tmp_path / "aws-exports.json"
    args = parse_deploy_args(
        "--template",
        str(template_file),
        "--skip-sso-login",
        "--existing-vpc-id",
        "vpc-123",
        "--existing-subnet-a",
        "subnet-a",
        "--existing-subnet-b",
        "subnet-b",
        "--aws-exports-file",
        str(aws_exports_file),
        "--skip-dlt-setup",
    )

    run_deploy(args)

    written = json.loads(aws_exports_file.read_text())
    assert written["UserPoolId"] == "ca-central-1_fakepool"
    assert written["UserFilesBucket"] == "my-scenarios-bucket"


def test_run_deploy_skip_aws_exports_does_not_write_file(aws, tmp_path):
    template_file = tmp_path / "small.template"
    template_file.write_text(small_template("ca-central-1_fakepool"))
    aws_exports_file = tmp_path / "aws-exports.json"
    args = parse_deploy_args(
        "--template",
        str(template_file),
        "--skip-sso-login",
        "--existing-vpc-id",
        "vpc-123",
        "--existing-subnet-a",
        "subnet-a",
        "--existing-subnet-b",
        "subnet-b",
        "--aws-exports-file",
        str(aws_exports_file),
        "--skip-aws-exports",
    )

    run_deploy(args)

    assert not aws_exports_file.exists()


def test_run_deploy_auto_resolves_vpc_by_subnet_name(aws, tmp_path):
    ec2 = aws.client("ec2")
    vpc_id = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
    for name, cidr in [("Prod-App-A", "10.0.1.0/24"), ("Prod-App-B", "10.0.2.0/24")]:
        subnet = ec2.create_subnet(VpcId=vpc_id, CidrBlock=cidr)["Subnet"]
        ec2.create_tags(Resources=[subnet["SubnetId"]], Tags=[{"Key": "Name", "Value": name}])
    template_file = tmp_path / "small.template"
    template_file.write_text(small_template("ca-central-1_fakepool"))
    args = parse_deploy_args(
        "--template",
        str(template_file),
        "--skip-sso-login",
        "--aws-exports-file",
        str(tmp_path / "aws-exports.json"),
        "--skip-dlt-setup",
    )

    run_deploy(args)  # should not raise -- VPC/subnets resolved automatically


def test_run_deploy_vpc_resolution_failure_exits(aws, tmp_path):
    template_file = tmp_path / "small.template"
    template_file.write_text(small_template("ca-central-1_fakepool"))
    args = parse_deploy_args(
        "--template",
        str(template_file),
        "--skip-sso-login",
        "--aws-exports-file",
        str(tmp_path / "aws-exports.json"),
        "--skip-dlt-setup",
    )

    with pytest.raises(SystemExit):
        run_deploy(args)  # no Prod-App-A/B subnets exist and --create-vpc wasn't passed


def test_run_deploy_large_template_without_bucket_option_exits(aws, tmp_path):
    template_file = tmp_path / "large.template"
    padded = json.loads(small_template("ca-central-1_fakepool"))
    padded["Description"] = "x" * 60_000
    template_file.write_text(json.dumps(padded))
    args = parse_deploy_args(
        "--template",
        str(template_file),
        "--skip-sso-login",
        "--existing-vpc-id",
        "vpc-123",
        "--existing-subnet-a",
        "subnet-a",
        "--existing-subnet-b",
        "subnet-b",
    )

    with pytest.raises(SystemExit):
        run_deploy(args)


def test_run_deploy_large_template_stages_via_s3(aws, tmp_path):
    template_file = tmp_path / "large.template"
    padded = json.loads(small_template("ca-central-1_fakepool"))
    padded["Description"] = "x" * 60_000
    template_file.write_text(json.dumps(padded))
    aws_exports_file = tmp_path / "aws-exports.json"
    args = parse_deploy_args(
        "--template",
        str(template_file),
        "--skip-sso-login",
        "--existing-vpc-id",
        "vpc-123",
        "--existing-subnet-a",
        "subnet-a",
        "--existing-subnet-b",
        "subnet-b",
        "--create-template-bucket",
        "--aws-exports-file",
        str(aws_exports_file),
        "--skip-dlt-setup",
    )

    run_deploy(args)

    assert aws_exports_file.exists()


def test_run_deploy_full_dlt_setup_success(aws, tmp_path, mocker):
    cognito = aws.client("cognito-idp")
    pool_id = cognito.create_user_pool(PoolName="test-pool")["UserPool"]["Id"]
    cognito.admin_create_user(UserPoolId=pool_id, Username="Jane Doe", MessageAction="SUPPRESS")
    template_file = tmp_path / "small.template"
    template_file.write_text(small_template(pool_id))
    aws_exports_file = tmp_path / "aws-exports.json"
    dlt_cli_path = tmp_path / "dlt"
    subprocess_run = mocker.patch("wps_tools.load_testing.manage_dlt.subprocess.run")
    args = parse_deploy_args(
        "--template",
        str(template_file),
        "--skip-sso-login",
        "--existing-vpc-id",
        "vpc-123",
        "--existing-subnet-a",
        "subnet-a",
        "--existing-subnet-b",
        "subnet-b",
        "--aws-exports-file",
        str(aws_exports_file),
        "--dlt-cli-path",
        str(dlt_cli_path),
    )

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, DLT_CLI_URL, body=b"#!/usr/bin/env node\n", status=200)
        run_deploy(args)

    assert dlt_cli_path.is_file()
    dlt_commands = [call.args[0][1:] for call in subprocess_run.call_args_list]
    assert ["configure", "--from-file", str(aws_exports_file)] in dlt_commands
    assert ["login", "--srp", "--username", "Jane Doe", "--password", ADMIN_PASSWORD] in dlt_commands
    user = cognito.admin_get_user(UserPoolId=pool_id, Username="Jane Doe")
    assert user["UserStatus"] in ("CONFIRMED", "FORCE_CHANGE_PASSWORD")


def test_run_deploy_dlt_setup_failure_exits(aws, tmp_path, mocker):
    cognito = aws.client("cognito-idp")
    pool_id = cognito.create_user_pool(PoolName="test-pool")["UserPool"]["Id"]
    template_file = tmp_path / "small.template"
    template_file.write_text(small_template(pool_id))
    dlt_cli_path = tmp_path / "dlt"
    mocker.patch(
        "wps_tools.load_testing.manage_dlt.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "dlt"),
    )
    args = parse_deploy_args(
        "--template",
        str(template_file),
        "--skip-sso-login",
        "--existing-vpc-id",
        "vpc-123",
        "--existing-subnet-a",
        "subnet-a",
        "--existing-subnet-b",
        "subnet-b",
        "--aws-exports-file",
        str(tmp_path / "aws-exports.json"),
        "--dlt-cli-path",
        str(dlt_cli_path),
    )

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, DLT_CLI_URL, body=b"#!/usr/bin/env node\n", status=200)
        with pytest.raises(SystemExit):
            run_deploy(args)


def test_run_deploy_sso_login_failure_exits(tmp_path, mocker):
    template_file = tmp_path / "small.template"
    template_file.write_text(small_template("ca-central-1_fakepool"))
    mocker.patch(
        "wps_tools.load_testing.manage_dlt.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "aws"),
    )
    args = parse_deploy_args("--template", str(template_file), "--aws-profile", "my-profile")

    with pytest.raises(SystemExit):
        run_deploy(args)


def test_run_deploy_partial_existing_vpc_args_exits(aws, tmp_path):
    template_file = tmp_path / "small.template"
    template_file.write_text(small_template("ca-central-1_fakepool"))
    args = parse_deploy_args(
        "--template", str(template_file), "--skip-sso-login", "--existing-vpc-id", "vpc-123"
    )

    with pytest.raises(SystemExit):
        run_deploy(args)  # existing-subnet-a/b omitted -- build_parameters should reject this


def test_run_teardown_missing_stack_returns_without_exit(aws):
    args = create_parser().parse_args(["teardown", "--region", REGION, "--yes"])

    run_teardown(args)  # should not raise -- a missing stack is treated as already torn down


def test_run_teardown_prompts_and_aborts_on_no(aws, mocker):
    cfn = aws.client("cloudformation")
    cfn.create_stack(StackName="my-stack", TemplateBody=small_template("ca-central-1_fakepool"))
    cfn.get_waiter("stack_create_complete").wait(StackName="my-stack")
    mocker.patch("builtins.input", return_value="n")
    args = create_parser().parse_args(["teardown", "--stack-name", "my-stack", "--region", REGION])

    run_teardown(args)

    cfn.describe_stacks(StackName="my-stack")  # still exists -- teardown was aborted


def test_run_teardown_yes_flag_deletes(aws):
    cfn = aws.client("cloudformation")
    cfn.create_stack(StackName="my-stack", TemplateBody=small_template("ca-central-1_fakepool"))
    cfn.get_waiter("stack_create_complete").wait(StackName="my-stack")
    args = create_parser().parse_args(["teardown", "--stack-name", "my-stack", "--region", REGION, "--yes"])

    run_teardown(args)

    with pytest.raises(Exception, match="does not exist"):
        cfn.describe_stacks(StackName="my-stack")


def test_run_teardown_failure_exits(aws, mocker):
    cfn = aws.client("cloudformation")
    cfn.create_stack(StackName="my-stack", TemplateBody=small_template("ca-central-1_fakepool"))
    cfn.get_waiter("stack_create_complete").wait(StackName="my-stack")
    mocker.patch("wps_tools.load_testing.manage_dlt.teardown_stack", side_effect=RuntimeError("boom"))
    args = create_parser().parse_args(["teardown", "--stack-name", "my-stack", "--region", REGION, "--yes"])

    with pytest.raises(SystemExit):
        run_teardown(args)
