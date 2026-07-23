# SVCMobile for iOS

The default target is a SwiftUI phone application backed by
`MockDeviceRepository`. CoreBluetooth is isolated behind `BLETransport`.

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

The experimental template is information-only. It contains no channel control
and no firmware update action. Apple approval is not assumed, and CarPlay cannot
be forced to open SVC automatically after every host reconnect.
