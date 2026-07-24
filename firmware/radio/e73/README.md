# E73 nRF52840 radio scaffold

Target module: E73-2G4M08S1C (nRF52840).

The current compile-validation board is `nrf52840dk/nrf52840`. It proves Zephyr,
Bluetooth, MCUmgr, MCUboot, telemetry stub, update state machine, and UART source
compatibility only. It is not the final LB-100 board definition or pin map.

## Build

With a Zephyr 4.2 workspace:

```bash
west build \
  --sysbuild \
  -b nrf52840dk/nrf52840 \
  firmware/radio/e73
```

Sysbuild enables MCUboot. The upstream MCUboot development key path is acceptable
only for compile validation and must be treated as
`TEST KEY — NOT FOR PRODUCTION`. Production signing material is not stored in
the repository.

## Included boundary

- BLE peripheral with LE Security Mode 1 level 2 request;
- MCUmgr/SMP over BLE and image management;
- MCUboot primary/secondary test-boot direction;
- explicit MCUboot test request and post-health-check image confirmation;
- BLE-to-UART bridge abstraction;
- unavailable-by-default telemetry stub;
- shared resumable update state machine.

The selected console UART is only a compile placeholder. Final E73 UART pins,
flow control, baud rate, wake behavior, BLE security provisioning, GATT
authorization, flash partitions, and radio power behavior require the accepted
LB-100 board definition and EVT measurements.

## First programming and recovery through SWD

LB-100 exposes E73 `SWDIO`, `SWDCLK`, `BLE_RESET_N`,
`RADIO_SENSOR_3V3` target reference, and GND on accessible pads.

1. Keep PB outputs disabled and power LB-100 from the approved current-limited
   service source.
2. Connect the probe target-reference input to `RADIO_SENSOR_3V3`; do not drive
   or source that rail from the probe.
3. Connect GND, SWDIO, SWDCLK, and optional reset.
4. Verify target voltage before any erase/program command.
5. Program MCUboot and the signed development application.
6. Read back/verify, reset, and capture the first boot log.
7. Confirm image slots and mark the known-good development image confirmed.

Do not drive E73 signals when the radio rail is off. BLE DFU is a field-update
path, not a replacement for SWD first programming or hardware recovery.

## MCUmgr evidence

- https://docs.zephyrproject.org/latest/services/device_mgmt/mcumgr.html
- https://docs.zephyrproject.org/latest/services/device_mgmt/smp_transport.html
- https://docs.zephyrproject.org/latest/services/device_mgmt/ota.html
