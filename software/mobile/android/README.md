# SVCMobile for Android

Modules:

- `app-mobile` — phone UI built with Jetpack Compose;
- `app-automotive` — projected Android Auto `CarAppService`;
- `core-model` — versioned telemetry and repository contracts;
- `core-protocol` — manifest and chunk protocol;
- `core-ble` — Android BLE API and mock transport;
- `core-update` — OTA admission and transfer state;
- `core-mock` — mock device repository.

The phone target packages the shared vehicle-brand catalog, SVC artwork, and
the ignored `software/mobile/branding/local` source for future owner-only
custom packs. Profiles resolve manufacturers by stable `brandId`, use
`logo-on-dark.svg` unless a preferred asset is declared, and fall back to the
catalog display name when no wordmark exists. Startup uses one linear
`Animatable` timeline, an always-dark surface, system animator-scale detection,
and the same 2100/500 ms timing as iOS. Appearance settings provide
profile/fallback selection and replay.

## Build and test

```bash
gradle :app-mobile:assembleDebug test
```

The debug phone APK contains the merged Android Auto service. Enable Android
Auto developer mode and unknown sources, install the APK, and run Google's
Desktop Head Unit. The service declares the experimental IoT category and shows
information-only templates.

Successful DHU execution does not guarantee Google Play eligibility. IoT
category fit, templated-app requirements, driver-distraction rules, and current
distribution policy require a separate review before publication.
