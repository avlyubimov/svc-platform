# Thermal Protection Service

Thermal Protection evaluates PB-100 board and power-zone temperatures from
Telemetry Snapshot and configuration thresholds.

## Zones

- `SVC_THERMAL_ZONE_PCB` — board reference temperature.
- `SVC_THERMAL_ZONE_PWR_A` — high-current/input hot zone.
- `SVC_THERMAL_ZONE_PWR_B` — secondary power zone.

## Initial behavior

- `ALLOW` below warning threshold.
- `DERATE` at or above warning threshold.
- `CUTOFF` at or above cutoff threshold.
- Cutoff latches per zone until temperature falls to recovery threshold.
- Missing, invalid, or stale temperature telemetry forces cutoff.
- System Safety applies thermal cutoff by disabling active outputs through the
  Output Manager.

## Configuration

Default thresholds are shared by all three zones until board thermal validation
provides zone-specific values:

- warning: 85 °C
- cutoff: 105 °C
- recovery: 75 °C

Thresholds are configuration values, not hardware role assumptions.

## Host-testable implementation

- `firmware/services/thermal_service.h`
- `firmware/services/thermal_service.c`
- `firmware/tests/test_thermal_service.c`

System-level thermal shutdown tests are in:

- `firmware/tests/test_system_safety.c`
