# Mobile Connectivity

## Boundary

SVC Mobile is an optional client of the SVC platform. Core vehicle behavior,
rules, logging, protection, and Output Manager continue to work without a phone,
CHIGEE, GitHub, or Internet access.

```text
GitHub Releases --HTTPS--> iOS / Android phone
                                  |
                                  +--CarPlay / Android Auto--> CHIGEE AIO-6
                                  |
                                  +--authenticated BLE-------> E73 / nRF52840
                                                                    |
                                                                    +--UART--> STM32H563
```

CHIGEE AIO-6 documents wireless CarPlay/Android Auto pairing with a phone. SVC
therefore runs on that phone and supplies only a projected, template-constrained
surface to CHIGEE. Installing an SVC APK or iOS binary on CHIGEE is not part of
the platform architecture.

The phone can maintain the projected-display session and the separate SVC BLE
session at the same time. Actual coexistence, reconnect latency, RF range, and
throughput require EVT measurement with the production enclosure.

## Application layers

```text
SwiftUI / Jetpack Compose
        |
Application state and use cases
        |
DeviceRepository
        +-- MockDeviceRepository
        +-- BleDeviceRepository
                |
          versioned protocol
                |
          BLE transport
```

UI code does not own CoreBluetooth or Android BLE callbacks. Repository and
transport interfaces make mock startup and protocol tests deterministic.

## Phone application

The full phone application contains:

- discovery and pairing;
- main telemetry dashboard;
- ten generic channel states and currents;
- diagnostics and CAN telemetry;
- event log;
- device and protocol versions;
- firmware release check, transfer, and confirmed installation;
- settings and calibration.

No first-iteration phone action enables, disables, or PWM-controls a physical
output. Future output actions require an accepted command contract and still
flow through device services and Output Manager.

## CarPlay

The experimental CarPlay scene is guarded by `SVC_CARPLAY_EXPERIMENT`. The
default build has no CarPlay scene manifest and no entitlement.

If Apple approves a suitable category:

1. request the category-specific CarPlay entitlement from Apple;
2. accept the CarPlay entitlement addendum;
3. enable the managed capability for the App ID;
4. create a new provisioning profile;
5. add the approved entitlement to a non-placeholder entitlements file;
6. enable the CarPlay scene configuration and compile flag;
7. validate only system-provided templates in Simulator and on an approved host.

The projected view is information-only: battery voltage, total current, engine
temperature, speed, RPM, fuel use, ambient temperature, light, lean angle,
warnings, and generic channel states. It exposes neither OTA nor output control.

Apple supports a fixed set of CarPlay categories and reviews entitlement
requests. An arbitrary SVC instrument dashboard is not assumed to qualify.
Automatic selection of SVC after CarPlay reconnect is also not guaranteed.

## Android Auto

The experimental `CarAppService` uses AndroidX Car App Library templates and
declares `androidx.car.app.category.IOT`. It exposes status, warnings, channel
state, and principal motorcycle metrics without controls or OTA.

The library uses a host application to render client templates. IoT category
declaration and successful Desktop Head Unit execution do not guarantee Google
Play approval; supported-category, driver-distraction, quality, and distribution
rules must be reviewed again before publication.

## Source evidence

- CHIGEE AIO-6 manual:
  https://www.chigee.com/pages/manual-for-aio6-max
- Apple CarPlay:
  https://developer.apple.com/carplay/
- Apple entitlement request:
  https://developer.apple.com/documentation/carplay/requesting-carplay-entitlements
- Android for Cars App Library:
  https://developer.android.com/training/cars/apps/library
