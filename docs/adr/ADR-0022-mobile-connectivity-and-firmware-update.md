# ADR-0022: Mobile connectivity and firmware update

## Status

Accepted — Product Owner direction on 2026-07-23

## Context

LB-100 contains an E73-2G4M08S1C radio module based on nRF52840, but no Wi-Fi
interface. CHIGEE AIO-6 provides a projected CarPlay/Android Auto display; it is
not the execution environment for SVC Mobile. Firmware distribution therefore
needs a phone-mediated path that preserves standalone SVC operation, safe
default-off behavior, configuration separation, and the existing Output Manager
boundary.

CarPlay requires an Apple-approved application category and managed entitlement.
Android Auto templated applications must fit a supported Google category and
pass the applicable quality review. Neither approval is assumed by this ADR.

## Decision

Use the following connectivity and update path:

```text
GitHub Releases
      |
      | HTTPS through the phone
      v
iOS / Android SVC Mobile
      |
      | authenticated BLE
      v
E73 / nRF52840
      |
      | framed UART
      v
STM32H563
      |
      v
telemetry, CAN, sensors, Output Manager
```

- SVC Mobile executes on an iPhone or Android phone.
- CHIGEE AIO-6 is only a CarPlay/Android Auto display host. No SVC APK or iOS
  application is installed on CHIGEE.
- The phone may connect to CHIGEE through CarPlay/Android Auto while maintaining
  a separate BLE connection to SVC.
- The current LB-100 has no Wi-Fi. It cannot download a GitHub release directly.
- SVC Mobile checks GitHub Releases over HTTPS, validates the manifest and
  artifacts, and transfers an explicitly selected update over BLE.
- Installation requires an explicit confirmation on the phone while parked.
  CarPlay and Android Auto surfaces are information-only and cannot install
  firmware or directly control power outputs.
- SVC remains fully functional without a phone or cloud connection.
- Mobile commands never bypass services, the Event Bus, safety coordination, or
  Output Manager. The first iteration exposes no mobile power-output command.
- E73 uses Zephyr/Nordic nRF Connect SDK direction with MCUboot and MCUmgr/SMP
  over BLE. Signed primary/secondary images use test boot, image confirmation,
  and rollback. Hardware SWD remains the first-programming and recovery path.
- STM32H563 uses ST's OEMiRoT direction with immutable secure boot, signed
  active/download slots, integrity checks, boot confirmation, watchdog, and
  rollback. E73 only transports the candidate image over UART; STM32 validates
  and writes its own staging area.
- E73 is not a hardware recovery programmer for STM32. STM32 boot-chain recovery
  remains through the approved SWD/USB service path.
- Production signing keys are external secrets. The repository may contain only
  fixtures explicitly marked `TEST KEY — NOT FOR PRODUCTION`.

## OTA admission

STM32 is authoritative for the final installation admission decision. An update
is denied with explicit reason codes unless all of these conditions are fresh
and valid:

- vehicle speed equals zero;
- engine is off;
- all managed power outputs are off;
- no critical fault is active;
- battery voltage is inside configured update limits;
- board temperature is inside configured update limits;
- BLE/UART transfer health is acceptable;
- the complete candidate has passed length, SHA-256, signature, hardware
  revision, protocol, and minimum-bootloader checks.

The phone preflights the same conditions for user feedback, but a phone result
cannot override device-side denial.

## Projection surfaces

- The phone application is the complete product surface.
- The experimental CarPlay surface uses only Apple system templates and remains
  behind `SVC_CARPLAY_EXPERIMENT`. No entitlement is committed. The app builds
  normally with the flag disabled.
- The experimental Android Auto surface uses AndroidX Car App Library templates
  and declares the IoT category for development. Publication eligibility is a
  separate Google review outcome.
- Projected surfaces show telemetry, warnings, and channel state only.
- Automatic launch of SVC on a CarPlay host is not guaranteed. The host may
  reconnect automatically, but the user can still need to select SVC.

## Evidence

- CHIGEE AIO-6 manual:
  https://www.chigee.com/pages/manual-for-aio6-max
- Apple CarPlay entitlement process:
  https://developer.apple.com/documentation/carplay/requesting-carplay-entitlements
- Android for Cars App Library:
  https://developer.android.com/training/cars/apps/library
- Zephyr MCUmgr and BLE SMP transport:
  https://docs.zephyrproject.org/latest/services/device_mgmt/mcumgr.html
  https://docs.zephyrproject.org/latest/services/device_mgmt/smp_transport.html
- STM32H563 product and OEMiRoT guidance:
  https://www.st.com/en/microcontrollers-microprocessors/stm32h563ii.html
  https://wiki.st.com/stm32mcu/wiki/Security:How_to_start_with_STM32CubeMX_OEMiRoT_Boot_path_on_STM32H563

## Consequences

- Mobile applications and release automation can be developed without changing
  PB-100, LB-100, FB-100, CAN1, or output-control architecture.
- Firmware updates remain deliberate, phone-mediated, signed, resumable, and
  recoverable.
- CarPlay and Android Auto are optional constrained views, not alternate control
  planes.
- App Store, Google Play, Apple entitlement, final Android Auto category
  acceptance, production keys, target flash layouts, radio pin mapping, and
  hardware validation remain explicit dependencies.
