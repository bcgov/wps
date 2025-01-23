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

1. Install Android Studio (Jetbrains Toolbox recommended: https://www.jetbrains.com/toolbox-app/)
2. Find where the Android SDK is installed
   - With Jetbrains Toolbox it should be /Users/<user>/Library/Android/sdk/
   - Set `$ANDROID_HOME` to the path of the Android SDK
3. Go to `mobile/asa-go`
4. Run `yarn cap sync` to synchronize app with native platforms
5. Build and run with live reload: `ionic cap run android -l --external`
