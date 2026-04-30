# asa-go Turbo Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move `asa-go` and the `keycloak` Capacitor plugin into the `frontend/` Turbo monorepo and upgrade MUI to v6 across all shared packages.

**Architecture:** `mobile/asa-go` → `frontend/apps/asa-go` and `mobile/keycloak` → `frontend/packages/keycloak` via `git mv`, preserving history. Both inherit Yarn 4 from the workspace root. All shared `@wps/*` packages are wired as `workspace:*` dependencies in asa-go. MUI is upgraded from 5.x to 6.x in `@wps/ui` and `wps-web` to match asa-go which is already on MUI 6.x.

**Tech Stack:** Yarn 4 (Berry), Turborepo, MUI 6, Capacitor 7, Vite 7, TypeScript 5

**Do not commit any changes** — all tasks end without a commit step.

---

## Files modified

| File | Change |
|---|---|
| `mobile/asa-go/` | git mv → `frontend/apps/asa-go/` |
| `mobile/keycloak/` | git mv → `frontend/packages/keycloak/` |
| `frontend/apps/asa-go/yarn.lock` | deleted |
| `frontend/packages/keycloak/package.json` | rename pkg, remove packageManager, fix scripts |
| `frontend/apps/asa-go/package.json` | keycloak dep, workspace deps, scripts cleanup |
| `frontend/turbo.json` | add keycloak, build:dev/prod, cap:sync tasks |
| `frontend/packages/ui/package.json` | MUI 5→6 version bumps |
| `frontend/apps/wps-web/package.json` | MUI 5→6 version bumps |
| `frontend/apps/wps-web/src/features/fba/components/viz/ElevationFlag.tsx` | Grid import + size prop |
| `frontend/apps/wps-web/src/features/fba/components/viz/ElevationStatus.tsx` | Grid import + size prop |
| `frontend/apps/wps-web/src/features/landingPage/components/ToolCards.tsx` | Grid import + size prop |
| `frontend/apps/wps-web/src/features/moreCast2/components/ForecastDataGrid.tsx` | remove experimentalFeatures |
| `frontend/apps/wps-web/src/features/moreCast2/components/ForecastSummaryDataGrid.tsx` | remove experimentalFeatures |
| `.github/workflows/integration.yml` | add asa-go test step |
| `codecov.yml` | update asa_go path |

---

## Task 1: Move directories

**Files:**
- `mobile/asa-go/` → `frontend/apps/asa-go/`
- `mobile/keycloak/` → `frontend/packages/keycloak/`

- [ ] **Step 1: Move asa-go**

```bash
git -C /Users/cbrady/projects/wps mv mobile/asa-go frontend/apps/asa-go
```

- [ ] **Step 2: Move keycloak**

```bash
git -C /Users/cbrady/projects/wps mv mobile/keycloak frontend/packages/keycloak
```

- [ ] **Step 3: Remove now-empty mobile directory**

```bash
git -C /Users/cbrady/projects/wps rm -r mobile --ignore-unmatch
rmdir /Users/cbrady/projects/wps/mobile 2>/dev/null || true
```

- [ ] **Step 4: Verify**

```bash
ls /Users/cbrady/projects/wps/frontend/apps/asa-go
ls /Users/cbrady/projects/wps/frontend/packages/keycloak
```

Expected: both directories present with their contents.

---

## Task 2: Update keycloak package.json

**Files:**
- Modify: `frontend/packages/keycloak/package.json`

- [ ] **Step 1: Apply all changes**

Replace the `name`, `scripts`, and remove `packageManager`. The full updated `package.json`:

```json
{
  "name": "@wps/keycloak",
  "version": "0.0.1",
  "description": "Capacitor plugin for keycloak auth",
  "main": "dist/plugin.cjs.js",
  "module": "dist/esm/index.js",
  "types": "dist/esm/index.d.ts",
  "unpkg": "dist/plugin.js",
  "files": [
    "android/src/main/",
    "android/build.gradle",
    "dist/",
    "ios/Sources",
    "ios/Tests",
    "Package.swift",
    "Keycloak.podspec"
  ],
  "author": "",
  "license": "Apache-2.0",
  "repository": {
    "type": "git",
    "url": "git+https://github.com/bcgov/wps.git"
  },
  "bugs": {
    "url": "https://github.com/bcgov/wps/issues"
  },
  "keywords": [
    "capacitor",
    "plugin",
    "native"
  ],
  "scripts": {
    "verify": "yarn verify:ios && yarn verify:android && yarn verify:web",
    "verify:ios": "xcodebuild -scheme Keycloak -destination generic/platform=iOS",
    "verify:android": "cd android && ./gradlew clean build test && cd ..",
    "verify:web": "yarn build",
    "lint": "yarn eslint && yarn prettier -- --check && yarn swiftlint -- lint",
    "fmt": "yarn eslint -- --fix && yarn prettier -- --write && yarn swiftlint -- --fix --format",
    "eslint": "eslint . --ext ts",
    "prettier": "prettier \"**/*.{css,html,ts,js,java}\" --plugin=prettier-plugin-java",
    "swiftlint": "node-swiftlint",
    "docgen": "docgen --api KeycloakPlugin --output-readme README.md --output-json dist/docs.json",
    "build": "rimraf ./dist && docgen --api KeycloakPlugin --output-readme README.md --output-json dist/docs.json && tsc && rollup -c rollup.config.mjs",
    "clean": "rimraf ./dist",
    "watch": "tsc --watch",
    "prepublishOnly": "yarn build"
  },
  "devDependencies": {
    "@capacitor/android": "^7.0.0",
    "@capacitor/core": "^7.4.2",
    "@capacitor/docgen": "^0.3.0",
    "@capacitor/ios": "^7.0.0",
    "@ionic/eslint-config": "^0.4.0",
    "@ionic/prettier-config": "^4.0.0",
    "@ionic/swiftlint-config": "^2.0.0",
    "eslint": "^8.57.0",
    "prettier": "^3.4.2",
    "prettier-plugin-java": "^2.6.6",
    "rimraf": "^6.0.1",
    "rollup": "^4.30.1",
    "swiftlint": "^2.0.0",
    "typescript": "~5.9.0"
  },
  "peerDependencies": {
    "@capacitor/core": ">=7.0.0"
  },
  "prettier": "@ionic/prettier-config",
  "swiftlint": "@ionic/swiftlint-config",
  "eslintConfig": {
    "extends": "@ionic/eslint-config/recommended"
  },
  "capacitor": {
    "ios": {
      "src": "ios"
    },
    "android": {
      "src": "android"
    }
  }
}
```

Key changes from original:
- `"name"`: `"keycloak"` → `"@wps/keycloak"`
- `"packageManager"` field removed (inherits from workspace root)
- All `"npm run X"` in scripts changed to `"yarn X"` or inlined
- `"build"` inlines clean+docgen rather than calling `npm run clean && npm run docgen`

---

## Task 3: Update asa-go package.json

**Files:**
- Modify: `frontend/apps/asa-go/package.json`

- [ ] **Step 1: Apply all changes**

The key diffs from the original `asa-go/package.json`:

1. Remove `"packageManager": "yarn@1.22.22..."` field entirely
2. Change `"keycloak": "../keycloak"` → `"@wps/keycloak": "workspace:*"` in `dependencies`
3. Add these workspace dependencies:
   ```json
   "@wps/api": "workspace:*",
   "@wps/types": "workspace:*",
   "@wps/ui": "workspace:*",
   "@wps/utils": "workspace:*"
   ```
4. Add to `devDependencies`:
   ```json
   "@wps/tsconfig": "workspace:*"
   ```
5. Rename script `"test:ci"` → `"coverage:ci"`
6. Refactor `cap:sync:*` scripts to sync-only (remove embedded build steps):
   ```json
   "cap:sync:dev": "APP_ENV=dev cap sync",
   "cap:sync:prod": "APP_ENV=prod cap sync",
   "cap:sync:android:dev": "APP_ENV=dev cap sync android",
   "cap:sync:android:prod": "APP_ENV=prod cap sync android",
   "cap:sync:ios:dev": "APP_ENV=dev cap sync ios",
   "cap:sync:ios:prod": "APP_ENV=prod cap sync ios"
   ```

The full `scripts` block after changes:

```json
"scripts": {
  "dev": "vite",
  "build": "tsc -b && vite build",
  "test": "vitest",
  "coverage:ci": "vitest --coverage",
  "lint": "eslint .",
  "preview": "vite preview",
  "build:dev": "vite build --mode development",
  "build:prod": "vite build --mode production",
  "cap:sync:dev": "APP_ENV=dev cap sync",
  "cap:sync:prod": "APP_ENV=prod cap sync",
  "cap:sync:android:dev": "APP_ENV=dev cap sync android",
  "cap:sync:android:prod": "APP_ENV=prod cap sync android",
  "cap:sync:ios:dev": "APP_ENV=dev cap sync ios",
  "cap:sync:ios:prod": "APP_ENV=prod cap sync ios"
}
```

---

## Task 4: Delete asa-go yarn.lock

**Files:**
- Delete: `frontend/apps/asa-go/yarn.lock`

- [ ] **Step 1: Remove the lockfile**

```bash
git -C /Users/cbrady/projects/wps rm frontend/apps/asa-go/yarn.lock
```

---

## Task 5: Update turbo.json

**Files:**
- Modify: `frontend/turbo.json`

- [ ] **Step 1: Add keycloak, build:dev/prod, and cap:sync tasks**

Add the following entries inside the `"tasks"` object in `frontend/turbo.json`:

```json
"@wps/keycloak#build": {
  "dependsOn": [],
  "outputs": ["dist/**"]
},
"build:dev": {
  "dependsOn": ["^build"],
  "outputs": ["dist/**"]
},
"build:prod": {
  "dependsOn": ["^build"],
  "outputs": ["dist/**"]
},
"cap:sync:dev":         { "dependsOn": ["build:dev"],  "cache": false },
"cap:sync:prod":        { "dependsOn": ["build:prod"], "cache": false },
"cap:sync:android:dev": { "dependsOn": ["build:dev"],  "cache": false },
"cap:sync:android:prod":{ "dependsOn": ["build:prod"], "cache": false },
"cap:sync:ios:dev":     { "dependsOn": ["build:dev"],  "cache": false },
"cap:sync:ios:prod":    { "dependsOn": ["build:prod"], "cache": false }
```

`build:dev`/`build:prod` each wait for upstream workspace deps (`^build`) before running, so shared packages are always built first. The `cap:sync:*` tasks then wait for the appropriate build variant.

---

## Task 6: Bump MUI to v6 in @wps/ui

**Files:**
- Modify: `frontend/packages/ui/package.json`

- [ ] **Step 1: Update MUI package versions in dependencies**

Change in `"dependencies"`:

```json
"@mui/icons-material": "^6.4.0",
"@mui/material": "^6.4.0",
"@mui/system": "^6.4.0",
"@mui/x-data-grid-pro": "^8.9.1",
"@mui/x-date-pickers": "^7.29.4"
```

(`@mui/x-date-pickers` stays at `^7.x` — it's already MUI 6 compatible at that version.)

---

## Task 7: Bump MUI to v6 in wps-web

**Files:**
- Modify: `frontend/apps/wps-web/package.json`

- [ ] **Step 1: Update MUI package versions in dependencies**

Change in `"dependencies"`:

```json
"@mui/icons-material": "^6.4.0",
"@mui/material": "^6.4.0",
"@mui/system": "^6.4.0",
"@mui/x-data-grid-pro": "^8.9.1",
"@mui/x-date-pickers": "^7.29.4"
```

---

## Task 8: Fix Grid in ElevationFlag.tsx

**Files:**
- Modify: `frontend/apps/wps-web/src/features/fba/components/viz/ElevationFlag.tsx`

In MUI 6, `@mui/material/Unstable_Grid2` is now stable as `@mui/material/Grid2`. The `xs` size prop becomes `size`.

- [ ] **Step 1: Update import and size prop**

Change line 3:
```tsx
// before
import Grid from '@mui/material/Unstable_Grid2'
// after
import Grid from '@mui/material/Grid2'
```

Change the `xs={6}` prop on the single `<Grid>` element:
```tsx
// before
<Grid sx={{ alignItems: 'center', display: 'flex', justifyContent: 'flex-end' }} xs={6}>
// after
<Grid sx={{ alignItems: 'center', display: 'flex', justifyContent: 'flex-end' }} size={6}>
```

---

## Task 9: Fix Grid in ElevationStatus.tsx

**Files:**
- Modify: `frontend/apps/wps-web/src/features/fba/components/viz/ElevationStatus.tsx`

- [ ] **Step 1: Update import**

Change line 3:
```tsx
// before
import Grid from '@mui/material/Unstable_Grid2'
// after
import Grid from '@mui/material/Grid2'
```

- [ ] **Step 2: Replace all xs size props**

Replace every `xs={12}` with `size={12}` and every `xs={6}` with `size={6}` in this file. There are 10 occurrences total. The full updated JSX return (for reference):

```tsx
return (
  <Grid container size={12} data-testid="elevation-status">
    <Grid container sx={{ height: theme.spacing(6) }} size={12}>
      <Grid sx={{ paddingLeft: theme.spacing(0.5), paddingRight: theme.spacing(0.5) }} size={6}>
        <Typography sx={{ color: '#003366', fontWeight: 'bold', textAlign: 'left', width: '50%' }}>
          Topographic Position:
        </Typography>
      </Grid>
      <Grid sx={{ display: 'flex', justifyContent: 'flex-end' }} size={6}>
        <Typography sx={{ color: '#003366', fontWeight: 'bold', textAlign: 'right', width: '65%' }}>
          Portion under advisory:
        </Typography>
      </Grid>
    </Grid>
    <Grid size={12}>
      <Box
        sx={{ background: `url(${Mountain})`, backgroundRepeat: 'round', display: 'flex', width: '100%' }}
        data-testid="tpi-mountain"
      >
        <Grid sx={{ paddingLeft: theme.spacing(0.5), paddingRight: theme.spacing(0.5) }} container size={12}>
          <Grid container sx={{ height: theme.spacing(8) }} size={12}>
            <ElevationLabel label={ElevationOption.UPPER} />
            <ElevationFlag id="upper" percent={upper_percent} testId="upper-slope" />
          </Grid>
          <Grid container sx={{ height: theme.spacing(8) }} size={12}>
            <ElevationLabel label={ElevationOption.MID} />
            <ElevationFlag id="mid" percent={mid_percent} testId="mid-slope" />
          </Grid>
          <Grid container sx={{ height: theme.spacing(8) }} size={12}>
            <ElevationLabel label={ElevationOption.BOTTOM} />
            <ElevationFlag id="lower" percent={bottom_percent} testId="valley-bottom" />
          </Grid>
        </Grid>
      </Box>
    </Grid>
  </Grid>
)
```

---

## Task 10: Fix Grid in ToolCards.tsx

**Files:**
- Modify: `frontend/apps/wps-web/src/features/landingPage/components/ToolCards.tsx`

In MUI 6, `@mui/material/Grid` is now the v2 API. The `item` prop is gone; responsive sizes use the `size` prop object.

- [ ] **Step 1: Update import**

Change line 3:
```tsx
// before
import Grid from '@mui/material/Grid'
// after
import Grid from '@mui/material/Grid2'
```

- [ ] **Step 2: Update the Grid item**

```tsx
// before
<Grid style={{ display: 'flex' }} key={item.name} item sm={12} md={6} lg={4}>
// after
<Grid style={{ display: 'flex' }} key={item.name} size={{ sm: 12, md: 6, lg: 4 }}>
```

The outer `<Grid container spacing={2.5}>` requires no change — `container` and `spacing` props are unchanged in MUI 6.

---

## Task 11: Remove experimentalFeatures from DataGrid components

**Files:**
- Modify: `frontend/apps/wps-web/src/features/moreCast2/components/ForecastDataGrid.tsx:104`
- Modify: `frontend/apps/wps-web/src/features/moreCast2/components/ForecastSummaryDataGrid.tsx:84`

In `@mui/x-data-grid-pro` v8, column grouping is stable and no longer needs `experimentalFeatures`.

- [ ] **Step 1: Remove from ForecastDataGrid.tsx**

Delete line 104:
```tsx
// remove this line:
experimentalFeatures={{ columnGrouping: true }}
```

- [ ] **Step 2: Remove from ForecastSummaryDataGrid.tsx**

Delete line 84:
```tsx
// remove this line:
experimentalFeatures={{ columnGrouping: true }}
```

---

## Task 12: Update CI and codecov

**Files:**
- Modify: `.github/workflows/integration.yml`
- Modify: `codecov.yml`

- [ ] **Step 1: Add asa-go test step to integration.yml**

In the `lint-and-test-web` job, after the existing `Unit tests (web)` step, add:

```yaml
      - name: Unit tests (asa-go)
        working-directory: ./frontend
        run: yarn workspace asa-go run coverage:ci
```

- [ ] **Step 2: Update codecov.yml asa_go flag path**

In `codecov.yml`, under the `asa_go` flag, change the path:
```yaml
# before
  asa_go:
    paths:
      - mobile/asa-go
# after
  asa_go:
    paths:
      - frontend/apps/asa-go
```

---

## Task 13: Install dependencies and verify

- [ ] **Step 1: Run yarn install from the frontend workspace root**

```bash
cd /Users/cbrady/projects/wps/frontend && yarn install
```

Expected: resolves all packages including `@wps/keycloak` and `asa-go` as workspace members. No errors.

- [ ] **Step 2: Verify TypeScript compiles across the workspace**

```bash
cd /Users/cbrady/projects/wps/frontend && yarn turbo build --filter=wps-web --filter=asa-go
```

Expected: both apps build without errors. If TypeScript errors appear from the MUI 6 migration not covered by tasks 8–11, fix them before proceeding.

- [ ] **Step 3: Run tests**

```bash
cd /Users/cbrady/projects/wps/frontend && yarn turbo test
```

Expected: all existing tests pass.

- [ ] **Step 4: Verify asa-go is recognized as a workspace member**

```bash
cd /Users/cbrady/projects/wps/frontend && yarn workspaces list
```

Expected: output includes `apps/asa-go` and `packages/keycloak` (as `@wps/keycloak`).
