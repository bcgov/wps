# asa-go Turbo Integration Design

**Date:** 2026-04-28
**Goal:** Move `asa-go` and the `keycloak` Capacitor plugin into the `frontend/` Turbo monorepo so all shared packages (`@wps/api`, `@wps/types`, `@wps/ui`, `@wps/utils`, `@wps/tsconfig`) can be consumed by asa-go without publishing.

---

## 1. Directory Structure

```
frontend/
  apps/
    wps-web/         (unchanged)
    asa-go/          ← git mv from mobile/asa-go
  packages/
    api/             (unchanged)
    tsconfig/        (unchanged)
    types/           (unchanged)
    ui/              (unchanged)
    utils/           (unchanged)
    keycloak/        ← git mv from mobile/keycloak
mobile/              ← deleted (empty after moves)
```

`frontend/package.json` workspaces already cover `apps/*` and `packages/*` — no glob changes needed.

---

## 2. Package Changes

### Keycloak rename
- `package.json` `name` field: `"keycloak"` → `"@wps/keycloak"`
- asa-go dependency: `"keycloak": "../keycloak"` → `"@wps/keycloak": "workspace:*"`

### Yarn migration
- Remove `"packageManager": "yarn@1.22.22..."` from `asa-go/package.json` and `keycloak/package.json` — both inherit `yarn@4.13.0` from the workspace root
- Delete `mobile/asa-go/yarn.lock`

### Keycloak build scripts
Internal `npm run X` calls in keycloak scripts get replaced with direct tool invocations so they work cleanly under Yarn 4:
- `"build": "npm run clean && npm run docgen && tsc && rollup -c rollup.config.mjs"`
  → `"build": "rimraf ./dist && docgen --api KeycloakPlugin --output-readme README.md --output-json dist/docs.json && tsc && rollup -c rollup.config.mjs"`
- Same treatment for other scripts that chain `npm run X`

### Shared package wiring in asa-go
Add `workspace:*` dependencies to `asa-go/package.json`:
```json
"@wps/api": "workspace:*",
"@wps/types": "workspace:*",
"@wps/ui": "workspace:*",
"@wps/utils": "workspace:*",
"@wps/tsconfig": "workspace:*"
```
Actual import rewrites (replacing local copies with shared package imports) are a follow-up task.

### asa-go script cleanup
Rename `test:ci` → `coverage:ci` to match workspace convention. Refactor `cap:sync:*` scripts to remove the embedded build step (Turbo owns build):
- Before: `"cap:sync:android:dev": "yarn build:dev && APP_ENV=dev yarn cap sync android"`
- After: `"cap:sync:android:dev": "APP_ENV=dev cap sync android"`

---

## 3. Turbo Integration

### turbo.json additions

```json
"@wps/keycloak#build": {
  "dependsOn": [],
  "outputs": ["dist/**"]
},
"cap:sync:dev":         { "dependsOn": ["build"], "cache": false },
"cap:sync:prod":        { "dependsOn": ["build"], "cache": false },
"cap:sync:android:dev": { "dependsOn": ["build"], "cache": false },
"cap:sync:android:prod":{ "dependsOn": ["build"], "cache": false },
"cap:sync:ios:dev":     { "dependsOn": ["build"], "cache": false },
"cap:sync:ios:prod":    { "dependsOn": ["build"], "cache": false }
```

asa-go's `build` uses the existing generic task (`dependsOn: ["^build"]`), which ensures all shared packages build first.

### Usage
```bash
turbo run cap:sync:android:dev --filter=asa-go
# → builds @wps/keycloak, shared packages, asa-go, then runs cap sync android
```

Cap sync tasks are excluded from CI — they are manual or handled in a separate mobile pipeline.

---

## 4. MUI Upgrade (5.x → 6.x)

Affects `@wps/ui` and `wps-web`. asa-go is already on MUI 6.x.

| Package | From | To |
|---|---|---|
| `@mui/material` | `5.15.20` | `^6.0.0` |
| `@mui/icons-material` | `^5.5.1` | `^6.0.0` |
| `@mui/system` | `^5.15.14` | `^6.0.0` |
| `@mui/x-data-grid-pro` | `^6.0.0` | `^8.0.0` |
| `@mui/x-date-pickers` | `^7.29.4` | unchanged (already MUI 6 compatible) |

**Breaking changes to address in code:**
- `<Grid item>` / `<Grid container>` → `<Grid2>` (MUI 6 deprecates the old Grid)
- `@mui/x-data-grid-pro` v8 prop renames (e.g. `experimentalFeatures` removed)
- Theme structure largely unchanged

---

## 5. CI Changes

### integration.yml
asa-go is covered by the existing `yarn install` in `lint-and-test-web` (same workspace). Add a test step:

```yaml
- name: Unit tests (asa-go)
  working-directory: ./frontend
  run: yarn workspace asa-go run coverage:ci
```

Add `frontend/apps/asa-go/**` to any `paths:` filters on the job.

### codecov.yml
Update the `asa_go` flag path:
- `mobile/asa-go` → `frontend/apps/asa-go`

---

## Out of Scope

- Rewriting asa-go imports to use shared packages (follow-up)
- Mobile CI pipeline for `cap:sync` / native builds
- Sharing the `@wps/ui` component library with asa-go beyond wiring (follow-up, after MUI version is aligned)
