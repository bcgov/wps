"""
Deploy or delete the Distributed Load Testing on AWS (headless) CloudFormation stack.

Usage:
    python3 -m wps_tools.load_testing.manage_dlt deploy --admin-name "Your Name" \
        --admin-email you@example.com --admin-password '<a-strong-password>'
    python3 -m wps_tools.load_testing.manage_dlt teardown --region ca-central-1
"""

import argparse
import hashlib
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import cast, get_args

import boto3
import requests
from botocore.exceptions import ClientError, WaiterError
from mypy_boto3_cloudformation.client import CloudFormationClient
from mypy_boto3_cloudformation.type_defs import ParameterTypeDef, StackResourceTypeDef, StackTypeDef
from mypy_boto3_cognito_idp.client import CognitoIdentityProviderClient
from mypy_boto3_ec2.client import EC2Client
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.literals import BucketLocationConstraintType
from mypy_boto3_s3.type_defs import (
    DeleteMarkerEntryTypeDef,
    ObjectIdentifierTypeDef,
    ObjectVersionTypeDef,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

DEFAULT_TEMPLATE_FILE = Path(__file__).parent / "distributed-load-testing-on-aws-headless.template"

# CloudFormation's hard limit for CreateStack's inline TemplateBody. Larger templates
# (like the bundled one, ~300KB) must be uploaded to S3 and passed as a TemplateURL instead.
CFN_INLINE_TEMPLATE_LIMIT_BYTES = 51_200


def cli_safe_value(value: str) -> str:
    """argparse type= validator for values that get passed as arguments to the `aws`/`dlt`
    subprocess (e.g. a profile name, username, password). A value starting with '-' would be
    interpreted by that downstream CLI as a different flag rather than as this argument's
    value, so reject it here instead of at the subprocess boundary."""
    if value.startswith("-"):
        raise argparse.ArgumentTypeError(f"must not start with '-' (got {value!r})")
    return value


def resolved_path(value: str) -> Path:
    """argparse type= validator for CLI-supplied filesystem paths. Resolves to an absolute,
    canonical path and rejects the target itself being a symlink, guarding against a symlink
    planted at that exact location redirecting a read/write to an unintended file."""
    path = Path(value).expanduser()
    if path.is_symlink():
        raise argparse.ArgumentTypeError(f"{path} is a symlink, refusing to use it")
    return path.resolve()


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--stack-name", default="distributed-load-testing", help="CloudFormation stack name"
    )
    common.add_argument("--region", help="AWS region (default: your profile's default region)")
    common.add_argument("--aws-profile", type=cli_safe_value, help="AWS named profile to use")

    deploy_parser = subparsers.add_parser("deploy", parents=[common], help="Deploy the stack")
    deploy_parser.add_argument(
        "--template",
        type=resolved_path,
        default=str(DEFAULT_TEMPLATE_FILE),
        help=f"Path to the CloudFormation template (default: bundled {DEFAULT_TEMPLATE_FILE.name})",
    )
    deploy_parser.add_argument(
        "--admin-name",
        type=cli_safe_value,
        required=True,
        help="Admin user name for the Cognito account",
    )
    deploy_parser.add_argument(
        "--admin-email", required=True, help="Admin user email for the Cognito account"
    )
    deploy_parser.add_argument(
        "--existing-vpc-id",
        help="Use an existing VPC instead of creating one (required if your account's SCPs block ec2:CreateVpc)",
    )
    deploy_parser.add_argument(
        "--existing-subnet-a", help="First existing subnet ID (required with --existing-vpc-id)"
    )
    deploy_parser.add_argument(
        "--existing-subnet-b", help="Second existing subnet ID (required with --existing-vpc-id)"
    )
    deploy_parser.add_argument(
        "--subnet-a-name",
        default="Prod-App-A",
        help=(
            "If none of --existing-vpc-id/--existing-subnet-a/--existing-subnet-b are given, look up a "
            "subnet by this Name tag and use it (default: Prod-App-A). See --create-vpc to disable."
        ),
    )
    deploy_parser.add_argument(
        "--subnet-b-name",
        default="Prod-App-B",
        help="Second subnet Name tag for the auto-lookup above",
    )
    deploy_parser.add_argument(
        "--create-vpc",
        action="store_true",
        help="Let CloudFormation create its own VPC instead of auto-resolving an existing one by name",
    )
    deploy_parser.add_argument(
        "--skip-sso-login",
        action="store_true",
        help="Don't run 'aws sso login' before deploying (it's a no-op if your session is already valid)",
    )
    deploy_parser.add_argument(
        "--template-bucket",
        help=(
            "S3 bucket to stage the template in (required if the template is over "
            f"{CFN_INLINE_TEMPLATE_LIMIT_BYTES} bytes, which the bundled one is). If omitted "
            "with --create-template-bucket, a name is derived from your account ID and region."
        ),
    )
    deploy_parser.add_argument(
        "--create-template-bucket",
        action="store_true",
        help="Create --template-bucket (or a derived name) if it doesn't already exist",
    )
    deploy_parser.add_argument(
        "--aws-exports-file",
        type=resolved_path,
        default="aws-exports.json",
        help="Where to write the 'dlt configure --from-file' config after deploy (default: aws-exports.json)",
    )
    deploy_parser.add_argument(
        "--skip-aws-exports", action="store_true", help="Don't write the aws-exports.json file"
    )
    deploy_parser.add_argument(
        "--dlt-cli-path",
        type=resolved_path,
        default=str(Path.home() / ".local" / "bin" / "dlt"),
        help="Where to install/find the dlt CLI (default: ~/.local/bin/dlt -- avoids needing sudo)",
    )
    deploy_parser.add_argument(
        "--admin-password",
        type=cli_safe_value,
        required=True,
        help=(
            "Permanent password for the admin user (must satisfy the pool's policy: 12+ chars, "
            "upper/lower/digit/symbol)"
        ),
    )
    deploy_parser.add_argument(
        "--skip-dlt-setup",
        action="store_true",
        help=(
            "Don't install/configure the dlt CLI, set a permanent admin password, or log in "
            "(implied by --skip-aws-exports, since dlt configure needs that file)"
        ),
    )

    teardown_parser = subparsers.add_parser("teardown", parents=[common], help="Delete the stack")
    teardown_parser.add_argument(
        "--empty-buckets",
        action="store_true",
        help=(
            "Empty S3 buckets created by the stack first (e.g. ScenariosBucket, which holds every "
            "uploaded script and test result). CloudFormation can't delete a non-empty bucket, so this "
            "is almost always required after any real usage -- but it's opt-in since it's destructive."
        ),
    )
    teardown_parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")

    return parser


def _ensure_sso_login(aws_profile: str | None) -> None:
    """Run `aws sso login` for the given profile. A no-op (fast) if the session is already valid;
    otherwise opens a browser and blocks until the user completes it there."""
    if not aws_profile:
        return
    # Also validated by argparse's `type=cli_safe_value` on --aws-profile, but re-checked here
    # since this function can be called directly, not only via the CLI.
    aws_profile = cli_safe_value(aws_profile)
    logger.info(
        "Ensuring SSO session is active for profile %s (opens a browser if needed)...", aws_profile
    )
    subprocess.run(["aws", "sso", "login", "--profile", aws_profile], check=True)


# Pinned to a specific commit (not `main`) and checksummed below so a compromised or rewritten
# upstream file can't be silently downloaded and made executable -- `main` is a moving target
# whose content we'd otherwise trust with no way to detect it changed underneath us.
DLT_CLI_COMMIT = "8672ef3edaecf5c27982f125cc418ae29208b1fb"
DLT_CLI_URL = (
    "https://raw.githubusercontent.com/aws-solutions/distributed-load-testing-on-aws/"
    f"{DLT_CLI_COMMIT}/deployment/cli/dlt-cli.mjs"
)
DLT_CLI_SHA256 = "ea512550b5341a68fbc873c34190324d5762c77188b1f02b3f01d1af9ff0957a"


def _install_dlt_cli(dest: Path) -> None:
    # Also validated by argparse's type=resolved_path on --dlt-cli-path, but re-resolved here
    # since this function can be called directly, not only via the CLI.
    dest = resolved_path(str(dest))
    if dest.is_file():
        logger.info("dlt CLI already installed at %s", dest)
        return
    logger.info("Installing dlt CLI to %s", dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(DLT_CLI_URL)
    response.raise_for_status()
    digest = hashlib.sha256(response.content).hexdigest()
    if digest != DLT_CLI_SHA256:
        raise RuntimeError(
            f"dlt CLI download from {DLT_CLI_URL} has unexpected SHA256 {digest} "
            f"(expected {DLT_CLI_SHA256}). Refusing to install -- if upstream genuinely updated "
            "the pinned commit, verify the new file and update DLT_CLI_COMMIT/DLT_CLI_SHA256."
        )
    dest.write_bytes(response.content)
    dest.chmod(0o755)


def set_permanent_password(
    cognito_client: CognitoIdentityProviderClient, user_pool_id: str, username: str, password: str
) -> None:
    logger.info("Setting a permanent password for %s", username)
    cognito_client.admin_set_user_password(
        UserPoolId=user_pool_id, Username=username, Password=password, Permanent=True
    )


# The only literal flags this module ever passes to the dlt CLI (see run_deploy's two
# _run_dlt_command calls). Any other flag-like ("-"-prefixed) element in `args` would have to be
# an unvalidated value slipping into a flag's position, e.g. an admin name/password that
# somehow reached here without going through argparse's cli_safe_value check -- so reject it
# rather than let the dlt CLI (mis)interpret it as a different flag.
KNOWN_DLT_FLAGS = {"--srp", "--username", "--password", "--from-file"}


def _run_dlt_command(dlt_path: Path, args: list[str]) -> None:
    for arg in args:
        if arg.startswith("-") and arg not in KNOWN_DLT_FLAGS:
            raise ValueError(f"Refusing to run dlt with unexpected flag-like argument: {arg!r}")
    subprocess.run([str(dlt_path), *args], check=True)


def find_subnet_by_name(ec2_client: EC2Client, name: str) -> tuple[str, str]:
    """Returns (subnet_id, vpc_id) for the subnet with this exact Name tag."""
    response = ec2_client.describe_subnets(Filters=[{"Name": "tag:Name", "Values": [name]}])
    subnets = response.get("Subnets", [])
    if not subnets:
        raise RuntimeError(f"No subnet found named {name!r}")
    if len(subnets) > 1:
        ids = [s["SubnetId"] for s in subnets]
        raise RuntimeError(f"Multiple subnets named {name!r}: {ids}")

    subnet = subnets[0]
    subnet_id = subnet.get("SubnetId")
    vpc_id = subnet.get("VpcId")
    if not subnet_id or not vpc_id:
        raise RuntimeError(f"Subnet named {name!r} is missing SubnetId/VpcId: {subnet}")
    return subnet_id, vpc_id


def resolve_existing_vpc(
    ec2_client: EC2Client, subnet_a_name: str, subnet_b_name: str
) -> tuple[str, str, str]:
    """Returns (vpc_id, subnet_a_id, subnet_b_id) by looking up two subnets by Name tag."""
    subnet_a_id, vpc_id_a = find_subnet_by_name(ec2_client, subnet_a_name)
    subnet_b_id, vpc_id_b = find_subnet_by_name(ec2_client, subnet_b_name)

    if vpc_id_a != vpc_id_b:
        raise RuntimeError(
            f"{subnet_a_name} and {subnet_b_name} are in different VPCs ({vpc_id_a} vs {vpc_id_b})"
        )

    return vpc_id_a, subnet_a_id, subnet_b_id


def build_parameters(
    admin_name: str,
    admin_email: str,
    existing_vpc_id: str | None = None,
    existing_subnet_a: str | None = None,
    existing_subnet_b: str | None = None,
) -> list[ParameterTypeDef]:
    parameters: list[ParameterTypeDef] = [
        {"ParameterKey": "AdminName", "ParameterValue": admin_name},
        {"ParameterKey": "AdminEmail", "ParameterValue": admin_email},
    ]

    if existing_vpc_id or existing_subnet_a or existing_subnet_b:
        if not existing_vpc_id or not existing_subnet_a or not existing_subnet_b:
            raise ValueError(
                "--existing-vpc-id, --existing-subnet-a, and --existing-subnet-b must be used together"
            )
        parameters += [
            {"ParameterKey": "ExistingVPCId", "ParameterValue": existing_vpc_id},
            {"ParameterKey": "ExistingSubnetA", "ParameterValue": existing_subnet_a},
            {"ParameterKey": "ExistingSubnetB", "ParameterValue": existing_subnet_b},
        ]

    return parameters


def build_aws_exports(outputs: dict[str, str], region: str) -> dict[str, str]:
    """Map CloudFormation stack outputs to the JSON shape `dlt configure --from-file` expects."""
    api_endpoint = next((v for k, v in outputs.items() if k.startswith("DLTApiEndpoint")), None)
    user_pool_id = outputs.get("CognitoUserPoolID")
    pool_client_id = outputs.get("CognitoAppClientID")
    identity_pool_id = outputs.get("CognitoIdentityPoolID")
    user_files_bucket = outputs.get("ScenariosBucket")
    solution_uuid = outputs.get("SolutionUUID")

    if (
        not api_endpoint
        or not user_pool_id
        or not pool_client_id
        or not identity_pool_id
        or not user_files_bucket
        or not solution_uuid
    ):
        raise RuntimeError(
            f"Could not build aws-exports.json, missing expected stack outputs: {outputs}"
        )

    return {
        "ApiEndpoint": api_endpoint,
        "UserPoolId": user_pool_id,
        "PoolClientId": pool_client_id,
        "IdentityPoolId": identity_pool_id,
        "UserFilesBucket": user_files_bucket,
        # The DLT CLI uses this as the full Cognito hosted-UI hostname (`https://{UserPoolDomain}/oauth2/authorize`),
        # not just the domain prefix -- it doesn't append .auth.<region>.amazoncognito.com itself.
        "UserPoolDomain": f"dlt-{solution_uuid}.auth.{region}.amazoncognito.com",
    }


def build_template_url(bucket: str, key: str, region: str) -> str:
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


def build_template_bucket_name(account_id: str, region: str) -> str:
    return f"dlt-template-staging-{account_id}-{region}"


def ensure_template_bucket(s3_client: S3Client, bucket: str, region: str) -> None:
    try:
        s3_client.head_bucket(Bucket=bucket)
        logger.info("Using existing bucket %s", bucket)
        return
    except ClientError as e:
        if e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 404:
            raise

    logger.info("Creating bucket %s", bucket)
    if region == "us-east-1":
        # us-east-1 is the default region and doesn't take a LocationConstraint.
        s3_client.create_bucket(Bucket=bucket)
        return

    if region not in get_args(BucketLocationConstraintType):
        raise ValueError(f"Not a valid S3 bucket region: {region}")
    location_constraint = cast(BucketLocationConstraintType, region)
    s3_client.create_bucket(
        Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": location_constraint}
    )


def stage_template(
    s3_client: S3Client, bucket: str, stack_name: str, template_path: Path, region: str
) -> str:
    key = f"{stack_name}/{template_path.name}"
    logger.info("Uploading %s to s3://%s/%s", template_path, bucket, key)
    s3_client.upload_file(str(template_path), bucket, key)
    return build_template_url(bucket, key, region)


def deploy_stack(
    cfn_client: CloudFormationClient,
    stack_name: str,
    parameters: list[ParameterTypeDef],
    *,
    template_body: str | None = None,
    template_url: str | None = None,
) -> StackTypeDef:
    template_kwargs = (
        {"TemplateURL": template_url} if template_url else {"TemplateBody": template_body}
    )

    logger.info("Creating stack %s", stack_name)
    cfn_client.create_stack(
        StackName=stack_name,
        Parameters=parameters,
        Capabilities=["CAPABILITY_NAMED_IAM"],
        **template_kwargs,
    )

    logger.info("Waiting for stack create to complete...")
    waiter = cfn_client.get_waiter("stack_create_complete")
    waiter.wait(StackName=stack_name)

    [stack] = cfn_client.describe_stacks(StackName=stack_name)["Stacks"]
    return stack


def filter_bucket_names(resources: list[StackResourceTypeDef]) -> list[str]:
    return [
        r["PhysicalResourceId"]
        for r in resources
        if r["ResourceType"] == "AWS::S3::Bucket" and r.get("PhysicalResourceId")
    ]


def build_delete_batch(
    versions: list[ObjectVersionTypeDef], delete_markers: list[DeleteMarkerEntryTypeDef]
) -> list[ObjectIdentifierTypeDef]:
    return [{"Key": v["Key"], "VersionId": v["VersionId"]} for v in [*versions, *delete_markers]]


def empty_bucket(s3_client: S3Client, bucket: str) -> None:
    logger.info("Emptying bucket %s", bucket)
    paginator = s3_client.get_paginator("list_object_versions")
    for page in paginator.paginate(Bucket=bucket):
        batch = build_delete_batch(page.get("Versions", []), page.get("DeleteMarkers", []))
        if batch:
            s3_client.delete_objects(Bucket=bucket, Delete={"Objects": batch})


def get_failure_reasons(cfn_client: CloudFormationClient, stack_name: str) -> list[str]:
    events = cfn_client.describe_stack_events(StackName=stack_name)["StackEvents"]
    return [
        f"{e['LogicalResourceId']}: {e.get('ResourceStatusReason', '')}"
        for e in events
        if e["ResourceStatus"].endswith("FAILED")
    ]


def teardown_stack(
    cfn_client: CloudFormationClient, s3_client: S3Client, stack_name: str, empty_buckets: bool
) -> None:
    if empty_buckets:
        resources = cfn_client.describe_stack_resources(StackName=stack_name)["StackResources"]
        for bucket in filter_bucket_names(resources):
            empty_bucket(s3_client, bucket)

    logger.info("Deleting stack %s", stack_name)
    cfn_client.delete_stack(StackName=stack_name)

    logger.info("Waiting for stack delete to complete...")
    waiter = cfn_client.get_waiter("stack_delete_complete")
    try:
        waiter.wait(StackName=stack_name)
    except WaiterError as e:
        reasons = get_failure_reasons(cfn_client, stack_name)
        reason_text = "\n".join(reasons) if reasons else str(e)
        raise RuntimeError(
            f"Stack deletion failed:\n{reason_text}\n\n"
            "If this is because an S3 bucket isn't empty, retry with --empty-buckets."
        ) from e


def resolve_region(session: boto3.Session) -> str:
    if not session.region_name:
        logger.error("--region (or a default region on your profile) is required")
        sys.exit(1)
    return session.region_name


def run_deploy(args: argparse.Namespace) -> None:
    template_path: Path = args.template  # already resolved + symlink-checked by resolved_path
    if not template_path.is_file():
        logger.error("Template not found: %s", template_path)
        sys.exit(1)

    if not args.skip_sso_login:
        try:
            _ensure_sso_login(args.aws_profile)
        except subprocess.CalledProcessError as e:
            logger.error("aws sso login failed: %s", e)
            sys.exit(1)

    session = boto3.Session(profile_name=args.aws_profile, region_name=args.region)
    region = resolve_region(session)
    cfn: CloudFormationClient = session.client("cloudformation")

    existing_vpc_id = args.existing_vpc_id
    existing_subnet_a = args.existing_subnet_a
    existing_subnet_b = args.existing_subnet_b
    if (
        not args.create_vpc
        and not existing_vpc_id
        and not existing_subnet_a
        and not existing_subnet_b
    ):
        ec2: EC2Client = session.client("ec2")
        try:
            existing_vpc_id, existing_subnet_a, existing_subnet_b = resolve_existing_vpc(
                ec2, args.subnet_a_name, args.subnet_b_name
            )
        except RuntimeError as e:
            logger.error(
                "%s. Pass --existing-vpc-id/--existing-subnet-a/--existing-subnet-b explicitly, or "
                "--create-vpc to let CloudFormation create its own VPC.",
                e,
            )
            sys.exit(1)
        logger.info(
            "Using existing VPC %s (subnets %s, %s)",
            existing_vpc_id,
            existing_subnet_a,
            existing_subnet_b,
        )

    try:
        parameters = build_parameters(
            args.admin_name,
            args.admin_email,
            existing_vpc_id,
            existing_subnet_a,
            existing_subnet_b,
        )
    except ValueError as e:
        logger.error(e)
        sys.exit(1)
    template_size = template_path.stat().st_size

    if template_size > CFN_INLINE_TEMPLATE_LIMIT_BYTES:
        if not args.template_bucket and not args.create_template_bucket:
            logger.error(
                "Template is %d bytes, over CloudFormation's %d byte inline limit. Pass --template-bucket "
                "(an S3 bucket you can write to), or --create-template-bucket to have one created for you.",
                template_size,
                CFN_INLINE_TEMPLATE_LIMIT_BYTES,
            )
            sys.exit(1)

        s3: S3Client = session.client("s3")
        bucket = args.template_bucket
        if not bucket:
            sts = session.client("sts")
            account_id = sts.get_caller_identity()["Account"]
            bucket = build_template_bucket_name(account_id, region)

        if args.create_template_bucket:
            ensure_template_bucket(s3, bucket, region)

        template_url = stage_template(s3, bucket, args.stack_name, template_path, region)
        stack = deploy_stack(cfn, args.stack_name, parameters, template_url=template_url)
    else:
        stack = deploy_stack(
            cfn, args.stack_name, parameters, template_body=template_path.read_text()
        )

    print(json.dumps(stack, indent=2, default=str))

    outputs = {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}
    aws_exports = build_aws_exports(outputs, region)

    if args.skip_aws_exports:
        return

    aws_exports_path: Path = (
        args.aws_exports_file
    )  # already resolved + symlink-checked by resolved_path
    aws_exports_path.write_text(json.dumps(aws_exports, indent=2) + "\n")
    logger.info("Wrote %s", aws_exports_path)

    if args.skip_dlt_setup:
        logger.info("Run: dlt configure --from-file %s", aws_exports_path)
        return

    dlt_path: Path = args.dlt_cli_path  # already resolved + symlink-checked by resolved_path
    try:
        _install_dlt_cli(dlt_path)
        _run_dlt_command(dlt_path, ["configure", "--from-file", str(aws_exports_path)])

        cognito: CognitoIdentityProviderClient = session.client("cognito-idp")
        set_permanent_password(
            cognito, aws_exports["UserPoolId"], args.admin_name, args.admin_password
        )

        _run_dlt_command(
            dlt_path,
            ["login", "--srp", "--username", args.admin_name, "--password", args.admin_password],
        )
    except (subprocess.CalledProcessError, requests.RequestException, ClientError, ValueError) as e:
        logger.error(
            "dlt CLI setup failed: %s. Fix the issue and finish manually with: dlt configure --from-file %s",
            e,
            aws_exports_path,
        )
        sys.exit(1)

    logger.info("Logged in as %s. Run a test with:", args.admin_name)
    logger.info(
        "  uv run --project packages/wps-tools python -m wps_tools.load_testing.run_k6_test "
        "<script.js> --stack-name %s --region %s",
        args.stack_name,
        region,
    )


def run_teardown(args: argparse.Namespace) -> None:
    session = boto3.Session(profile_name=args.aws_profile, region_name=args.region)
    region = resolve_region(session)
    cfn: CloudFormationClient = session.client("cloudformation")

    try:
        cfn.describe_stacks(StackName=args.stack_name)
    except ClientError as e:
        if "does not exist" in str(e):
            logger.info("Stack %s does not exist (already deleted?)", args.stack_name)
            return
        logger.error(e)
        sys.exit(1)

    if not args.yes:
        response = input(f"Delete stack '{args.stack_name}' in {region}? This is permanent. [y/N] ")
        if response.strip().lower() != "y":
            logger.info("Aborted.")
            return

    s3: S3Client = session.client("s3")

    try:
        teardown_stack(cfn, s3, args.stack_name, args.empty_buckets)
    except RuntimeError as e:
        logger.error(e)
        sys.exit(1)

    logger.info("Stack %s deleted.", args.stack_name)


def main() -> None:
    args = create_parser().parse_args()
    if args.command == "deploy":
        run_deploy(args)
    else:
        run_teardown(args)


if __name__ == "__main__":
    main()
