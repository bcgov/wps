# ASA Go

Capacitor app using react/vite.

## Building

1. `yarn install`
2. `yarn build`

## Setup live reload

1. Install ionic CLI and native run for live reload with: `npm install -g @ionic/cli native-run`

### Building/Running iOS

1. Make sure xcode is installed with `xcode-select --install`
2. Go to `mobile/asa-go/ios`
3. Install/update cocoapods with `gem install cocoapods`
4. Go to `mobile/asa-go`
5. Run `yarn cap sync` to synchronize app with native platforms
6. Build and run with live reload: `ionic cap run ios -l --external`

### Building/Running Android

1. Install Android Studio (Jetbrains Toolbox recommended: <https://www.jetbrains.com/toolbox-app/>)
2. Find where the Android SDK is installed
   - With Jetbrains Toolbox it should be /Users/<user>/Library/Android/sdk/
   - Set `$ANDROID_HOME` to the path of the Android SDK
3. Go to `mobile/asa-go`
4. Run `yarn cap sync` to synchronize app with native platforms
5. Navigate to the android directory and run Gradle commands:
   ```bash
   cd android
   ./gradlew clean
   ./gradlew build
   cd ..
   ```
6. Build and run with live reload: `ionic cap run android -l --external`

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

Bump `appBuildVersion` appropriately via semvar, in `.github/workflows/asa_go_build_deploy.yml`.
Run: `gh workflow run "Publish ASA Go"`
This will build and publish the app that is on the `main` branch.
