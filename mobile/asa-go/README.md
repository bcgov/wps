# ASA Go

Capacitor app using react/vite. Test

For iOS & Android Firebase push notification setup details, see [Notifications.md](Notifications.md).

## Building

The keycloak plugin must be built before installing asa-go dependencies, as asa-go resolves it as a local path dependency.

```bash
# 1. Build the keycloak plugin
cd mobile/keycloak
yarn install
yarn build

# 2. Install and build asa-go
cd mobile/asa-go
yarn install
yarn build
```

## Setup live reload

1. Install ionic CLI and native run for live reload with: `npm install -g @ionic/cli native-run`

### Building/Running iOS

1. Make sure xcode is installed with `xcode-select --install`
2. Go to `mobile/asa-go`
3. Run `APP_ENV=dev yarn cap:sync:ios:dev` or `APP_ENV=prod yarn cap:sync:ios:prod`
4. List available devices/simulators with `ionic capacitor run ios --list`
5. Build and run with live reload:
   - `APP_ENV=dev ionic capacitor run ios -l --external`
   - `APP_ENV=prod ionic capacitor run ios -l --external`

`APP_ENV=dev` selects the `ASA Go Dev` iOS scheme and `APP_ENV=prod` selects `ASA Go`.

### Building/Running Android

1. Install Android Studio (Jetbrains Toolbox recommended: <https://www.jetbrains.com/toolbox-app/>)
2. Find where the Android SDK is installed
   - With Jetbrains Toolbox it should be `/Users/<user>/Library/Android/sdk/`
   - Set `$ANDROID_HOME` to the path of the Android SDK
3. Go to `mobile/asa-go`
4. Run `APP_ENV=dev yarn cap:sync:android:dev` or `APP_ENV=prod yarn cap:sync:android:prod`
5. If you are building from Android Studio, open the [`android`](/Users/breedwar/projects/other/wps/mobile/asa-go/android) project and choose the matching build variant in the `Build Variants` tool window:
   - `devDebug` or `devRelease` after a dev sync
   - `prodDebug` or `prodRelease` after a prod sync
6. Build and run with live reload: `APP_ENV=dev ionic capacitor run android -l --external` or `APP_ENV=prod ionic capacitor run android -l --external`

If the selected Android Studio build variant does not match the last `cap sync` flavor, you can end up with mismatched native config and web assets.

To build a debug APK directly:

```bash
cd mobile/asa-go/android
./gradlew assembleDevDebug
./gradlew assembleProdDebug
```

#### Running on a physical Android device against your local API

Get your local machine IP: `ipconfig getifaddr en0`

1. Set `VITE_API_BASE_URL=http://{local_machine_ip}:8080/api` in `.env.development`
2. Set `ORIGINS="http://localhost/ http://{local_machine_ip}:8080"` in `backend/packages/wps-api/src/app/.env`
3. Add `server: { androidScheme: "http" }` to the root of the config in `capacitor.config.ts`
4. Add `<domain includeSubdomains="true">{local_machine_ip}</domain>` to the `domain-config` list in `network_security_config.xml`

### Asset Generation

The `@capacitor/assets` npm package was used to generate icon and splash screen assets for Android with the following command: `npx capacitor-assets generate --android`

### Offline Basemap

- The pmtiles file for the offline basemap was extracted using the [pmtiles cli extract command](https://docs.protomaps.com/pmtiles/cli#extract) using a `maxzoom` of 6 to keep the file small for offline caching.

```
pmtiles extract https://build.protomaps.com/20250326.pmtiles bc_basemap_20250326.pmtiles --maxzoom=6 --bbox=-139.06,60,-114.03,48.3
```

- The pmtiles data was sourced from the Protomaps Basemap daily build which is derived from OpenStreetMap. See <https://docs.protomaps.com/basemaps/downloads>.
- The MapBox/MapLibre style for the pmtiles basemap was generated using the [protomaps/basemaps styles package](https://github.com/protomaps/basemaps/tree/main/styles). The style can also be created at <https://maps.protomaps.com/>.
- The MapBox/MapLibre style is applied to the OpenLayers VectorTile layer using [ol-mapbox-style](https://github.com/openlayers/ol-mapbox-style)'s `applyStyle` function.

### Distributing

Bump `appBuildVersion` appropriately in:

- `.github/workflows/asa_go_android_build.yml`
- `.github/workflows/asa_go_ios_build_deploy.yml`

Run the Android build workflow:

```bash
gh workflow run "Build ASA Go Android" --ref <branch-name>
```

Run the iOS build/deploy workflow:

```bash
gh workflow run "Publish ASA Go iOS" --ref <branch-name>
```

These workflows build the app from the specified branch.

## CI Workflows

### Integration Tests (`.github/workflows/asa_go_integration.yml`)

Runs on pull requests to `main` that touch `mobile/**`. Three parallel jobs:

- **`js_test`** — Runs Vitest unit tests with coverage on Ubuntu; uploads coverage to Codecov (`asa_go` flag)
- **`ios_test`** — Runs `yarn cap sync ios`, then `xcodebuild test` for the Keycloak Swift plugin on macOS; uploads `.xcresult` coverage bundle to Codecov (`keycloak_ios` flag)
- **`android_test`** — Runs `yarn cap sync android`, then `./gradlew jacocoTestReport` for both `asa-go/android` and `keycloak/android` on Ubuntu; uploads JaCoCo XML reports to Codecov (`android` flag)

All three jobs use the shared composite action `.github/actions/asa-go-setup`, which:

1. Sets up Node.js 20
2. Caches and installs `mobile/keycloak` node_modules, then runs `yarn build`
3. Caches and installs `mobile/asa-go` node_modules

### Android Release Build (`.github/workflows/asa_go_android_build.yml`)

Builds a signed release APK. Requires these GitHub secrets:

- `VITE_API_BASE_URL`, `VITE_KEYCLOAK_AUTH_URL`, `VITE_KEYCLOAK_REALM`, `VITE_KEYCLOAK_CLIENT`
- `VITE_PMTILES_BUCKET`, `VITE_BASEMAP_TILE_URL`, `VITE_BASEMAP_STYLE_URL`
- `ANDROID_KEY_ALIAS`, `ANDROID_SIGNING_STORE_PASSWORD`, `ANDROID_SIGNING_KEY_PASSWORD`, `ANDROID_KEYSTORE_BASE64`

### iOS Release Build (`.github/workflows/asa_go_ios_build_deploy.yml`)

Builds and deploys to TestFlight. Requires the above VITE secrets plus Apple provisioning secrets.
Built with Xcode 26 (macOS 15 runner) to meet the iOS 26 SDK requirement effective April 28, 2026.
