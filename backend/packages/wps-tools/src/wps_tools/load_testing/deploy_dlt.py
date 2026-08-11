"""
Deploy the Distributed Load Testing on AWS (headless) CloudFormation stack.

Usage:
    python3 -m wps_tools.load_testing.deploy_dlt --admin-name "Your Name" --admin-email you@example.com
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import cast, get_args

import boto3
from botocore.exceptions import ClientError
from mypy_boto3_cloudformation.client import CloudFormationClient
from mypy_boto3_cloudformation.type_defs import ParameterTypeDef, StackTypeDef
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.literals import BucketLocationConstraintType

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


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--template",
        default=str(DEFAULT_TEMPLATE_FILE),
        help=f"Path to the CloudFormation template (default: bundled {DEFAULT_TEMPLATE_FILE.name})",
    )
    parser.add_argument("--admin-name", required=True, help="Admin user name for the Cognito account")
    parser.add_argument("--admin-email", required=True, help="Admin user email for the Cognito account")
    parser.add_argument("--stack-name", default="distributed-load-testing", help="CloudFormation stack name")
    parser.add_argument(
        "--existing-vpc-id",
        help="Use an existing VPC instead of creating one (required if your account's SCPs block ec2:CreateVpc)",
    )
    parser.add_argument("--existing-subnet-a", help="First existing subnet ID (required with --existing-vpc-id)")
    parser.add_argument("--existing-subnet-b", help="Second existing subnet ID (required with --existing-vpc-id)")
    parser.add_argument("--aws-profile", help="AWS named profile to use")
    parser.add_argument("--region", help="AWS region to deploy into")
    parser.add_argument(
        "--template-bucket",
        help=(
            "S3 bucket to stage the template in (required if the template is over "
            f"{CFN_INLINE_TEMPLATE_LIMIT_BYTES} bytes, which the bundled one is). If omitted "
            "with --create-template-bucket, a name is derived from your account ID and region."
        ),
    )
    parser.add_argument(
        "--create-template-bucket",
        action="store_true",
        help="Create --template-bucket (or a derived name) if it doesn't already exist",
    )
    parser.add_argument(
        "--aws-exports-file",
        default="aws-exports.json",
        help="Where to write the 'dlt configure --from-file' config after deploy (default: aws-exports.json)",
    )
    parser.add_argument("--skip-aws-exports", action="store_true", help="Don't write the aws-exports.json file")
    return parser


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
            raise ValueError("--existing-vpc-id, --existing-subnet-a, and --existing-subnet-b must be used together")
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
        raise RuntimeError(f"Could not build aws-exports.json, missing expected stack outputs: {outputs}")

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
    s3_client.create_bucket(Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": location_constraint})


def stage_template(s3_client: S3Client, bucket: str, stack_name: str, template_path: Path, region: str) -> str:
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
    template_kwargs = {"TemplateURL": template_url} if template_url else {"TemplateBody": template_body}

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


def main() -> None:
    args = create_parser().parse_args()

    template_path = Path(args.template)
    if not template_path.is_file():
        logger.error("Template not found: %s", template_path)
        sys.exit(1)

    session = boto3.Session(profile_name=args.aws_profile, region_name=args.region)
    if not session.region_name:
        logger.error("--region (or a default region on your profile) is required")
        sys.exit(1)
    region = session.region_name
    cfn: CloudFormationClient = session.client("cloudformation")

    try:
        parameters = build_parameters(
            args.admin_name,
            args.admin_email,
            args.existing_vpc_id,
            args.existing_subnet_a,
            args.existing_subnet_b,
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
        stack = deploy_stack(cfn, args.stack_name, parameters, template_body=template_path.read_text())

    print(json.dumps(stack, indent=2, default=str))

    if args.skip_aws_exports:
        return

    outputs = {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}
    aws_exports = build_aws_exports(outputs, region)

    aws_exports_path = Path(args.aws_exports_file)
    aws_exports_path.write_text(json.dumps(aws_exports, indent=2) + "\n")
    logger.info("Wrote %s", aws_exports_path)
    logger.info("Run: dlt configure --from-file %s", aws_exports_path)


if __name__ == "__main__":
    main()
