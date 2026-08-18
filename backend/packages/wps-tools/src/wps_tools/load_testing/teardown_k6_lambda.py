"""
Tears down every AWS resource deploy_k6_lambda.py and verify_ip_diversity.py can create: the
k6-on-Lambda function, the IP-diversity probe function, the k6 runtime layer, the S3 bucket
staging the layer zip, the shared IAM execution role, and the CloudWatch Logs log groups
Lambda auto-creates for each function on first invocation.

Usage:
    python3 -m wps_tools.load_testing.teardown_k6_lambda --region ca-central-1
    python3 -m wps_tools.load_testing.teardown_k6_lambda \\
        --regions ca-central-1,ca-west-1,us-west-1,us-west-2 --yes
"""

import argparse
import logging
import sys

import boto3
from botocore.exceptions import ClientError
from mypy_boto3_iam.client import IAMClient
from mypy_boto3_lambda.client import LambdaClient
from mypy_boto3_logs.client import CloudWatchLogsClient
from mypy_boto3_s3.client import S3Client

from wps_tools.load_testing.deploy_k6_lambda import (
    BASIC_EXECUTION_POLICY_ARN,
    DEFAULT_FUNCTION_NAME,
    DEFAULT_LAYER_NAME,
    DEFAULT_ROLE_NAME,
    build_layer_bucket_name,
    resolve_regions,
    run_per_region,
)
from wps_tools.load_testing.verify_ip_diversity import (
    DEFAULT_FUNCTION_NAME as DEFAULT_PROBE_FUNCTION_NAME,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    region_group = parser.add_mutually_exclusive_group(required=True)
    region_group.add_argument("--region", help="AWS region to tear down")
    region_group.add_argument(
        "--regions",
        help="Comma-separated AWS regions to tear down (e.g. one per --regions "
        "used at deploy time)",
    )
    parser.add_argument("--aws-profile", help="AWS named profile to use")
    parser.add_argument("--function-name", default=DEFAULT_FUNCTION_NAME)
    parser.add_argument("--probe-function-name", default=DEFAULT_PROBE_FUNCTION_NAME)
    parser.add_argument("--layer-name", default=DEFAULT_LAYER_NAME)
    parser.add_argument("--role-name", default=DEFAULT_ROLE_NAME)
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")
    return parser


def delete_function_if_exists(lambda_client: LambdaClient, function_name: str) -> None:
    try:
        lambda_client.delete_function(FunctionName=function_name)
        logger.info("Deleted function %s", function_name)
    except lambda_client.exceptions.ResourceNotFoundException:
        logger.info("Function %s does not exist, nothing to delete", function_name)


def delete_log_group_if_exists(logs_client: CloudWatchLogsClient, function_name: str) -> None:
    # Lambda auto-creates this on the function's first invocation; deleting the function
    # itself leaves the log group behind.
    log_group_name = f"/aws/lambda/{function_name}"
    try:
        logs_client.delete_log_group(logGroupName=log_group_name)
        logger.info("Deleted log group %s", log_group_name)
    except logs_client.exceptions.ResourceNotFoundException:
        logger.info("Log group %s does not exist, nothing to delete", log_group_name)


def delete_layer_versions(lambda_client: LambdaClient, layer_name: str) -> None:
    paginator = lambda_client.get_paginator("list_layer_versions")
    deleted = 0
    for page in paginator.paginate(LayerName=layer_name):
        for version in page["LayerVersions"]:
            lambda_client.delete_layer_version(
                LayerName=layer_name, VersionNumber=version["Version"]
            )
            deleted += 1
    logger.info("Deleted %d version(s) of layer %s", deleted, layer_name)


def empty_and_delete_bucket(s3_client: S3Client, bucket: str) -> None:
    try:
        s3_client.head_bucket(Bucket=bucket)
    except ClientError as e:
        if e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
            logger.info("Bucket %s does not exist, nothing to delete", bucket)
            return
        raise

    paginator = s3_client.get_paginator("list_object_versions")
    for page in paginator.paginate(Bucket=bucket):
        batch = [
            {"Key": v["Key"], "VersionId": v["VersionId"]}
            for v in [*page.get("Versions", []), *page.get("DeleteMarkers", [])]
        ]
        if batch:
            s3_client.delete_objects(Bucket=bucket, Delete={"Objects": batch})

    s3_client.delete_bucket(Bucket=bucket)
    logger.info("Deleted bucket %s", bucket)


def delete_execution_role(iam_client: IAMClient, role_name: str) -> None:
    try:
        iam_client.detach_role_policy(RoleName=role_name, PolicyArn=BASIC_EXECUTION_POLICY_ARN)
    except ClientError:
        # Either the role is already gone, or it exists without the policy attached --
        # either way there's nothing to detach, and delete_role below still reports whether
        # the role itself needs deleting.
        pass

    try:
        iam_client.delete_role(RoleName=role_name)
        logger.info("Deleted IAM role %s", role_name)
    except iam_client.exceptions.NoSuchEntityException:
        logger.info("IAM role %s does not exist, nothing to delete", role_name)


def run_teardown(args: argparse.Namespace) -> None:
    regions = resolve_regions(args)

    if not args.yes:
        response = input(
            f"Tear down k6 load-testing resources ({args.function_name}, "
            f"{args.probe_function_name}, layer {args.layer_name}, role {args.role_name}, "
            f"their S3 staging buckets, and their CloudWatch log groups) in "
            f"{', '.join(regions)}? This is permanent. [y/N] "
        )
        if response.strip().lower() != "y":
            logger.info("Aborted.")
            return

    iam_session = boto3.Session(profile_name=args.aws_profile, region_name=regions[0])
    account_id = iam_session.client("sts").get_caller_identity()["Account"]

    def teardown_one_region(region: str) -> None:
        session = boto3.Session(profile_name=args.aws_profile, region_name=region)
        lambda_client: LambdaClient = session.client("lambda")
        s3_client: S3Client = session.client("s3")
        logs_client: CloudWatchLogsClient = session.client("logs")

        delete_function_if_exists(lambda_client, args.function_name)
        delete_function_if_exists(lambda_client, args.probe_function_name)
        delete_log_group_if_exists(logs_client, args.function_name)
        delete_log_group_if_exists(logs_client, args.probe_function_name)
        delete_layer_versions(lambda_client, args.layer_name)
        empty_and_delete_bucket(s3_client, build_layer_bucket_name(account_id, region))

    _, failed_regions = run_per_region(regions, teardown_one_region)

    # IAM has no per-region endpoint -- the role is global, shared across every region's
    # function, so it's only deleted once all regions have been torn down.
    delete_execution_role(iam_session.client("iam"), args.role_name)

    if failed_regions:
        logger.error(
            "Teardown failed in %d/%d region(s): %s",
            len(failed_regions),
            len(regions),
            ", ".join(failed_regions),
        )
        sys.exit(1)

    logger.info("Teardown complete.")


def main() -> None:
    run_teardown(create_parser().parse_args())


if __name__ == "__main__":
    main()
