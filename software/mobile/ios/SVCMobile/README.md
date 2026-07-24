# SVCMobile for iOS

The default target is a SwiftUI phone application backed by
`MockDeviceRepository`. CoreBluetooth is isolated behind `BLETransport`.

The startup animation uses `TimelineView` at a 60 Hz cadence over an opaque
`#050505` surface. XcodeGen bundles the shared vehicle-brand catalog and SVC
artwork. Profiles resolve manufacturers by stable `brandId`, use
`logo-on-dark.svg` unless a preferred asset is declared, and fall back to the
catalog display name when no wordmark exists. The ignored
`software/mobile/branding/local` folder remains available for future
owner-only custom packs. The Appearance screen provides profile selection,
animation disable, reduced-motion preview, and replay.

The SwiftUI SVC Ride Dashboard uses the shared technical vehicle profile
independently from BrandPack selection. It provides adaptive landscape/portrait
layouts, profile-driven tachometer zones, explicit telemetry quality states,
SVC-estimated lean, automatic Day/Night hysteresis, and Reduce Motion. Gear
remains `—` under telemetry v1 and no value is inferred from speed/RPM. SwiftUI
previews use SVC-owned presentation without manufacturer artwork.

## Generate and test

```bash
brew install xcodegen
xcodegen generate
xcodebuild \
  -project SVCMobile.xcodeproj \
  -scheme SVCMobile \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  test
```

## CarPlay experiment

The repository contains no CarPlay entitlement and the generated project has no
CarPlay scene configuration. `CarPlaySceneDelegate.swift` compiles to an empty
translation unit unless `SVC_CARPLAY_EXPERIMENT` is defined.

After Apple approves an applicable category:

1. request the category-specific entitlement at Apple CarPlay Contact Us;
2. accept the entitlement addendum;
3. enable the managed capability for the App ID;
4. regenerate the provisioning profile;
5. add the approved entitlement file outside the default scaffold;
6. add `SVC_CARPLAY_EXPERIMENT` to `SWIFT_ACTIVE_COMPILATION_CONDITIONS`;
7. add the CarPlay scene role to the target Info configuration;
8. test with Xcode Simulator using `I/O > External Displays > CarPlay`.

The experimental template is information-only and reduced to speed, gear,
battery, SVC current, main warning, and connection state. It contains no full
graphical dashboard, channel control, or firmware update action. Apple approval
is not assumed, and CarPlay cannot be forced to open SVC automatically after
every host reconnect.
