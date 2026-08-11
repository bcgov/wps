# Load testing

Tooling for the [Distributed Load Testing on AWS](https://aws.amazon.com/solutions/implementations/distributed-load-testing-on-aws/)
solution (SO0062), deployed headless (backend only, no web console) via the bundled `distributed-load-testing-on-aws-headless.template`. `manage_dlt.py` handles the stack (deploy/teardown); `run_k6_test.py` runs a k6 test against it.

## Quick start

```bash
# 1. AWS credentials (SSO, common for gov.bc.ca accounts)
aws configure sso   # first time only, names a profile
aws sso login --profile <profile-name>

# 2. Find an existing VPC + two subnets, different AZs (your account's SCPs likely
#    block the stack from creating its own VPC -- see Gotchas). Pick an "App" tier
#    subnet if your landing zone has one; not Mgmt/Data/TgwAttach.
aws ec2 describe-vpcs --region ca-central-1 --profile <profile-name> \
  --query "Vpcs[].[VpcId,CidrBlock,Tags[?Key=='Name'].Value|[0]]" --output table
aws ec2 describe-subnets --region ca-central-1 --profile <profile-name> --filters Name=vpc-id,Values=<vpc-id> \
  --query "Subnets[].[SubnetId,AvailabilityZone,CidrBlock,Tags[?Key=='Name'].Value|[0]]" --output table

# 3. Deploy the stack
uv run --project packages/wps-tools python -m wps_tools.load_testing.manage_dlt deploy \
  --admin-name YourName --admin-email you@example.com \
  --region ca-central-1 --aws-profile <profile-name> \
  --create-template-bucket \
  --existing-vpc-id <vpc-id> --existing-subnet-a <subnet-a-id> --existing-subnet-b <subnet-b-id>

# 4. Install the dlt CLI and point it at the stack (aws-exports.json is written by step 3)
curl -sLo /usr/local/bin/dlt \
  https://raw.githubusercontent.com/aws-solutions/distributed-load-testing-on-aws/main/deployment/cli/dlt-cli.mjs
chmod +x /usr/local/bin/dlt
dlt configure --from-file aws-exports.json

# 5. Set a permanent password (the admin user always starts in FORCE_CHANGE_PASSWORD) and log in
aws cognito-idp admin-set-user-password \
  --user-pool-id "$(jq -r .UserPoolId aws-exports.json)" \
  --username YourName --password 'Some-Strong-Password1' --permanent \
  --region ca-central-1 --profile <profile-name>
dlt login --srp --username YourName --password 'Some-Strong-Password1'

# 6. Run a k6 test (paths are relative to backend/, matching --project above)
uv run --project packages/wps-tools python -m wps_tools.load_testing.run_k6_test \
  packages/wps-tools/src/wps_tools/load_testing/k6_scripts/smoke_test.js \
  --stack-name distributed-load-testing --region ca-central-1

# 7. Tear down when done
uv run --project packages/wps-tools python -m wps_tools.load_testing.manage_dlt teardown \
  --region ca-central-1 --aws-profile <profile-name> --empty-buckets
```

Every command supports `--help` for the full flag list. `YourName` and
`Some-Strong-Password1` are placeholders -- use your own; `--admin-name`
becomes the literal Cognito login username, so keep it a single token.

## Gotchas

These aren't obvious from the commands alone -- each cost real debugging time:

- **k6 scripts must make at least one real HTTP call.** Taurus (which wraps
  k6 on the Fargate task) only captures request-level metrics; a script that
  never calls `http.get`/`http.post`/etc produces an empty results file, and
  the run gets reported as failed even though k6 itself ran fine. Use
  `k6_scripts/smoke_test.js` (hits `test.k6.io`, k6's own public test
  endpoint) as a template.
- **Never run `dlt scenarios start` after `run_k6_test.py`.** Creating a
  scenario (`POST /scenarios`) starts the run immediately -- it's not a
  separate step. Starting it again creates a second, competing run that
  races the first for the same ECS service name, and both fail with
  `Creation of service was not idempotent`. `run_k6_test.py` polls for
  completion itself for exactly this reason.
- **`showLive: false` must be sent explicitly, not omitted.** The backend's
  DynamoDB update code references a `:sl` placeholder unconditionally; omit
  the field and creation 500s with `Invalid UpdateExpression... attribute
  value: :sl`, even though the field is optional per the validation schema.
  A real backend bug, already handled in `run_k6_test.py`.
- **The template can't be passed inline.** It's ~300KB, over CloudFormation's
  51,200-byte `TemplateBody` limit, so it's staged in S3 first. Use
  `--create-template-bucket` if you don't already have a bucket to use via
  `--template-bucket`.
- **Teardown fails with `DELETE_FAILED`** if any bucket the stack created
  (e.g. `ScenariosBucket`, holding every uploaded script and result) still
  has objects in it -- CloudFormation won't delete a non-empty bucket. Pass
  `--empty-buckets` to `teardown` (opt-in since it's destructive).

## Debugging

Quick checks:
```bash
dlt token status                  # is your session still valid?
dlt runs latest <testId>          # most recent run's status + stats
```

**Stack deploy failures**: why did CloudFormation roll back:
```bash
aws cloudformation describe-stack-events --stack-name <name> --region <region> --profile <profile> \
  --query "StackEvents[?contains(ResourceStatus, 'FAILED')].[LogicalResourceId,ResourceStatusReason]" --output table
```

**Container output**: what k6/Taurus actually did (log group name has a
CDK-generated suffix, so look it up first):
```bash
aws logs describe-log-groups --region <region> --profile <profile> \
  --query "logGroups[?contains(logGroupName, 'DLTEcs')].logGroupName" --output text

aws logs describe-log-streams --region <region> --profile <profile> \
  --log-group-name "<log group from above>" --order-by LastEventTime --descending --max-items 5 \
  --query "logStreams[].logStreamName" --output text

aws logs get-log-events --region <region> --profile <profile> \
  --log-group-name "<log group>" --log-stream-name "<stream from above>" \
  --query "events[].message" --output text
```

**Lambda errors** (API 500s, orchestration failures), physical function
names have a CDK-generated suffix that changes on redeploy, so find the log
group by a distinguishing substring rather than hardcoding the full name:
```bash
aws logs describe-log-groups --region <region> --profile <profile> \
  --query "logGroups[?contains(logGroupName, '<substring, e.g. APIServices>')].logGroupName" --output text

aws logs filter-log-events --region <region> --profile <profile> \
  --log-group-name "<log group from above>" \
  --start-time $(( $(date +%s) * 1000 - 300000 )) \
  --query "events[].message" --output text
```
Useful substrings: `APIServices` (handles `POST /scenarios`, `GET
/scenarios/{testId}`, etc.), `TaskRunn` (creates the ECS service per
region), `TestClea` (post-run cleanup), `Stabiliz` (waits for the ECS
service to stabilize, or reports why it didn't).

**Orchestration**: did a run actually start once, or race twice:
```bash
SM_ARN=$(aws stepfunctions list-state-machines --region <region> --profile <profile> \
  --query "stateMachines[?contains(name, 'DLTStepFunctionTaskRunner')].stateMachineArn | [0]" --output text)
aws stepfunctions list-executions --region <region> --profile <profile> --state-machine-arn "$SM_ARN" \
  --query "executions[?contains(name, '<testId>')].{name:name,status:status,startDate:startDate}" --output table
```

**ECS**: did Fargate actually launch anything:
```bash
aws ecs list-tasks --region <region> --profile <profile> --cluster <stack-name> --desired-status STOPPED
aws ecs describe-tasks --region <region> --profile <profile> --cluster <stack-name> --tasks <task-arn> \
  --query "tasks[].{stoppedReason:stoppedReason,containers:containers[].reason}"
```

**Who touched a resource** (e.g. what scaled an ECS service to zero):
```bash
aws cloudtrail lookup-events --region <region> --profile <profile> \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=<resource-name> \
  --start-time <ISO8601> --end-time <ISO8601> \
  --query "Events[].{Time:EventTime,User:Username,EventName:EventName}" --output table
```

**Raw result artifacts** (k6 stdout/stderr, Taurus log, metrics CSV):
pull directly from S3 instead of/alongside `dlt runs download`:
```bash
aws s3 cp s3://<ScenariosBucket>/results/<testId>/<runPrefix>/k6-<uuid>-<region>.out - \
  --region <region> --profile <profile>
```

## `dlt` CLI reference

The command-line client shipped with the solution, distributed as a single
bundled Node.js script. Auth via `--srp --username <name>` (password via
`--password` or the `DLT_PASSWORD` env var) or `--iam` (ambient AWS
credentials). Both cache a Cognito ID token + Identity Pool STS credentials
to `~/.dlt/credentials.json`, which `run_k6_test.py` reads directly.

| Command | What it does |
| --- | --- |
| `dlt configure [--from-file <file>]` | Sets up the API endpoint and Cognito IDs from `aws-exports.json` (written by `manage_dlt deploy`), or prompts for each value. |
| `dlt login` / `dlt logout` | See auth modes above. |
| `dlt token status` / `dlt token output [--type id\|access]` | Check or print the cached token. |
| `dlt scenarios list` / `dlt scenarios get <testId>` | List/inspect scenarios. No `create` -- that's API-only, hence `run_k6_test.py`. |
| `dlt scenarios start <testId> [--wait]` | Re-runs an *existing* scenario. **Don't use after `run_k6_test.py`** -- see Gotchas. |
| `dlt runs latest <testId>` | Most recent run's aggregated stats. |
| `dlt runs download <testId> <runId> --zip` | Downloads result artifacts as a zip. |

Status vocabulary: `queued` → `provisioning` → `running` → `cleaning up` →
`complete`/`failed` (terminal). `run_k6_test.py` polls until one of the
known terminal statuses, bounded by `--max-wait`.
