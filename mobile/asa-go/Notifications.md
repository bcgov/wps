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

## Google Play App Signing

When distributing via the Play Store, Google re-signs your APK with their own App Signing Key rather than your local upload key. Firebase needs the SHA-1 of this key registered to validate the app's identity when requesting FCM tokens.
To get it: Play Console -> Test and release -> App Integrity -> App signing → copy the SHA-1 and add it to the app in Firebase Console under Project Settings.

## APNs auth key

The APNs auth key is the Apple push key used by Firebase to send iOS notifications through APNs.

Important points:

- It is only uploaded in Firebase Console.
- It can be used for both development and production APNs delivery.

Because we have separate Firebase setups for dev and prod, make sure the Firebase project used by each app has APNs configured.

## What lives where

In the app folder:

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

## Why we use separate app IDs

This repo uses separate app IDs for dev and prod instead of trying to inject only Firebase config into one app identity.

This lets dev and prod be installed on the same device at the same time. It also keeps dev push notifications separate from
prod and makes the Firebase app registration clearer, because each app variant has its own app ID.

On iOS, the current implementation uses separate Xcode targets and separate `Info.plist` files for those app identities.

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
