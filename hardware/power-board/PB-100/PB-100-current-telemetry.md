# PB-100 Current Telemetry Strategy

Status: Schematic-planning input

This document defines how PB-100 current measurements are mapped to LB-100 for
schematic planning. It does not freeze resistor values, ADC channels, or final
current-monitor MPNs.

## Decision

Use the TPS48110-class high-side controller `IMON` output as the primary
per-output current telemetry source for all 10 Rev.1 outputs.

Use a dedicated input shunt monitor for total board input current. The preferred
family remains INA228/INA229 or INA226-class digital current monitors, with an
analog `IIN_SENSE` path retained for fast firmware budget checks if the final
monitor topology requires it.

## Measurement map

Detailed map CSV:
`hardware/power-board/PB-100/PB-100-current-telemetry-map.csv`.

The map keeps output hardware generic. Reference vehicle roles are not encoded
in telemetry names.

## Range targets

| Measurement class | Calibrated range target | Rationale |
|---|---:|---|
| OUT2 high-current channel | 0-30 A | Covers 18 A configured limit and fault margin |
| OUT1 medium 12 A channel | 0-20 A | Covers 12 A configured limit and fuse margin |
| 8 A medium channels | 0-15 A | Covers 8 A configured limits and fuse margin |
| 4 A low-current channels | 0-8 A | Covers 4 A configured limits and fuse margin |
| Total input current | 0-60 A | Covers 40 A budget and 50 A main fuse target |

Pulse and short-circuit validation can use oscilloscope/test-point capture in
addition to firmware telemetry. Firmware current-budget enforcement must use the
total input current measurement, not the sum of output estimates alone.

## Schematic requirements

- Route `OUT1_IMON` through `OUT10_IMON` to LB-100 ADC-capable pins.
- Scale every analog current signal to stay inside the `LB_3V3_IO` ADC domain.
- Add RC filtering that preserves budget-control dynamics without hiding faults.
- Keep `IIN_SENSE` available for fast total-current measurement or analog
  fallback.
- Reserve `PB_I2C_SCL`, `PB_I2C_SDA`, and `PB_I2C_INT` for a digital input
  current monitor or future PB-side monitor.
- Provide calibration constants through configuration, not firmware constants.
- Treat missing, saturated, or implausible telemetry as a safe fault.

## Evidence links

- TI TPS4811-Q1 product page: https://www.ti.com/product/TPS4811-Q1
- TI TPS4811-Q1 data sheet: https://www.ti.com/lit/ds/symlink/tps4811-q1.pdf
- INA226 LCSC candidate: https://www.lcsc.com/product-detail/current-sense-amplifiers_texas-instruments-ina226aidgst_C2653870.html
