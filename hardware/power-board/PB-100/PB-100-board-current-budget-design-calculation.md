# PB-100 Board Current Budget Design Calculation

Status: Schematic-freeze evidence, not frozen

This document converts the ADR-0008 current-budget decision into a numeric
pre-layout check for PB-100 Rev.1. It is not a PCB layout package. No PCB layout copper geometry,
placement, Gerbers, drills, pick-place, or `PB-100.kicad_pcb` work is
authorized by this calculation.

## Inputs

| Item | Value | Source |
|---|---:|---|
| Main harness fuse target | 50 A | ADR-0008 and garage connector/fuse plan |
| Board continuous-current target | 40 A | ADR-0008 and PB-100 capability manifest |
| Default configuration total-current limit | 40 A | `firmware/configs/config-example.json` |
| Total-current telemetry range | 0-60 A | `PB-100-current-telemetry-map.csv` |
| Total-current shunt candidate | 0.5 mΩ four-terminal AEC-Q200 class | `PB-100-input-power-design-values.csv` |
| Summed output current limits | 82 A | PB-100 capability manifest |
| Reverse-FET thermal multiplier | 2.0 × room-temperature Rds(on) | `PB-100-thermal-estimates.csv` |

The 82 A summed output limit is intentionally oversubscribed. The board is not
sized for simultaneous maximum output current. Configuration stays separate from firmware,
and the firmware-visible board budget remains the controlling limit.

## Path Under Review

The current path for the board budget is:

```text
Battery positive
  -> near-battery 50 A main fuse
  -> garage-installed high-current harness entry
  -> VBAT_RAW
  -> Q1 reverse-protection MOSFET path
  -> VBAT_REV_PROT
  -> 0.5 mΩ four-terminal total-current shunt
  -> VBAT_PROT
  -> per-output fuse and high-side switch distribution
```

The sequence keeps total-current telemetry downstream of reverse-polarity
protection and upstream of output distribution. The shunt must use Kelvin sense
routing; a two-terminal sense shortcut is not acceptable for schematic freeze.

## Shunt Calculation

Equations:

- `Vshunt = I * Rshunt`
- `Pshunt = I^2 * Rshunt`
- `Rshunt = 0.5 mΩ`

| Current | Shunt voltage | Shunt dissipation | Release meaning |
|---:|---:|---:|---|
| 40 A | 20 mV at 40 A | 0.8 W at 40 A | Normal board continuous-current budget point |
| 50 A | 25 mV at 50 A | 1.25 W at 50 A | Main-fuse class review point |
| 60 A | 30 mV at 60 A | 1.8 W at 60 A | Telemetry full-range review point |

Schematic freeze must keep the 0.5 mΩ four-terminal package, Kelvin connection,
input-filter values, monitor range, and calibration plan aligned with the 40 A
budget and 0-60 A telemetry range.

## Reverse-Protection MOSFET Calculation

Equation:

- `Pfet = I^2 * Rds(on) * 2.0`

| Candidate path | Package class | Rds(on) basis | 40 A dissipation | 50 A dissipation | 60 A dissipation | Release note |
|---|---|---:|---:|---:|---:|---|
| `IAUTN06S5N008ATMA1` | TOLL / PG-HSOF-8-1 | 0.76 mΩ | 2.43 W | 3.80 W | 5.47 W | Preferred only if TVS overshoot and factory assembly review pass |
| `BUK7S1R2-80M` | 80 V LFPAK88 | 1.2 mΩ | 3.84 W | 6.00 W | 8.64 W | Higher-voltage alternate with tighter thermal margin |
| dual `SIDR626LDP` | dual PowerPAK fallback | 2.1 mΩ per FET at half current | 1.68 W per FET / 3.36 W total | 2.63 W per FET / 5.25 W total | 3.78 W per FET / 7.56 W total | Requires current-sharing, fuse-energy, and copper review |

These values are conduction-only review numbers. They do not close transient
surge, package-to-board thermal resistance, copper spreading, enclosure
temperature, or fuse-energy behavior.

## Copper And Connector Boundary

Copper resistance is not locked here because layout is blocked. The pre-layout
loss check for any future proposed high-current copper segment is:

- `Pcopper = I^2 * Rcopper`
- Every 1 mΩ in the protected high-current path dissipates 1.6 W at 40 A.
- Every 1 mΩ in the protected high-current path dissipates 2.5 W at 50 A.
- Every 1 mΩ in the protected high-current path dissipates 3.6 W at 60 A.

Before schematic freeze can close PBREL-002, the release packet must still
review connector derating, battery-input wire gauge, shunt package heating,
Q1 package thermal path, protected-rail distribution, and bench telemetry
calibration.

## Freeze Requirements

- Keep the 50 A main fuse target in the garage-installed harness.
- Keep the 40 A board continuous-current target and 40 A default configuration
  limit.
- Keep total-current telemetry independent of summed per-output IMON.
- Keep the total-current shunt four-terminal with Kelvin sense.
- Keep Q1 package and alternate paths visible until the 40 A thermal review
  closes.
- Keep `PB-100.kicad_pcb` absent and block all layout/manufacturing output until
  the schematic freeze checklist closes.
