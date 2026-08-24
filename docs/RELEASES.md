# Releases

Four things can be released independently out of this monorepo: **asago** (the mobile
app), **sfms** (the SFMS Daily FWI API), **wps** (everything else — backend API and web
frontend), and **wps-sfms** (the `wps_sfms` raster-interpolation package). All four run
in production and all four report to Sentry — `wps-sfms` deploys as scheduled CronJobs
(`sfms_daily_actuals`, `sfms_daily_forecasts`, `sfms_calculations`) off the same
`wps-api` image, rather than a long-running service, but those job processes now call
`sentry_sdk.init()` too. This doc covers how versioning, release notes, and Sentry are
wired together for them, and what's deliberately *not* wired up.

## The important caveat: sfms and wps share one Docker image

The SFMS Daily FWI API (`sfms_fwi_main.py` → `app/routers/sfms_fwi.py`) is just a
different FastAPI entrypoint baked into the **same** `wps-api` Docker image as the main
API (`main.py`) and the ASA Go backend (`asa_go_main.py`). They're deployed as separate
OpenShift `Deployment` objects (`oc_deploy.sh` vs `oc_deploy_sfms_fwi_api.sh`), but from
identical bits.

Note this is **not** the same thing as `backend/packages/wps-sfms` (the `wps_sfms`
Python package, released independently as the `wps-sfms` component) — that's a
raster-interpolation library used by a completely different set of CronJobs
(`app/jobs/sfms_run_pipeline.py`, `sfms_daily_actuals.py`, `sfms_daily_forecasts.py`),
and the FWI API doesn't import it at all. The FWI API's own code is `sfms_fwi_main.py`,
`app/routers/sfms_fwi.py`, `app/sfms/` (shared with one other cronjob,
`sfms_calculations.py`), and `wps_shared/sfms/`.

So today, cutting an `sfms-*` tag and a `wps-*` tag doesn't build or deploy two
different artifacts — it can't, there's only one image. What it *does* give you is
independent version numbers, changelogs, and Sentry release tracking for each, scoped to
the paths that actually belong to each product. If sfms ever needs to genuinely diverge
from the api (a real bug fix that only ships to one), that requires splitting it into
its own build/image/BuildConfig — a bigger project, not done here.

Mobile (`mobile/asa-go`) already builds and deploys completely independently — its own
Capacitor app, its own `workflow_dispatch`-triggered build workflows
(`asa_go_android_build.yml`, `asa_go_ios_build_deploy.yml`).

## Cutting a release

Run the **Release** workflow (`.github/workflows/release.yml`) via `workflow_dispatch`,
either from the Actions tab or with `gh`:

```bash
gh workflow run release.yml -f component=wps -f bump=patch
```

- `component`: `asago`, `sfms`, `wps`, or `wps-sfms`.
- `bump`: `patch` (default, so it's omittable), `minor`, or `major`.

That's it. The workflow:

1. Looks at the most recent tag for that component's prefix (`asago-[0-9]*` /
   `sfms-[0-9]*` / `wps-[0-9]*` / `wps-sfms-[0-9]*` — the `[0-9]*` matters: a bare `*`
   on `wps-*` would also match `wps-sfms-*` tags), and bumps the requested part. No
   prior tag → starts at `0.1.0`.
2. Bumps whichever version file(s) that component owns (`pyproject.toml`,
   `package.json`, or both — see table below), committing each straight to `main`
   before tagging so the tag ends up pointing at a commit whose version file(s)
   actually match. `sfms` owns neither: its code lives inside the `wps-api` package,
   whose files `wps` already owns bumping. Note: none of these version fields are read
   at build/install time — the Python packages are `uv` workspace packages referenced
   by path, and `asago`'s real app-store version comes from the tag directly, not from
   `mobile/asa-go/package.json` (see "Keeping the mobile build aligned" below) — so this
   is purely for humans reading the file, not functional.
3. Tags that commit `<prefix>-<version>`.
4. Generates release notes from `git log <prev-tag>..HEAD -- <paths>`, scoped to that
   component's paths only (see table below) — not GitHub's built-in
   `--generate-notes`, which can't filter by path and would pull in every PR merged to
   main in that window, unrelated components included.
5. Creates a GitHub Release with those notes, a compare link, and (if the component has
   one) a link to the matching Sentry release.
6. Creates/finalizes a Sentry release for that same commit SHA and associates its
   commits, in the Sentry project(s) for that component (see below), via
   `getsentry/action-release`. (This step is skippable — via an `if` on whether the
   component has a Sentry project at all — for a future component that might not; all
   four current ones do.)

| component | tag prefix | paths for notes | pyproject.toml bumped | package.json bumped | Sentry project(s) |
|---|---|---|---|---|---|
| `asago` | `asago-*` | `mobile` | — | `mobile/asa-go/package.json` | `asago` |
| `sfms` | `sfms-*` | `sfms_fwi_main.py`, `app/routers/sfms_fwi.py`, `app/sfms/`, `wps_shared/sfms/` (all under `backend/packages/...`) | — | — | `api` |
| `wps` | `wps-*` | `backend`, `web` | `wps-api` | `web/apps/wps-web/package.json` | `api`, `frontend` |
| `wps-sfms` | `wps-sfms-*` | `backend/packages/wps-sfms` | `wps-sfms` | — | `api` |

Nothing about the actual build/deploy pipeline changes when you do this —
`deployment.yml`/`production.yml` keep deploying continuously on every push/promotion,
exactly as before. Tags are a documentation and traceability layer on top, not a deploy
trigger. If you want a tag push to actually gate a deploy, that's a deliberate follow-up,
not something this workflow does.

## Keeping the mobile build aligned

`asa_go_android_build.yml` and `asa_go_ios_build_deploy.yml` are the real build/publish
workflows for the mobile app — they produce the signed AAB/IPA. They used to set the
app-store version number from a hardcoded `appBuildVersion` env var, hand-edited in each
workflow file, completely disconnected from any tag. That's a drift trap: nothing
stopped the two files from disagreeing with each other, or with whatever `release.yml`
last tagged.

Both workflows now derive `VERSION_NAME` (Android) / marketing version (iOS) from the
latest `asago-*` tag instead:

```bash
TAG=$(git tag --list "asago-*" --sort=-v:refname | head -n1)
```

There's exactly one place a mobile version number is decided — the tag — and both build
workflows just read it. `release.yml` also bumps `mobile/asa-go/package.json`'s
`version` field to match (step 2 above), but that's bookkeeping only — nothing reads it
for the actual app-store version, the tag is still the source of truth.

Cutting an `asago` release *is* shipping it: the last step of `release.yml`, once the
tag is pushed, runs `gh workflow run asa_go_android_build.yml --ref "${TAG}"` and the
same for iOS — targeting the exact commit just tagged. There's no separate step to
remember, and no window where a tag exists but was never actually built. This does mean
running `component: asago` on `release.yml` kicks off a real macOS-runner build with
production signing certs and pushes toward app-store submission — there's no extra
confirmation gate beyond picking `asago` and hitting run. Running either build workflow
directly (without going through `release.yml` first) still works and still fails loudly
(`No asago-* tag found`) if no tag exists yet, for a manual rebuild off an existing tag.

## Tying a release to what's actually deployed, via Sentry

Sentry releases are keyed on **the git commit SHA**, not the human tag
(`asago-1.2.0`, etc.) — because that's the only thing the running process can know
about itself at the moment it emits an error. The tag is just a pointer to a commit, and
that commit's SHA is the Sentry release, so the two are connected for free: no second
naming scheme to keep in sync, no risk of the tag and the "real" release drifting apart.

**Backend** (`main.py`, `asa_go_main.py`, `sfms_fwi_main.py`) tags every event with
`release=<commit SHA>`, sourced from `Dockerfile`'s `SENTRY_RELEASE` env var, which in
turn comes from `ARG OPENSHIFT_BUILD_COMMIT` — OpenShift's Docker build strategy
auto-populates that ARG with the commit it actually built, no template changes needed to
get it. (It didn't tag releases at all before this.)

**Web** (`web/apps/wps-web/vite.config.ts`) does the same via `Dockerfile.web`'s
identical `OPENSHIFT_BUILD_COMMIT` → `SENTRY_RELEASE` wiring, fed into the
`sentryVitePlugin`'s `release.name`. Commit association is pinned explicitly to
`bcgov/wps@<sha>` rather than relying on the plugin's default git-based auto-detection,
because there's no `.git` in that build context (`Dockerfile.web` only `COPY`s source
files, not history). Along the way, `Dockerfile.web` was also missing
`ARG SENTRY_AUTH_TOKEN` — `build.web.bc.yaml` was passing the token in, but no stage
declared the ARG to receive it, so source map upload had likely been silently failing.

**Mobile** already auto-detects its release from `.git` (its build workflows run
directly on the GitHub Actions runner with a real checkout, unlike the OpenShift Docker
builds above) — it just needed `fetch-depth: 0` instead of the default shallow clone, so
commit association has history to walk.

**The sfms CronJobs** (`app/jobs/sfms_daily_actuals.py`, `sfms_daily_forecasts.py`,
`sfms_calculations.py` — the ones that actually import `wps_sfms`) previously called
`sentry_sdk.init()` nowhere at all: a failure was only visible via
`send_chatops_notification`'s Slack message, with no grouping, no stack trace, no
release. They now init the same way as the FastAPI entrypoints
(`if ENVIRONMENT == "production": sentry_sdk.init(dsn=..., release=SENTRY_RELEASE, ...)`)
and, in their existing `except Exception` handlers, call `sentry_sdk.capture_exception()`
followed by `sentry_sdk.flush()` before `sys.exit()` — a short-lived script that exits
right after an exception can outrun Sentry's background sender, so the event has to be
flushed explicitly rather than left to the SDK's normal async send.

This needed real plumbing, not just the three Python files: none of the three CronJob
templates (`openshift/templates/sfms_daily_actuals.cronjob.yaml`,
`sfms_daily_forecasts.cronjob.yaml`, `sfms_calculations.cronjob.yaml`) had `SENTRY_DSN`
or `ENVIRONMENT` at all — those had to be added (a new `ENVIRONMENT` parameter,
defaulting to `development`; a `SENTRY_DSN` env sourced from the same
`${GLOBAL_NAME}`/`sentry-dsn` secret the Deployments use). The three
`oc_provision_sfms_*_cronjob.sh` scripts now forward `ENVIRONMENT` as an optional `-p`,
and `oc_deploy_to_production.sh` passes `ENVIRONMENT="production"` explicitly when
provisioning these three, matching the pattern already used there for
`oc_deploy.sh`/`oc_deploy_asa_go_api.sh`/`oc_deploy_sfms_fwi_api.sh`. Dev/PR cronjob runs
need no changes — they pick up the template's `development` default.

Because releases are SHA-keyed, most deploys (continuous, on every merge to main) create
bare Sentry releases with no curated commit list — normal Sentry behavior. Only the
commits explicitly cut as `asago-*`/`sfms-*`/`wps-*`/`wps-sfms-*` releases get the full
commit-association treatment from step 6 above.

### What isn't wired up

- **The GitHub SCM integration.** Commit *association* works without it, but suspect
  commit author/assignee resolution needs Sentry's GitHub integration installed
  (org Settings → Integrations). That's an OAuth flow in the Sentry UI — can't be done
  from a workflow file.
- **`SENTRY_AUTH_TOKEN` scope.** The existing secret was only ever exercised for web
  source map upload. `release.yml` now also uses it to create releases in the `api` and
  `asago` projects — if the token is scoped to just one project, widen it in Sentry
  (Settings → Auth Tokens) and update the GitHub secret.
- **Deploy tracking in Sentry** (`sentry-cli deploys new` / the `deploy:` option) is
  still not wired up, even though `oc_deploy_to_production.sh` was touched to plumb
  `ENVIRONMENT`/`SENTRY_DSN` through to the sfms CronJobs. That's tagging events with the
  right environment, not recording "a deploy happened" as its own Sentry event — the
  latter would need an explicit `sentry-cli deploys new` call at deploy time, deliberately
  left out. Add it if "which environment is this release actually running in" becomes
  something you need Sentry to answer directly.
