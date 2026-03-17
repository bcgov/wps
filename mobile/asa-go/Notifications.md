# Notifications

Short reference for the ASA Go mobile notification setup.

## iOS app IDs

We have two iOS app variants:

- Prod bundle ID: `ca.bc.gov.asago`
- Dev bundle ID: `ca.bc.gov.asago.dev`

These bundle IDs must match the Firebase iOS app registration exactly.

## Android app IDs

We also have two Android app variants:

- Prod application ID: `ca.bc.gov.asago`
- Dev application ID: `ca.bc.gov.asago.dev`

These application IDs must match the Firebase Android app registration exactly.

## Firebase dev vs prod

We use different Firebase app configs for prod and dev on both platforms.

- Prod Firebase plist: `ios/App/App/Firebase/Prod/GoogleService-Info.plist`
- Dev Firebase plist: `ios/App/App/Firebase/Dev/GoogleService-Info.plist`
- Prod Android config: `android/app/src/prod/google-services.json`
- Dev Android config: `android/app/src/dev/google-services.json`

Current mapping:

- Prod plist `BUNDLE_ID`: `ca.bc.gov.asago`
- Dev plist `BUNDLE_ID`: `ca.bc.gov.asago.dev`

If the wrong plist is used, Firebase Messaging will not be configured for the installed app correctly.

The same rule applies on Android: if the wrong `google-services.json` is used, Firebase Messaging will not be configured for the installed app correctly.

## GoogleService-Info.plist

`GoogleService-Info.plist` is the iOS Firebase app config file.

It tells the app which Firebase project/app to talk to, including:

- Firebase project ID
- iOS app ID
- sender ID
- API key
- expected iOS bundle ID

It is required locally in the iOS project.

## google-services.json

`google-services.json` is the Android Firebase app config file.

It tells the Android app which Firebase project/app to talk to, including:

- Firebase project ID
- Android app ID
- sender ID
- API key
- expected Android application ID

It is required locally in the Android project.

## APNs auth key

The APNs auth key is the Apple push key used by Firebase to send iOS notifications through APNs.

Important points:

- It does not go in this repo.
- It does not go in Xcode project files.
- It is uploaded in Firebase Console.
- It can be used for both development and production APNs delivery.

Because we have separate Firebase setups for dev and prod, make sure the Firebase project used by each app has APNs configured.

## What lives where

In the app repo:

- iOS bundle IDs
- Android application IDs / flavors
- Xcode targets/schemes (`ASA Go` and `ASA Go Dev`)
- `GoogleService-Info.plist`
- `google-services.json`
- Capacitor config

In Firebase Console:

- APNs auth key upload
- Firebase app registration for each bundle ID
- Cloud Messaging setup

## Auth callback scheme

The Android dev and prod flavors currently share the same AppAuth redirect scheme:

- `ca.bc.gov.asago`

That matches the older auth setup. The app IDs are still different, but the auth callback scheme is shared.

This is workable, but there is one tradeoff: if both Android app variants are installed on the same device, a custom-scheme auth callback can be ambiguous because both apps can claim the same scheme.

## Why we use separate app IDs

This repo uses separate app IDs for dev and prod instead of trying to inject only Firebase config into one app identity.

Why this is useful:

- dev and prod can both be installed on the same iPhone
- dev and prod can both be installed on the same Android device
- dev push notifications stay separate from prod
- dev testing is less likely to affect the prod app
- the Firebase app registration is clearer because each app variant has its own app ID

An alternative is to keep one app ID and inject different config at build time. That can work, but it means dev and prod are still the same app identity, so they cannot be installed side by side.

## Running dev vs prod

`capacitor.config.ts` switches between dev and prod using `APP_ENV`.

Examples:

```bash
APP_ENV=dev yarn cap:sync:ios:dev
APP_ENV=prod yarn cap:sync:ios:prod
```

For live reload:

```bash
APP_ENV=dev ionic capacitor run ios -l --external
APP_ENV=prod ionic capacitor run ios -l --external
APP_ENV=dev ionic capacitor run android -l --external
APP_ENV=prod ionic capacitor run android -l --external
```

On iOS, `APP_ENV=dev` selects the `ASA Go Dev` scheme and `APP_ENV=prod` selects `ASA Go`.

## Quick checks

If notifications are not working, check these first:

1. The installed app's iOS bundle ID or Android application ID matches the Firebase app config.
2. The correct `GoogleService-Info.plist` or `google-services.json` is included for the target/flavor.
3. APNs auth key is uploaded in the correct Firebase project.
4. The iOS app is running on a real iPhone, not the iOS simulator.
5. Push permissions were granted on the device.
