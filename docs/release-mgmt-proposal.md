# Proposal: independent release management for asago, sfms, wps, and wps-sfms

Status: draft, implemented on a branch, looking for sign-off before merging.

## Problem

Four things ship from this monorepo — three **deployments** (asago mobile, sfms Daily
FWI API, wps backend+web — each a real running process) and one **package** (wps-sfms,
versioned code with no process of its own, baked into whatever consumes it) — with no
independent versioning, release notes, or Sentry tracing:

- No git tags anywhere in the repo's history.
- `DEPLOY_VERSION="${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"` — a CI run id, same across
  web/api/jobs per push, meaningless outside that run.
- Mobile version: hardcoded `appBuildVersion`, disconnected from the codebase.
- Backend Sentry events carried no release; the sfms CronJobs had no Sentry at all
  (chatops/Slack only).
- No changelog mechanism for any component.

## Goals

- Independent version numbers for all four components.
- Auto-generated, path-scoped release notes (not "everything merged since last time").
- Sentry errors traceable to a real commit, then a tagged release.
- Minimal new machinery — git tags, GitHub Releases, `gh`/`getsentry` actions already
  available — instead of Conventional Commits + release-please/semantic-release, which
  would require changing how the team titles PRs.

## Non-goals

- **Splitting sfms into its own deployable.** Still ships in the same `wps-api` image;
  a real split (new Dockerfile target, BuildConfig/ImageStream) is a bigger project.
  Unrelated to the separate `wps_sfms` package, which the FWI API doesn't import.
- **Changing the deploy pipeline.** `deployment.yml`/`production.yml` keep deploying
  continuously; tags don't gate deploys for wps/sfms.
- **Sentry deploy tracking** (`sentry-cli deploys new`). `oc_deploy_to_production.sh` is
  touched (see #7), but only to tag events with the right environment — not to record
  deploy events.

## Design

- **Tagging**: `asago-<version>`, `sfms-<version>`, `wps-<version>`,
  `wps-sfms-<version>`, each its own semver line from `0.1.0`. Matched via
  `<prefix>-[0-9]*` so `wps-*` can't also catch `wps-sfms-*` tags.
- **One workflow**: `gh workflow run release.yml -f component=wps -f bump=patch`.
  Resolves the next version, tags, writes path-scoped release notes, creates a Sentry
  release on the same commit.
- **Sentry release = commit SHA**, not the tag name — baked in via
  `OPENSHIFT_BUILD_COMMIT` → `SENTRY_RELEASE` at build time. The tag already points at
  that commit, so there's no second name to keep in sync.
- **Version files move with the tag**: `wps`/`wps-sfms` bump their own
  `pyproject.toml`; `asago`/`wps` also bump a `package.json`. `sfms` bumps nothing (its
  code lives in `wps-api`, which `wps` already owns). None of this affects any build —
  `asago`'s real app-store version still comes from the tag, not `package.json`.
- **sfms CronJobs now report to Sentry.** Needed more than `sentry_sdk.init()`: none of
  the 3 CronJob templates had `SENTRY_DSN`/`ENVIRONMENT`, so those were added, threaded
  through the 3 `oc_provision_sfms_*.sh` scripts, and set to `production` in
  `oc_deploy_to_production.sh`. Exception handlers now `capture_exception()` +
  `flush()` before `sys.exit()`, since a short-lived process can outrun the async
  sender.
- **Cutting `asago` ships it.** The last step of `release.yml` dispatches both mobile
  build workflows against the tag — one action, no drift between "tagged" and "built."
- **Deployment vs. package is a docs grouping, not a workflow field.** All four run the
  same steps; there's no `type` output to maintain. Sentry has no generic metadata slot
  to hang it on, and OpenShift already expresses it natively (`Deployment` vs
  `CronJob`), so adding one would just be an unused field.

## Key decisions, flagged for review

1. **asago auto-ships** — no confirmation gate between tagging and a real signed macOS
   build heading toward app-store submission.
2. **sfms and wps version the same image independently** — cutting both the same day
   doesn't mean two builds. Intentional; needs sign-off until/unless sfms splits out.
3. **The version-file bump commits straight to `main`**, bypassing PR review — needs
   `github-actions[bot]` allowed by branch protection.
4. **`SENTRY_AUTH_TOKEN` scope is unverified** beyond web source maps; now also used
   for `api`/`asago`/`frontend` releases.
5. **Sentry's GitHub integration isn't confirmed installed** — needed for
   suspect-commit blame, not just association. OAuth flow in Sentry's UI; can't be
   scripted.
6. **Two pre-existing bugs fixed in passing**: backend never tagged Sentry releases at
   all, and `Dockerfile.web` was missing `ARG SENTRY_AUTH_TOKEN`, so source maps had
   likely never been uploading.
7. **`oc_deploy_to_production.sh` is edited** — narrowly, for the sfms CronJobs'
   `ENVIRONMENT`/`SENTRY_DSN` plumbing — but it's the one change here that touches the
   production deploy script directly.

## What's built

All of the above, implemented on this branch. Reference docs (how it works, not why):
[`docs/RELEASES.md`](./RELEASES.md).

## Open questions

- Is asago auto-ship (#1) acceptable, or should tagging and building stay separate?
- Does branch protection allow the bot commit in #3?
- Who confirms Sentry's GitHub integration (#5) and `SENTRY_AUTH_TOKEN` scope (#4)?
- Is shared-image versioning (#2) fine long-term, or should splitting sfms out be
  scheduled?
- Is the `oc_deploy_to_production.sh` edit (#7) acceptable as scoped?
