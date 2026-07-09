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
- Configuration acceptance for a discovered hardware capability contract before
  startup uses a configuration.
- Hardware capability validation that checks generic board limits, safe defaults,
  CAN1 read-only policy, and config electrical limits without role assumptions.
  PB-100's compiled capability constant is checked against the JSON hardware
  capability manifest by repository validation.
- PB-100 board-level power budget service.
- Output Manager safe default-off, enable/disable, budget denial, telemetry
  denial, and fault lockout behavior.
- Battery protection warning, cutoff latch, recovery, and invalid telemetry
  behavior.
- Event Bus FIFO order, overflow rejection, and empty-pop behavior.
- Event Dispatcher output overcurrent/fault handling through Output Manager.
- Event Log fixed-size diagnostic ring buffer with overwrite/drop accounting.
- CAN1 listen-only TX denial and CAN2 expansion TX allowance.
- System Safety Coordinator integration between battery cutoff, Event Bus, and
  Output Manager output shutdown.
- Role Resolver and Rule Engine skeleton for role-based actions through Output
  Manager.
- Rule condition state tracking for engine, high-beam, and left-indicator events.
- Rule runner evaluation for matched/unmatched conditions before role actions.
- Rule text parser for the initial supported JSON rule condition/action grammar.
- Output Manager PWM duty-cycle ownership and `pwm_allowed` enforcement.
- Rule text compile helper from condition/action strings to in-memory `svc_rule_t`.
- Telemetry Snapshot validity/staleness for battery, total current, and
  per-output current samples.
- Telemetry-backed System Safety and Rule Engine wrappers for stale-data fail
  safe behavior.
- Thermal Protection allow/derate/cutoff decisions for PB-100 thermal zones.
- Thermal System Safety shutdown through Output Manager on cutoff/stale
  telemetry.
