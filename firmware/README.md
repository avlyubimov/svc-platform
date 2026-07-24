# Firmware

Target architecture:
- FreeRTOS
- drivers
- event bus
- services
- plugins
- rule engine
- logger
- BLE/USB API

Update scaffolds:

- `radio/e73/` — Zephyr/nRF52840, MCUboot, MCUmgr/SMP over BLE, UART bridge,
  SWD recovery instructions.
- `bootloader/stm32h5/` — host-buildable OEMiRoT integration boundary for
  STM32H563; it is not an ad-hoc production bootloader.
- `update/` — target-neutral chunk/resume/admission/trial-boot state machine and
  the E73-to-STM32 UART framing contract.

No direct feature-to-hardware coupling. Use Output Manager and role mapping.

## Host validation

Run from `firmware/`:

```bash
make test
```

The firmware Makefile treats `core/*.h` and `services/*.h` as host-test
prerequisites, so interface changes force test binary rebuilds.

Current host tests cover:

- Configuration validation for battery settings, power budget, and output role
  enum bounds without role-to-output assumptions.
- Configuration Store record validation and two-slot selection so firmware
  defaults do not overwrite valid persisted user configuration.
- Configuration Store wrap-aware sequence selection across two persisted slots.
- Configuration Store reserved-field validation before accepting persisted
  records.
- Configuration Update preparation that refuses to persist a config until it is
  accepted against hardware capability.
- Configuration acceptance for a discovered hardware capability contract before
  startup uses a configuration.
- Hardware capability validation that checks generic board limits, safe defaults,
  CAN1 read-only policy, and config electrical limits without role assumptions.
  PB-100's compiled capability constant is checked against the JSON hardware
  capability manifest by repository validation.
- PB-100 board-level power budget service and configured load-shed ordering.
- Output Manager safe default-off, enable/disable, budget denial, telemetry
  denial, priority shedding, PWM increase revalidation, thermal derating, and
  fault lockout behavior.
- Overflow-safe projected-current denial for output starts and PWM increases.
- Battery protection warning, overflow-safe delayed cutoff latch using
  `shutdown_delay_s`, recovery, and invalid telemetry behavior.
- Event Bus FIFO order, overflow rejection, and empty-pop behavior.
- Event Dispatcher output overcurrent/fault handling through Output Manager.
- Event Log fixed-size diagnostic ring buffer with overwrite/drop accounting
  that saturates instead of wrapping the diagnostic drop counter.
- CAN1 listen-only TX denial and CAN2 expansion TX allowance.
- CAN RX Log fixed-size receive-only diagnostics plus a separate ISR-to-logger
  CAN1 queue, 44-byte v2 CRC records with 64-bit microsecond timestamps,
  identity-bearing 128-byte FatFs session headers, independent sync/close,
  restart/reopen, preallocation, rotation and torn-tail recovery. The target
  STM32 disk-I/O binding remains required before motorcycle logging tests.
- CAN Event Decode from received frames to internal Event Bus state-change
  events without output control.
- CAN Event Decode dropped-edge retry behavior when the Event Bus is full.
- Rule Event Bridge that drains CAN-derived and other condition events into rule
  condition state while retaining non-rule events for safety dispatch.
- Rule Runtime step that runs bridge, fault dispatch, and ordered rule
  evaluation in a safety-preserving order.
- System Safety Coordinator integration between battery cutoff, power-budget
  shedding, thermal derating/cutoff, Event Bus, and Output Manager output
  shutdown.
- System Safety runtime fail-safe shutdown when total-current telemetry is stale
  or invalid.
- System Safety retry of dropped runtime power-budget shed events.
- Role Resolver and Rule Engine role-action runner through Output Manager.
- Rule condition state tracking for engine, high-beam, left-indicator, and
  ambient-light day/dusk/night events.
- Rule runner evaluation for matched/unmatched conditions before role actions.
- Rule set runner for ordered multi-rule evaluation, skipped-rule accounting,
  and stop-on-first-failure behavior.
- Rule text parser for the initial supported JSON rule condition/action grammar.
- Output Manager PWM duty-cycle ownership and `pwm_allowed` enforcement.
- Rule text compile helpers from condition/action strings to in-memory
  `svc_rule_t` and ordered `svc_rule_t` arrays for multi-action rules.
- Rule-set compilation rejects invalid multi-action rule text before writing
  compiled rule entries or caller-provided condition buffers.
- Rule action grammar alignment between the JSON Schema, repository
  configuration validator, and firmware parser for supported roles and PWM
  values, with canonical `0` or `1..100` PWM literals.
- Runtime Boot path from direct configuration or persistent store that keeps
  outputs off unless configuration and hardware capability checks pass.
- Runtime Boot invalid-argument handling that leaves runtime state safe/off.
- Telemetry Snapshot validity/staleness for battery, total current, and
  per-output current samples.
- Telemetry-backed System Safety and Rule Engine wrappers for stale-data fail
  safe behavior.
- Thermal Protection allow/derate/cutoff decisions for PB-100 thermal zones.
- Thermal System Safety derating through Output Manager at warning threshold and
  shutdown through Output Manager on cutoff/stale telemetry.
- Firmware-update protocol mismatch, hardware mismatch, corrupt/repeated chunks,
  interruption/resume, incomplete file, hash/signature denial, parked-state
  admission, power loss before confirmation, rollback, and E73/STM32 version
  compatibility.
