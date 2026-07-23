# OEMiRoT integration checklist for STM32H563

## Required ST baseline

- Pin the reviewed STM32CubeH5 release.
- Start from ST's `NUCLEO-H563ZI` OEMiRoT boot and provisioning examples.
- Generate the target project and flash layout with ST tools.
- Keep the OEMiRoT boot region immutable/protected after the development
  lifecycle is complete.
- Use a download slot separate from the active application.
- Use ST image tooling for the exact authenticated image format.

STM32H563 supports up to 2 MiB dual-bank flash. Exact partition sizes are not
guessed in this scaffold.

## Required product behavior

- Authenticate every candidate signature.
- Verify image length and SHA-256/integrity metadata.
- Verify LB-100 hardware revision and firmware dependencies.
- Enforce anti-rollback/minimum-version policy.
- Request a trial boot only after OTA admission passes.
- Arm the independent watchdog during trial boot.
- Confirm only after application self-test, configuration load, telemetry
  startup, and Output Manager safe-off checks pass.
- Roll back or enter the ST recovery path after failed confirmation.
- Keep user configuration outside image replacement areas.
- Reject corrupted, incomplete, incompatible, or unconfirmed images.

## Provisioning boundary

Production authentication keys are generated and retained outside the
repository. ST example/default keys may be used only for local development and
must be labelled `TEST KEY — NOT FOR PRODUCTION`.

Provisioning option bytes, debug authentication, TrustZone/HDPL boundaries,
write protection, secure storage, anti-rollback counters, regression policy,
and recovery entry require a separate reviewed manufacturing procedure.

## Recovery

E73 is not an STM32 hardware programmer. It can forward bytes only while the
STM32 boot/application update receiver is healthy. Boot-chain damage requires
the approved STM32 SWD or ROM/USB recovery path.

## Evidence

- STM32H563 product:
  https://www.st.com/en/microcontrollers-microprocessors/stm32h563ii.html
- ST OEMiRoT for STM32H563:
  https://wiki.st.com/stm32mcu/wiki/Security:How_to_start_with_STM32CubeMX_OEMiRoT_Boot_path_on_STM32H563
