# Load testing

Tooling for the [Distributed Load Testing on AWS](https://aws.amazon.com/solutions/implementations/distributed-load-testing-on-aws/)
solution, deployed headless (backend only, no hosted web console) via
`distributed-load-testing-on-aws-headless.template`, bundled alongside this code.

## AWS credentials

`deploy_dlt` and `run_k6_test` both use `boto3`, which needs AWS credentials
available before you run them. If your account uses IAM Identity Center
(SSO), which is the common case for gov.bc.ca AWS accounts:

```bash
aws configure sso   # first time only, names a profile
aws sso login --profile <profile-name>
```

Then pass `--aws-profile <profile-name>` to `deploy_dlt`/`run_k6_test`, or
`export AWS_PROFILE=<profile-name>` so you don't have to repeat it. If your
account uses static access keys instead, use `aws configure` instead of the
SSO flow above.

## Deploy

```bash
uv run --project packages/wps-tools python -m wps_tools.load_testing.deploy_dlt \
  --admin-name "Your Name" --admin-email you@example.com \
  --region ca-central-1 --aws-profile <profile-name> \
  --template-bucket <an-s3-bucket-you-can-write-to>
```

The bundled template is ~300KB, over CloudFormation's 51,200-byte limit for
passing `TemplateBody` inline (and `TemplateURL` only accepts S3 or SSM
document URLs, so it has to be staged in S3 and deployed via `TemplateURL` instead.
 `--template-bucket` takes any existing S3 bucket you have write
access to (it doesn't need to be dedicated to this; 
the template is uploaded under a `<stack-name>/` prefix).

If you don't have a bucket, add `--create-template-bucket` to have one
created for you (name derived from your account ID and region, or pass
`--template-bucket <name> --create-template-bucket` together to control the
name). Requires `s3:CreateBucket` permission; it's created once and reused
on subsequent deploys.

This creates the stack (`distributed-load-testing` by default), waits for
`CREATE_COMPLETE`, prints the stack's `describe-stacks` output, and writes
`aws-exports.json` in the current directory. A headless deployment has no
console to download this from, so it's built from stack outputs (see
`build_aws_exports` for the mapping, including `UserPoolDomain`, which isn't
an output at all and has to be derived as `dlt-<SolutionUUID>`). Pass
`--skip-aws-exports` to skip writing it, or `--aws-exports-file` to change
where it's written. `AdminName` and `AdminEmail` are the only required
parameters; every other template parameter has a working default (VPC/subnet
CIDRs, egress CIDR, image tagging, optional MCP server). Pass
`--stack-name`/`--aws-profile`/`--region` to override defaults, or
`--template` to deploy a different template than the bundled one; see
`--help` for details.

By default the template creates its own VPC, subnets, and Internet Gateway.
Some accounts (e.g. BC Gov's landing zone) have an AWS Organizations Service
Control Policy that denies `ec2:CreateVpc`/`ec2:CreateInternetGateway`
outright, which fails the stack with a `ROLLBACK_COMPLETE` and an
`AccessDenied`/"explicit deny in a service control policy" error in the
stack events (`aws cloudformation describe-stack-events --stack-name
<name>`). If you hit that, delete the failed stack
(`aws cloudformation delete-stack --stack-name <name>`) and redeploy with an
existing VPC + two subnets instead:

```bash
uv run --project packages/wps-tools python -m wps_tools.load_testing.deploy_dlt \
  --admin-name "Your Name" --admin-email you@example.com \
  --region ca-central-1 --aws-profile <profile-name> \
  --template-bucket <an-s3-bucket-you-can-write-to> \
  --existing-vpc-id vpc-xxxxxxxx --existing-subnet-a subnet-xxxxxxxx --existing-subnet-b subnet-yyyyyyyy
```

All three of `--existing-vpc-id`/`--existing-subnet-a`/`--existing-subnet-b`
are required together. Find candidates with:

```bash
aws ec2 describe-vpcs --region ca-central-1 --profile <profile-name> \
  --query "Vpcs[].[VpcId,CidrBlock,Tags[?Key=='Name'].Value|[0]]" --output table
aws ec2 describe-subnets --region ca-central-1 --profile <profile-name> --filters Name=vpc-id,Values=<vpc-id> \
  --query "Subnets[].[SubnetId,AvailabilityZone,CidrBlock,Tags[?Key=='Name'].Value|[0]]" --output table
```

## Running a k6 test

Since it's a headless deployment, test scenarios are created directly against
the backend REST API (`DLTApiEndpoint` stack output), and k6 scripts are
uploaded straight to the `ScenariosBucket` S3 bucket, under a `public/`
prefix -- the Cognito authenticated role's IAM policy scopes `s3:PutObject`
to `ScenariosBucket/public/*` only (matching Amplify Storage's "public"
access level, which the web console uploads through), so anything uploaded
outside that prefix gets `AccessDenied`.

1. Install the [DLT CLI](https://github.com/aws-solutions/distributed-load-testing-on-aws/blob/main/source/cli/README.md)
   and log in (handles Cognito auth, including SRP), using the
   `aws-exports.json` written by `deploy_dlt`:
   ```bash
   curl -sLo /usr/local/bin/dlt \
     https://raw.githubusercontent.com/aws-solutions/distributed-load-testing-on-aws/main/deployment/cli/dlt-cli.mjs
   chmod +x /usr/local/bin/dlt
   dlt configure --from-file aws-exports.json
   dlt login --srp --username admin@example.com
   ```
2. Run `run_k6_test` to upload the script, create the scenario, and poll
   until it finishes. It uses the AWS credentials `dlt login` writes to
   `~/.dlt/credentials.json` for both the S3 upload and the `POST
   /scenarios` call -- that endpoint's `AuthorizationType` is `AWS_IAM`
   (`execute-api:Invoke`), so requests are SigV4-signed with those
   credentials rather than sent with the Cognito ID token as a bearer
   token. k6 scripts live in `k6_scripts/`:
   ```bash
   uv run --project packages/wps-tools python -m wps_tools.load_testing.run_k6_test \
     k6_scripts/<name>.js --stack-name distributed-load-testing --region ca-central-1
   ```
   Pass `--api-endpoint`/`--scenarios-bucket` instead of `--stack-name` to skip
   the CloudFormation lookup, and `--poll-interval` to change how often it
   checks status. See `--help` for concurrency/ramp-up/hold-for/task-count
   options.

   **Important:** `POST /scenarios` starts a run immediately -- it is not a
   separate step from `dlt scenarios start`. Don't call `dlt scenarios
   start` after this script creates a scenario; that creates a second run
   that races the first one for the same ECS service name and both fail
   with `"Creation of service was not idempotent"`. This script polls for
   completion itself for exactly that reason, instead of shelling out to
   `dlt scenarios start --wait`.
