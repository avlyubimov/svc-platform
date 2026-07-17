# Telemetry Snapshot

Telemetry Snapshot is the firmware boundary between future ADC/I2C/CAN drivers
and safety services.

## Initial responsibilities

- Store battery voltage, thermal zone temperatures, total input current, and
  per-output current samples.
- Track sample validity independently from sample values.
- Track update timestamps for stale-data checks.
- Keep total-current and per-output current calibration parameters in
  `svc_device_config_t`, not in driver constants.
- Provide power-budget and battery-service input structs.
- Reject invalid output IDs for per-output current updates.
- Feed System Safety, Rule Engine, and Thermal Protection wrapper APIs so callers
  do not pass raw validity flags manually.

## Safety contract

Missing, invalid, or stale telemetry must propagate as `telemetry_valid = false`.
Power Budget and Battery Protection already treat invalid telemetry as a safe
denial/cutoff path.

Current calibration is represented by `svc_telemetry_config_t` in
`firmware/core/svc_config.h`. The default PB-100 total-current planning values
are 500 µΩ shunt resistance, 40960 µV monitor range, 0 mA zero offset,
1000000 ppm gain, 1000 ms stale timeout, and 60000 mA plausible maximum.
Per-output IMON calibration uses role-free `OUT1`..`OUT10` records with
0 mA offset, 1000000 ppm gain, 1000 ms stale timeout, and class ranges of
20000 mA, 30000 mA, 15000 mA, or 8000 mA as defined by the PB-100 telemetry
map. `firmware/services/config_validator.c` rejects calibration records that
cannot cover the configured limits or that exceed their electrical ranges.

## Host-testable implementation

- `firmware/services/telemetry.h`
- `firmware/services/telemetry.c`
- `firmware/tests/test_telemetry.c`
