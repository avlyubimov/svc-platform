# SVC Mobile

SVC Mobile runs on the phone. CHIGEE AIO-6 is a CarPlay/Android Auto projection
host, not an installation target.

## Layout

```text
protocol/   Versioned JSON and BLE contracts
ios/        SwiftUI/CoreBluetooth application scaffold
android/    Kotlin/Compose/Android BLE/Car App scaffold
mock-data/  Hardware-free application data
```

Both phone applications start with `MockDeviceRepository`. No mobile or
projected-display action controls a physical power channel.

## Startup and personal branding

The phone apps load the common profile catalog from
`branding/brand-pack-index-v1.json` and the 2100 ms startup contract from
`branding/startup-animation-v1.json` at runtime. Manufacturer metadata and
artwork resolve from `branding/vehicle-brands/vehicle-brands-v1.json` by stable
`brandId`; `brandId`, `model`, `generation`, and `year` remain separate profile
fields. Brand text, color, asset paths, profile choices, and phase timing are
not duplicated in Swift or Kotlin.

The default personal profile is `bmw-r1200gs-k25-personal` with theme
`svc-boxer-blue`. Its preferred asset is the period-correct
`brands/bmw/bmw-roundel-1997-2020.svg`. Other profiles use
`logo-on-dark.svg` on the standard dark startup surface. Manufacturer
wordmarks are optional and fall back to the catalog display name as text. If a
profile or required logo is unavailable, the apps show the committed SVC mark,
`SMART VEHICLE CONTROLLER`, and `ENGINEERED FOR THE RIDE`. No brand artwork is
downloaded at runtime. Preview the result from
`Settings → Appearance → Preview Startup Animation`.

The public application identity is always SVC. The phone launcher, App
Store/Google Play package, CarPlay, and Android Auto use the committed SVC app
icon sourced from `branding/svc/svg/svc-app-icon.svg` and its platform exports.
Manufacturer assets appear only inside the selected post-launch phone profile
animation. The OS launch surface stays neutral black and never presents BMW
branding.

The vehicle catalog preserves `THIRD_PARTY_NOTICES.md`, its pinned Simple Icons
license/disclaimer, per-brand source URLs, and the original/derived SVG
variants. Run protocol validation after adding a brand; it requires every
catalog entry to contain `brand.json`, `logo-source.svg`, `logo-on-dark.svg`,
`logo-on-light.svg`, and `logo-accent.svg`, and parses every SVG as XML.

Profile/theme loading, mock BLE restoration, telemetry refresh, and screen
restoration start in parallel. The animation never waits for BLE; Dashboard
shows `Connecting to SVC` until restoration completes. Critical warnings use a
500 ms startup and render as a red card after it. Reduced motion also uses a
500 ms fade, while disabled animation enters the selected screen immediately.
No POST statuses or fabricated `OK` values appear in startup.

The animation is phone-only. CarPlay and Android Auto retain host-controlled
launch transitions and show only the SVC app identity, profile name, permitted
accent, and informational templates.

## GitHub Releases client

The iOS and Android data layers include an unauthenticated client for this
public repository. No PAT is stored or sent:

- stable uses `GET /repos/avlyubimov/svc-platform/releases/latest`;
- beta and test load the public release list and select matching prerelease
  tags;
- tags must be `svc-vX.Y.Z`, `svc-vX.Y.Z-beta.N`, or
  `svc-vX.Y.Z-test.N`;
- `firmware-manifest.json`, component assets, and detached signature assets
  are downloaded over HTTPS;
- GitHub asset size/digest, manifest size/SHA-256, detached-signature
  size/SHA-256, key ID, and RSA-PSS/SHA-256 signature are checked before a
  manifest is accepted.

The production public key is injected into each phone build after production
key provisioning; private keys never enter a mobile build. Missing or
unrecognized public-key material fails closed. Installation and BLE firmware
transfer remain mock-only. `review-raw` assets are explicitly non-installable.

## Protocol validation

```bash
python3 -m pip install -r tools/mobile_protocol_validation/requirements.txt
python3 tools/validate_mobile_protocol.py
python3 tools/validate_ota_release.py scaffold
PYTHONPATH=tools python3 -m unittest discover \
  -s tools/mobile_protocol_validation/tests
```

## iOS

Requirements: current Xcode and XcodeGen.

```bash
cd software/mobile/ios/SVCMobile
xcodegen generate
xcodebuild \
  -project SVCMobile.xcodeproj \
  -scheme SVCMobile \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  test
```

The default target has no CarPlay entitlement. See
`ios/SVCMobile/README.md` before enabling the experimental scene.

## Android

Requirements: JDK 21, Android SDK 36, and Gradle 8.11.1.

```bash
gradle -p software/mobile/android \
  :app-mobile:assembleDebug \
  test
```

Install `app-mobile/build/outputs/apk/debug/app-mobile-debug.apk`, enable Android
Auto developer mode and unknown sources, then start Desktop Head Unit according
to Google's DHU instructions. The merged APK contains the experimental IoT
`CarAppService`.

## Mock data

`mock-data/device-v1.json` intentionally marks undecoded CAN values unavailable.
Mock values are development data and are never substituted for missing vehicle
signals on a real connection.
