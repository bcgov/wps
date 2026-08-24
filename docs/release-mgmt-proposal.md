# Proposal: independent release management for asago, sfms, wps, and wps-sfms

Status: draft, implemented on a branch, looking for sign-off before merging.

## Problem

This monorepo ships four things worth versioning independently: the mobile app (asago),
the SFMS Daily FWI API (sfms), everything else (wps: backend API + web), and the
raster-interpolation package (wps-sfms). The first three run as long-lived services;
wps-sfms runs as scheduled CronJobs off the same image instead. None of them had a way
to version, release-note, or trace independently, and wps-sfms's CronJobs additionally
had no error tracking at all beyond a Slack message:

- No git tags at all, anywhere in the repo's history.
- Deploys were identified by `DEPLOY_VERSION="${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"` —
  a CI run id, same value across web/api/jobs in a given push, meaningless outside that
  run.
- Mobile app-store version numbers lived in a hand-edited `appBuildVersion` string in
  each build workflow, with no link to what was actually in the codebase at that point.
- Backend Sentry events carried no release tag at all. Web/mobile events did, but via an
  unverified default (see below) — nobody could reliably answer "what's the suspect
  commit for this error" for any of the three.
- No changelog/release-notes mechanism existed for any component.

## Goals

- Independent, human-readable version numbers for asago, sfms, wps, and wps-sfms.
- Auto-generated release notes per component, scoped to the paths that actually belong
  to it (not "everything merged to main since last time," which would be mostly noise
  for the other components).
- Sentry errors traceable back to a real commit and, from there, to a tagged release.
- Minimal new machinery: reuse git tags, GitHub Releases, and `gh`/`getsentry` actions
  already in this ecosystem, rather than adopting Conventional Commits + a
  release-automation bot (release-please/semantic-release) that would require changing
  how the team writes PR titles.

## Non-goals (explicitly out of scope)

- **Splitting sfms into its own deployable.** `sfms_fwi_main.py` still ships inside the
  same `wps-api` Docker image as the main API — same bits, independently tagged. Actually
  decoupling the artifact is a bigger project (new Dockerfile target, new
  BuildConfig/ImageStream, repointing `sfms_fwi_api.yaml`) and isn't part of this.
  (Note: this is specifically about the SFMS Daily FWI API service — `sfms_fwi_main.py`
  / `app/routers/sfms_fwi.py`. It's unrelated to the separate `wps_sfms` Python package,
  which backs a different set of raster-interpolation CronJobs and isn't imported by the
  FWI API at all. `sfms`'s release scope tracks the former, not the latter.)
- **Changing the deploy pipeline.** `deployment.yml`/`production.yml` keep deploying
  continuously on every push/promotion, exactly as today. Tags are a documentation and
  traceability layer on top, not a deploy gate, for wps/sfms.
- **Sentry deploy tracking** (`sentry-cli deploys new` / the `deploy:` env option) —
  recording "this release went to production" as its own Sentry event. Left for later.
  Note this proposal does touch `oc_deploy_to_production.sh`, but only to plumb
  `ENVIRONMENT`/`SENTRY_DSN` through to the sfms CronJobs (see Key decisions #7) — that's
  event *tagging*, not deploy tracking, and is a materially smaller change than wiring up
  `deploys new`.

## Proposed design

**Tagging**: four independent prefixes — `asago-<version>`, `sfms-<version>`,
`wps-<version>`, `wps-sfms-<version>` — each its own semver line, starting at `0.1.0`.
(Tag matching uses `<prefix>-[0-9]*`, not a bare `*` — otherwise `wps-*` would also
match `wps-sfms-*` tags.)

**One workflow to cut a release** (`.github/workflows/release.yml`,
`workflow_dispatch`): pick a `component` and a `bump` (patch/minor/major), e.g.
`gh workflow run release.yml -f component=wps -f bump=patch`. It resolves the next
version from the last matching tag, tags the commit, writes a GitHub Release with notes
generated from `git log <prev-tag>..HEAD` scoped to that component's paths only, and
creates a Sentry release tied to the same commit.

**Sentry releases are keyed on the commit SHA, not the tag name.** The SHA is the only
thing a running process can know about itself, so backend and web now bake
`OPENSHIFT_BUILD_COMMIT` (an ARG OpenShift's build strategy auto-populates) into
`SENTRY_RELEASE` at image build time. The tag is just a pointer at a commit, so "the
Sentry release for `wps-1.4.0`" is just "the SHA that tag points to" — no second naming
scheme to keep in sync, no risk of drift between the two.

**Version files move with the tag.** `wps` and `wps-sfms` bump their own
`pyproject.toml` (`wps-api` or `wps-sfms`); `asago` and `wps` also bump a `package.json`
(`mobile/asa-go` or `web/apps/wps-web`) — each commits straight to `main` before tagging,
so the tag lands on a commit whose version file(s) agree with it. `sfms` bumps
nothing — its code lives inside the `wps-api` package too (see the correction below), so
there's no separate file for it to own. None of this affects any build: the Python
files are `uv` workspace packages referenced by path, not published, and `asago`'s real
app-store version still comes from the tag directly, not from its `package.json` — see
"Mobile version numbers" below. Purely for humans reading the file.

**The sfms CronJobs (`sfms_daily_actuals`, `sfms_daily_forecasts`, `sfms_calculations`)
now report to Sentry too**, so wps-sfms gets the same commit-association treatment as
the other three components. This needed more than adding `sentry_sdk.init()` to three
Python files: none of the three CronJob templates carried `SENTRY_DSN` or `ENVIRONMENT`
at all, so those had to be added to the templates, threaded through the
`oc_provision_sfms_*_cronjob.sh` scripts, and set to `"production"` explicitly in
`oc_deploy_to_production.sh` — mirroring the existing pattern for the API/ASA-Go/SFMS-FWI
Deployments. Short-lived scripts also need an explicit `sentry_sdk.flush()` before
`sys.exit()` in their exception handlers, since a process that exits immediately after
an error can outrun the SDK's normal async send.

**Mobile version numbers now come from the tag, not a hand-edited string.**
`asa_go_android_build.yml`/`asa_go_ios_build_deploy.yml` read `VERSION_NAME` from the
latest `asago-*` tag and fail loudly if none exists, instead of trusting a separately
maintained `appBuildVersion`.

**Cutting an `asago` release ships it.** `release.yml`'s last step, once the tag is
pushed, dispatches both mobile build workflows against that exact commit
(`gh workflow run ... --ref "${TAG}"`). One action, not two steps that can drift apart.

## Key decisions and tradeoffs, flagged for review

1. **asago auto-ships to the app stores with no separate confirmation.** Picking
   `component: asago` on `release.yml` and hitting run kicks off a real macOS-runner
   build with production signing certs, heading toward store submission — there's no
   "are you sure" step between tagging and shipping. Alternative: keep tag-cut and
   build-dispatch as two manual steps if that gate is wanted back.
2. **sfms and wps get independent version numbers for the same underlying image.**
   Cutting `sfms-1.2.0` and `wps-1.2.0` on the same day doesn't mean two different
   builds — it's the same api image, tagged twice for two audiences. This is
   intentional (see Non-goals) but worth the team explicitly agreeing it's acceptable
   until/unless sfms gets its own image.
3. **The pyproject.toml bump commits directly to `main`** from the release workflow,
   bypassing PR review for that one-line version bump. Fine if branch protection allows
   it for `github-actions[bot]`; blocks the whole release if it doesn't.
4. **`SENTRY_AUTH_TOKEN` scope is unverified.** It's only ever been exercised for web
   source-map upload; `release.yml` now also uses it to create releases in the `api` and
   `asago` Sentry projects. If it's project-scoped rather than org-scoped, those calls
   will fail silently-ish (the action errors, but easy to miss in a release run nobody's
   watching closely).
5. **Sentry's GitHub integration isn't confirmed installed.** Commit *association* works
   without it, but suspect-commit author/assignee resolution doesn't. That's an OAuth
   flow in the Sentry UI (org Settings → Integrations) that needs a human with org admin
   to click through — can't be done from a workflow file.
6. **Found and fixed two pre-existing bugs along the way**, worth calling out explicitly
   since they predate this proposal and are easy to mistake for new behavior: backend
   never tagged Sentry events with a release at all, and `Dockerfile.web` never declared
   `ARG SENTRY_AUTH_TOKEN`, so the token `build.web.bc.yaml` was passing in never reached
   the build — source map upload had likely been silently no-op-ing.
7. **`oc_deploy_to_production.sh` was edited** to pass `ENVIRONMENT="production"` to the
   three sfms CronJob provisioning calls, alongside three CronJob templates gaining a new
   `ENVIRONMENT` parameter (default `development`, so dev/PR runs need no changes) and a
   `SENTRY_DSN` env var. This is the one change in this proposal that touches the
   production deploy script directly, even though narrowly (env var plumbing, not new
   deploy logic) — worth a second pair of eyes given the file it's in.

## What's already built

Everything described above is implemented on this branch:
`.github/workflows/release.yml` (new), `asa_go_android_build.yml`/
`asa_go_ios_build_deploy.yml` (version + fetch-depth changes), `Dockerfile`/
`Dockerfile.web` (`SENTRY_RELEASE`/`SENTRY_AUTH_TOKEN` ARGs), the three backend API
`sentry_sdk.init()` call sites, `web/apps/wps-web/vite.config.ts`, the three sfms
CronJob Python files (`sentry_sdk.init()` + capture/flush on failure), their three
OpenShift CronJob templates (`ENVIRONMENT`/`SENTRY_DSN`), their three
`oc_provision_sfms_*_cronjob.sh` scripts, and `oc_deploy_to_production.sh`. Full
reference docs, written as "how it works" rather than "here's why," live in
[`docs/RELEASES.md`](./RELEASES.md) once this is agreed on.

## Open questions for reviewers

- Is the asago auto-ship-on-tag behavior (#1) acceptable, or should tagging and building
  stay separate?
- Does branch protection on `main` allow `github-actions[bot]` to push the
  pyproject.toml bump commit (#3)?
- Who has org admin on Sentry to confirm/install the GitHub integration (#5) and check
  `SENTRY_AUTH_TOKEN`'s scope (#4)?
- Is the shared-image versioning for sfms/wps (#2) acceptable long-term, or should
  splitting sfms into its own image be scheduled as follow-up work?
- Is the `oc_deploy_to_production.sh` edit (#7) acceptable as scoped (env var plumbing
  only), or should the sfms CronJobs' Sentry env vars be wired some other way that avoids
  touching that file at all?
