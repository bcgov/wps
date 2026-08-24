# Releases

Three things ship out of this monorepo and can be released independently: **asago**
(the mobile app), **sfms** (the SFMS Daily FWI API), and **wps** (everything else —
backend API and web frontend). This doc covers how versioning, release notes, and
Sentry are wired together for them, and what's deliberately *not* wired up.

## The important caveat: sfms and wps share one Docker image

`backend/packages/wps-sfms` is a real, separate Python package, but the SFMS Daily FWI
API (`sfms_fwi_main.py`) is just a different FastAPI entrypoint baked into the **same**
`wps-api` Docker image as the main API (`main.py`) and the ASA Go backend
(`asa_go_main.py`). They're deployed as separate OpenShift `Deployment` objects
(`oc_deploy.sh` vs `oc_deploy_sfms_fwi_api.sh`), but from identical bits.

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

Run the **Release** workflow (`.github/workflows/release.yml`) via `workflow_dispatch`:

1. Pick `component`: `asago`, `sfms`, or `wps`.
2. Pick `bump`: `patch` (default), `minor`, or `major`.

That's it. The workflow:

1. Looks at the most recent tag for that component's prefix (`asago-*` / `sfms-*` /
   `wps-*`), and bumps the requested part. No prior tag → starts at `0.1.0`.
2. For `sfms`/`wps`, bumps the version in the relevant `pyproject.toml`
   (`wps-sfms` or `wps-api`) and commits that straight to `main` — so the tag ends up
   pointing at a commit whose `pyproject.toml` actually matches. (`asago` has no
   `pyproject.toml` to bump — see "Keeping the mobile build aligned" below instead.)
   Note: nothing reads this version field at build/install time — these are `uv`
   workspace packages referenced by path, not published anywhere — so this is purely
   for humans reading the file, not functional.
3. Tags that commit `<prefix>-<version>`.
4. Generates release notes from `git log <prev-tag>..HEAD -- <paths>`, scoped to that
   component's paths only (see table below) — not GitHub's built-in
   `--generate-notes`, which can't filter by path and would pull in every PR merged to
   main in that window, unrelated components included.
5. Creates a GitHub Release with those notes, a compare link, and a link to the
   matching Sentry release.
6. Creates/finalizes a Sentry release for that same commit SHA and associates its
   commits, in the Sentry project(s) for that component (see below), via
   `getsentry/action-release`.

| component | tag prefix | paths for notes | pyproject.toml bumped | Sentry project(s) |
|---|---|---|---|---|
| `asago` | `asago-*` | `mobile` | — | `asago` |
| `sfms` | `sfms-*` | `backend/packages/wps-sfms` | `wps-sfms` | `api` |
| `wps` | `wps-*` | `backend`, `web` | `wps-api` | `api`, `frontend` |

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
workflows just read it.

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

Because releases are SHA-keyed, most deploys (continuous, on every merge to main) create
bare Sentry releases with no curated commit list — normal Sentry behavior. Only the
commits explicitly cut as `asago-*`/`sfms-*`/`wps-*` releases get the full
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
- **Deploy tracking in Sentry** (`sentry-cli deploys new` / the `deploy:` option). This
  needs to fire at actual deploy time, which means touching `deployment.yml`/
  `production.yml` or the `oc_deploy*.sh` scripts — deliberately out of scope so far to
  avoid touching the production deploy pipeline. Add it if "which environment is this
  release actually running in" becomes something you need Sentry to answer directly.
