# Telemetry Snapshot

Telemetry Snapshot is the firmware boundary between future ADC/I2C/CAN drivers
and safety services.

## Initial responsibilities

- Store battery voltage, thermal zone temperatures, total input current, and
  per-output current samples.
- Track sample validity independently from sample values.
- Track update timestamps for stale-data checks.
- Provide power-budget and battery-service input structs.
- Reject invalid output IDs for per-output current updates.
- Feed System Safety, Rule Engine, and Thermal Protection wrapper APIs so callers
  do not pass raw validity flags manually.

## Safety contract

Missing, invalid, or stale telemetry must propagate as `telemetry_valid = false`.
Power Budget and Battery Protection already treat invalid telemetry as a safe
denial/cutoff path.

## Host-testable implementation

- `firmware/services/telemetry.h`
- `firmware/services/telemetry.c`
- `firmware/tests/test_telemetry.c`
