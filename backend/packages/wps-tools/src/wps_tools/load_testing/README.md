# Load testing

Tooling for the [Distributed Load Testing on AWS](https://aws.amazon.com/solutions/implementations/distributed-load-testing-on-aws/)
solution, deployed headless (backend only, no hosted web console) via
`distributed-load-testing-on-aws-headless.template`, bundled alongside this code.

## Architecture

The template deploys a set of interacting AWS services, not a single app --
worth understanding before running anything, since several of the gotchas
below come directly from this shape:

- **Auth.** A Cognito User Pool holds one admin user, seeded from the
  `--admin-name`/`--admin-email` you pass to `manage_dlt deploy`. A Cognito
  Identity Pool federates that User Pool and issues *temporary AWS
  credentials* to authenticated users -- these are what `dlt login` caches
  and what `run_k6_test.py` reuses directly for both the S3 script upload
  and the API call, rather than re-implementing Cognito auth itself.
- **API.** An API Gateway REST API (the `DLTApiEndpoint` stack output)
  fronts everything. Its `/scenarios` resource uses `AWS_IAM` authorization
  (`execute-api:Invoke`), not the Cognito User Pool's JWT. Requests must
  be SigV4-signed with the Identity Pool credentials above, not sent with
  the ID token as a bearer header.
- **Orchestration.** API Gateway invokes Lambda microservices (task runner,
  stabilization checker, test cleanup, results parser, and others) that
  drive a Step Functions state machine. Creating a scenario (`POST
  /scenarios`) both stores its definition *and* immediately starts a new
  Step Functions execution for a fresh run.
- **Execution.** Per requested region, the state machine creates an ECS
  Fargate *service* (not a bare task) running the solution's bundled
  `distributed-load-testing-on-aws-load-tester` container image. That
  container downloads the test's JSON config and script from S3, installs
  k6 (or JMeter/Locust) at runtime, waits for a synchronized "start signal"
  file in S3 so multi-region tasks begin together, wraps the script with
  Taurus/BZT, runs it, and uploads results.
- **Storage.**
  - S3 `ScenariosBucket` -- scripts under `public/test-scenarios/<type>/<testId>.<ext>`
    (must be under `public/`; that's the only prefix the Identity Pool
    role's IAM policy grants `s3:PutObject` on), results under
    `results/<testId>/<runPrefix>/` (raw k6 CSV, k6 stdout/stderr, Taurus/BZT log).
  - DynamoDB -- scenario definitions and per-run summary stats
    (requests/success/errors/response-time percentiles). This is what `dlt
    runs latest` and `GET /scenarios/{testId}/testruns` read -- not the raw
    S3 CSV. Its update code (`updateTestDBEntry`) references a `:sl`
    (`showLive`) placeholder in its `UpdateExpression` unconditionally, even
    though `showLive` is optional in the create-scenario validation schema
    -- omit it from the request entirely (rather than sending `false`) and
    you get a 500 (`Invalid UpdateExpression... attribute value: :sl`) at
    creation time, despite the payload itself validating fine. A real
    backend bug, not a client-side mistake; `run_k6_test.py` always sends
    `"showLive": false` explicitly for exactly this reason.
  - CloudWatch Logs -- one log stream per ECS task, in a log group named
    `<stack-name>-DLTEcsDLTCloudWatchLogsGroup...`.
  - CloudWatch Metrics + a per-test Dashboard (`EcsLoadTesting-<testId>-<region>`),
    populated via Logs Metric Filters that extract numeric values from the
    container's log stream.
- **Cleanup.** After a run finishes (or is cancelled), a `TestCleanup`
  Lambda scales the ECS service to zero, deletes it, deregisters its task
  definition, and removes the CloudWatch Metric Filters it created.
- **Optional MCP server.** If deployed with that option, a Bedrock
  AgentCore Gateway + Lambda expose scenario/run data to AI agents over
  MCP. Unrelated to anything in this package.

## The `dlt` CLI

The command-line client shipped with the solution (`source/cli` in the
[GitHub repo](https://github.com/aws-solutions/distributed-load-testing-on-aws)),
distributed as a single bundled Node.js script.

**Auth modes** (`dlt login`): `--srp --username <name>` (SRP -- password via
`--password <value>` or, preferably, the `DLT_PASSWORD` env var, so it
doesn't land in shell history) or `--iam` (uses whatever AWS credentials are
already active in the shell). Both write the same shape to
`~/.dlt/credentials.json` -- a Cognito ID token plus Identity Pool STS
credentials (`awsAccessKeyId`/`awsSecretAccessKey`/`awsSessionToken`) --
which is exactly what `run_k6_test.py` reads directly instead of
re-implementing any of this. Config (API endpoint, Cognito IDs) lives
separately in `~/.dlt/config.json`.

**Commands:**

| Command | What it does |
| --- | --- |
| `dlt configure [--from-file <file>]` | Sets up the API endpoint and Cognito IDs. `--from-file` expects `ApiEndpoint`/`UserPoolId`/`PoolClientId`/`IdentityPoolId`/`UserPoolDomain`/`UserFilesBucket` fields -- exactly the shape `manage_dlt deploy` writes to `aws-exports.json`. Without `--from-file` it prompts for each value individually. |
| `dlt login` / `dlt logout` | See auth modes above. |
| `dlt token status` | Expiry / remaining-minutes table for the cached ID token and AWS credentials. |
| `dlt token output [--type id\|access]` | Prints the raw cached token to stdout. |
| `dlt scenarios list` / `dlt scenarios get <testId>` | List/inspect scenarios that already exist. There's no `dlt scenarios create` -- creating one is API-only, which is why `run_k6_test.py` exists. |
| `dlt scenarios start <testId> [--wait]` | Re-runs an *existing* scenario. **Don't use this after `run_k6_test.py`** -- `POST /scenarios` already started a run on creation, so calling this afterward starts a second, competing run of the same test (see "Running a k6 test" below). Fine to use standalone on a scenario that isn't currently running. |
| `dlt runs latest <testId>` | Most recent run's aggregated stats. |
| `dlt runs download <testId> <runId> --zip` | Downloads result artifacts (bzt log, k6 out/err, kpi.csv) as a zip. |

**Status vocabulary:** a scenario/run moves through `queued` →
`provisioning` → `running` → `cleaning up` → a terminal status. The only
terminal statuses observed are `complete` and `failed` -- notably not
`"success"` despite that being the natural guess (and a string that does
appear elsewhere in the CLI, just not as this field's terminal value).
`run_k6_test.py`'s `wait_for_completion` treats only a small known-terminal
set as done and everything else -- including any status not listed above --
as still in progress, bounded by `--max-wait` as a safety net.

## AWS credentials

`manage_dlt` and `run_k6_test` both use `boto3`, which needs AWS credentials
available before you run them. If your account uses IAM Identity Center
(SSO), which is the common case for gov.bc.ca AWS accounts:

```bash
aws configure sso   # first time only, names a profile
aws sso login --profile <profile-name>
```

Then pass `--aws-profile <profile-name>` to `manage_dlt`/`run_k6_test`, or
`export AWS_PROFILE=<profile-name>` so you don't have to repeat it. If your
account uses static access keys instead, use `aws configure` instead of the
SSO flow above.

## Deploy

`manage_dlt` handles the stack's full lifecycle -- `deploy` and `teardown`
subcommands, sharing `--stack-name`/`--region`/`--aws-profile`.

To deploy the dlt stack:

```bash
uv run --project packages/wps-tools python -m wps_tools.load_testing.manage_dlt deploy \
  --admin-name "Your Name" --admin-email you@example.com \
  --region ca-central-1 --aws-profile <profile-name> \
  --template-bucket <an-s3-bucket-you-can-write-to> \
  --existing-vpc-id vpc-xxxxxxxx --existing-subnet-a subnet-xxxxxxxx --existing-subnet-b subnet-yyyyyyyy
```

To find the existing vps and subnets:
```bash
aws ec2 describe-vpcs --region ca-central-1 --profile <profile-name> \
  --query "Vpcs[].[VpcId,CidrBlock,Tags[?Key=='Name'].Value|[0]]" --output table
aws ec2 describe-subnets --region ca-central-1 --profile <profile-name> --filters Name=vpc-id,Values=<vpc-id> \
  --query "Subnets[].[SubnetId,AvailabilityZone,CidrBlock,Tags[?Key=='Name'].Value|[0]]" --output table
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
<name>`). If you hit that, delete the failed stack (`manage_dlt teardown
--region ca-central-1 --aws-profile <profile-name> --yes` -- a stack that
failed this early won't have any objects in its buckets yet, so
`--empty-buckets` isn't needed) and redeploy with an existing VPC + two
subnets instead:

```bash
uv run --project packages/wps-tools python -m wps_tools.load_testing.manage_dlt deploy \
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
   `aws-exports.json` written by `manage_dlt deploy`:
   ```bash
   curl -sLo /usr/local/bin/dlt \
     https://raw.githubusercontent.com/aws-solutions/distributed-load-testing-on-aws/main/deployment/cli/dlt-cli.mjs
   chmod +x /usr/local/bin/dlt
   dlt configure --from-file aws-exports.json
   dlt login --srp --username admin@example.com
   ```

   **First login will fail** with `Error: A new password is required. Please
   log in via the web console to set your permanent password, then retry.`
   The admin user CloudFormation creates starts in Cognito's
   `FORCE_CHANGE_PASSWORD` state (a temporary password, normally set via the
   web console -- which doesn't exist in this headless setup), and the CLI's
   SRP flow doesn't handle that challenge itself. Set a permanent password
   directly instead of using a console:
   ```bash
   aws cognito-idp admin-set-user-password \
     --user-pool-id <CognitoUserPoolID stack output, or from aws-exports.json's UserPoolId> \
     --username <same value as --admin-name at deploy time -- case-sensitive> \
     --password '<a-strong-password>' \
     --permanent \
     --region ca-central-1 --profile <profile-name>
   ```
   Then retry `dlt login --srp --username <name> --password '<that password>'`
   (or export it as `DLT_PASSWORD` instead of passing `--password`).
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

## Teardown

```bash
uv run --project packages/wps-tools python -m wps_tools.load_testing.manage_dlt teardown \
  --region ca-central-1 --aws-profile <profile-name> --empty-buckets
```

Deletes the stack and waits for `DELETE_COMPLETE`. `--empty-buckets` empties
every S3 bucket the stack created (`ScenariosBucket` -- every uploaded
script and test result -- and, if present, `ConsoleAssetsBucket`) before
deleting; CloudFormation can't delete a non-empty bucket, so this is
required after any real usage, but it's opt-in since it permanently deletes
that data. Without it, a stack with objects in its buckets fails with
`DELETE_FAILED`, and the error message tells you to retry with
`--empty-buckets`.

Prompts for confirmation unless you pass `--yes`. Safe to re-run on a stack
that's already gone -- it checks first and exits cleanly instead of
erroring. Does not touch the S3 bucket used to stage the template
(`--template-bucket`/`--create-template-bucket` in `deploy`) -- that's
outside the stack and meant to be reused across deploys.
