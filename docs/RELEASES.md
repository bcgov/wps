# Releases

Four independently-releasable things ship from this monorepo, split into two kinds:

- **Deployments** — a real running process with its own "what's live right now"
  question: **asago** (mobile), **sfms** (SFMS Daily FWI API), **wps** (backend API +
  web).
- **Packages** — versioned code with no process of its own; it's baked into whatever
  deployment consumes it: **wps-sfms** (the `wps_sfms` raster-interpolation package,
  consumed by CronJobs that run off the same image as everything else).

All four report to Sentry, and `release.yml` runs the same steps for both kinds
(except the mobile-build dispatch, which is `asago`-only). The deployment/package split
is a documentation grouping, not a field in the workflow — Sentry has no generic
metadata slot to hang it on, and OpenShift already expresses it natively via resource
kind (`Deployment` vs `CronJob`), so there was nothing for the workflow to feed.

## sfms and wps share one Docker image

`sfms_fwi_main.py` (→ `app/routers/sfms_fwi.py`) is a separate FastAPI entrypoint baked
into the same `wps-api` image as `main.py`/`asa_go_main.py`, deployed as its own
`Deployment` (`oc_deploy_sfms_fwi_api.sh`) but identical bits. Cutting `sfms-*` and
`wps-*` tags gives independent versions/changelogs/Sentry tracking, not two artifacts —
there's only one. A real split (own Dockerfile target, BuildConfig/ImageStream) is a
bigger project, not done here.

This is **not** the same as the `wps_sfms` package (`backend/packages/wps-sfms`) — that
backs a different set of CronJobs (`sfms_run_pipeline.py`, `sfms_daily_actuals.py`,
`sfms_daily_forecasts.py`) that the FWI API never imports. FWI API code:
`sfms_fwi_main.py`, `app/routers/sfms_fwi.py`, `app/sfms/`, `wps_shared/sfms/`.

Mobile already builds/deploys independently via its own workflows
(`asa_go_android_build.yml`, `asa_go_ios_build_deploy.yml`).

## Cutting a release

```bash
gh workflow run release.yml -f component=wps -f bump=patch
```

`component`: `asago` / `sfms` / `wps` / `wps-sfms`. `bump`: `patch` (default) / `minor`
/ `major`.

1. Resolves the next version from the last `<prefix>-[0-9]*` tag (`[0-9]*`, not a bare
   `*` — otherwise `wps-*` would also match `wps-sfms-*`). No tag → `0.1.0`.
2. Bumps that component's version file(s) — see table — and commits to `main`.
3. Tags `<prefix>-<version>` on that commit.
4. Writes release notes from `git log <prev-tag>..HEAD -- <paths>`, scoped to that
   component's paths — not GitHub's `--generate-notes`, which can't filter by path.
5. Creates/finalizes a Sentry release for that commit and associates its commits, in
   the project(s) below (skippable per-component if one has no Sentry project).
6. `asago` only: dispatches both mobile build workflows against the tag.

**Deployments**

| component | tag prefix | paths for notes | pyproject.toml | package.json | Sentry project(s) |
|---|---|---|---|---|---|
| `asago` | `asago-*` | `mobile` | — | `mobile/asa-go/package.json` | `asago` |
| `sfms` | `sfms-*` | `sfms_fwi_main.py`, `app/routers/sfms_fwi.py`, `app/sfms/`, `wps_shared/sfms/` (under `backend/packages/...`) | — | — | `api` |
| `wps` | `wps-*` | `backend`, `web` | `wps-api` | `web/apps/wps-web/package.json` | `api`, `frontend` |

**Packages**

| component | tag prefix | paths for notes | pyproject.toml | package.json | Sentry project(s) |
|---|---|---|---|---|---|
| `wps-sfms` | `wps-sfms-*` | `backend/packages/wps-sfms` | `wps-sfms` | — | `api` |

None of the version-file bumps affect any build — the Python packages are `uv`
workspace packages, not published, and `asago`'s real app-store version comes from the
tag, not its `package.json`.

## Mobile build reads the tag

`asa_go_android_build.yml`/`asa_go_ios_build_deploy.yml` used to set the app-store
version from a hardcoded `appBuildVersion`, disconnected from any tag. Both now resolve
`VERSION_NAME`/marketing version from the latest `asago-*` tag and fail loudly
(`No asago-* tag found`) if none exists.

Cutting an `asago` release ships it: `release.yml`'s last step dispatches both build
workflows against the tag right after pushing it. No separate step to forget — but also
no confirmation gate before a real macOS build with production signing certs runs.

## Sentry: release = commit SHA, not the tag

The SHA is the only thing a process knows about itself at error time, and the tag
already points at a commit — so the two are connected for free, no second name to keep
in sync.

- **Backend** (3 FastAPI entrypoints + the 3 sfms CronJobs): `release=<sha>` via
  `SENTRY_RELEASE`, sourced from `Dockerfile`'s `ARG OPENSHIFT_BUILD_COMMIT` (OpenShift's
  build strategy auto-populates it). Backend had zero release tagging before this; the
  CronJobs had zero Sentry at all (chatops/Slack only) — they now init, and
  `capture_exception()` + `flush()` before `sys.exit()`, since a short-lived process can
  outrun Sentry's async sender.
- **Web**: same `OPENSHIFT_BUILD_COMMIT` → `SENTRY_RELEASE`, fed to `sentryVitePlugin`,
  commit association pinned explicitly to `bcgov/wps@<sha>` (no `.git` in that build
  context for auto-detection). Found along the way: `Dockerfile.web` was missing
  `ARG SENTRY_AUTH_TOKEN`, so `build.web.bc.yaml`'s token never reached the build —
  source maps were likely never uploading.
- **Mobile**: already auto-detects from `.git` (real checkout on the runner) — just
  needed `fetch-depth: 0` instead of the default shallow clone.

Wiring the CronJobs took more than three lines of Python: none of the 3 CronJob
templates had `SENTRY_DSN`/`ENVIRONMENT`, so those were added (new `ENVIRONMENT`
parameter, default `development`), threaded through the 3 `oc_provision_sfms_*.sh`
scripts, and set to `production` explicitly in `oc_deploy_to_production.sh` — the one
place this touches the prod deploy script.

Most deploys (continuous, every merge to main) still create bare, uncurated Sentry
releases — normal. Only tagged releases get full commit association.

### Not wired up

- **GitHub SCM integration** — needed for suspect-commit author/assignee, not just
  association. OAuth flow in Sentry's UI (org Settings → Integrations); can't be
  scripted.
- **`SENTRY_AUTH_TOKEN` scope** — was only ever exercised for web source maps;
  `release.yml` now also uses it for `api`/`asago`/`frontend` releases. Verify it's
  org-scoped, not project-scoped.
- **Sentry deploy tracking** (`sentry-cli deploys new`) — separate from the
  `ENVIRONMENT` tagging above (that's event tagging, this would be "a deploy happened").
  Still not implemented.
