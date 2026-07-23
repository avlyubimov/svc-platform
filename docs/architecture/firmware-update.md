# Firmware Update Architecture

## Trust boundary

GitHub and the phone transport release artifacts; they are not the root of
device trust. Each target verifies its own candidate before installation.

```text
GitHub draft/release
  firmware-manifest.json
  signed E73 image
  signed STM32 image
            |
            | HTTPS, manifest/hash checks
            v
phone cache
            |
            | authenticated BLE, resumable chunks
            v
E73 staging / MCUboot secondary slot
            |
            +-- E73 image: MCUboot test boot -> confirm / rollback
            |
            +-- STM32 image: framed UART -> STM32 download slot
                                      -> OEMiRoT verify/install
                                      -> test boot -> confirm / rollback
```

## Release manifest

`firmware-manifest.json` is versioned independently from BLE protocol version.
Every component identifies:

- target and semantic version;
- compatible hardware revisions;
- required protocol version;
- file name and byte length;
- SHA-256 digest and detached signature;
- minimum bootloader version.

The mobile parser rejects unknown schema versions, duplicate targets, path-like
filenames, incompatible hardware, protocol mismatch, invalid size, wrong digest,
invalid signature, or an insufficient bootloader. Dev fixtures may use explicit
placeholder signatures. Release mode rejects every placeholder.

Production signing keys are never generated or stored in this repository.

## BLE transfer

The control plane creates a transfer session and negotiates protocol version,
component, size, hash, chunk size, and resume point. Each data frame carries a
transfer ID, absolute offset, sequence number, payload length, and CRC-32.

The receiver:

- acknowledges only committed chunks;
- returns the next expected sequence and offset;
- NACKs a corrupt or out-of-order chunk;
- accepts an idempotent retry of the last committed chunk;
- persists a bounded resume record;
- resumes after a temporary BLE disconnect only after re-authentication;
- invalidates the session when metadata changes.

The complete candidate is hashed after transfer. Installation cannot begin from
a partially received file.

## E73

The E73 direction is Zephyr or Nordic nRF Connect SDK with:

- MCUboot;
- MCUmgr/SMP over BLE;
- signed images;
- primary and secondary slots;
- test boot;
- explicit image confirmation;
- rollback after failed health confirmation.

The repository build target uses `nrf52840dk/nrf52840` only as a compile
validation board until the final E73/LB-100 board definition and pin mapping are
accepted. First programming and recovery use the already routed E73 SWD pads.
BLE DFU never replaces SWD recovery.

## STM32H563

STM32H563 provides up to 2 MiB dual-bank flash. The selected implementation
direction is ST OEMiRoT for STM32H563 rather than an ad-hoc bootloader.

The immutable boot stage owns:

- image size and layout checks;
- hardware revision and dependency checks;
- SHA-256/integrity verification;
- digital-signature authentication;
- anti-rollback/minimum-version policy;
- candidate installation;
- boot-attempt accounting;
- watchdog-backed trial boot;
- explicit application confirmation;
- automatic rollback or recovery entry.

E73 is a transport peer only. STM32 receives framed UART data, writes its own
download/staging slot, verifies the final hash, and requests reboot. If the
STM32 boot chain itself is damaged, recovery remains SWD/USB.

Final flash partition sizes, OEMiRoT provisioning, option bytes, TrustZone/HDPL
policy, target keys, and CubeH5 integration require an accepted target-specific
security review before hardware programming.

## Admission checks

`install` returns a stable denial code for every failed condition:

| Code | Condition |
|---|---|
| `vehicle_moving` | speed is non-zero, invalid, or stale |
| `engine_running` | engine state is on, invalid, or stale |
| `outputs_active` | any Output Manager channel is active |
| `critical_fault` | a critical diagnostic is active |
| `battery_out_of_range` | battery sample is invalid/stale or outside configured limits |
| `temperature_out_of_range` | required board temperature is invalid/stale or outside configured limits |
| `link_unstable` | BLE/UART health is below the configured threshold |
| `file_incomplete` | committed length differs from manifest length |
| `hash_mismatch` | SHA-256 differs |
| `signature_invalid` | target verifier rejects the signature |
| `hardware_mismatch` | board revision is absent from the component allowlist |
| `protocol_incompatible` | negotiated protocol is unsupported |
| `bootloader_too_old` | minimum bootloader is not met |

The phone displays these reasons, but only the device authorizes installation.

## Failure behavior

- Power loss before a complete staged image leaves the active image unchanged.
- Power loss after install request but before confirmation boots according to
  OEMiRoT/MCUboot trial rules.
- Failure to confirm rolls back.
- A rollback never restores or rewrites user configuration.
- Dangerous commands require an authenticated confirmed session.
- CarPlay and Android Auto cannot request install.

## Source evidence

- Zephyr MCUmgr:
  https://docs.zephyrproject.org/latest/services/device_mgmt/mcumgr.html
- Zephyr SMP transport:
  https://docs.zephyrproject.org/latest/services/device_mgmt/smp_transport.html
- Zephyr OTA:
  https://docs.zephyrproject.org/latest/services/device_mgmt/ota.html
- STM32H563:
  https://www.st.com/en/microcontrollers-microprocessors/stm32h563ii.html
- STM32H563 OEMiRoT:
  https://wiki.st.com/stm32mcu/wiki/Security:How_to_start_with_STM32CubeMX_OEMiRoT_Boot_path_on_STM32H563
