# Final Readiness

Status: In progress  
Last updated: 2026-07-10

This document defines what “ready” means for the current repository state. It
does not authorize PB-100 PCB layout.

## Automated gate

Run from the repository root:

```bash
make check
```

Current coverage:

- PB-100 CSV and KiCad scaffold validation.
- Optional PB-100 KiCad schematic ERC and netlist export when `kicad-cli` is
  installed.
- PB-100 KiCad role-token guard for generic `OUT1`..`OUT10` naming.
- PB-100 layout/manufacturing artifact blocker.
- Firmware config JSON/schema validation.
- Firmware host-test suite.
- Firmware hardware-capability, config-store, config-update, and runtime-boot
  startup safety validation.

## Current readiness

| Area | Status | Notes |
|---|---|---|
| Architecture v1.0 | Ready | Frozen by ADR; PB-100 requirement changes still need ADR |
| PB-100 requirements | Ready for schematic planning | Baseline is frozen; schematic freeze remains open |
| PB-100 KiCad scaffold | Review-ready scaffold | Schematic ERC and netlist export pass locally with KiCad 10.0.4 |
| PB-100 PCB/layout | Blocked | Layout, Gerber, drill, placement, and manufacturing zips are blocked |
| Firmware safety core | Host-test ready | Output, battery, thermal, CAN, telemetry, events, logging, config, runtime boot, CAN-to-rule bridge, ambient-light rule conditions, ordered rule sets, multi-action rule compilation, rule runtime, and rule paths covered |
| Configuration format | Host-test ready | JSON schema, rule grammar, rule-action mapping, PB-100 capability manifest, compiled capability baseline, config store, config update, and examples are validated |
| Production package | Draft | BOMs and component families need final sourcing and schematic evidence |

## Required before schematic freeze

- Replace abstract KiCad block symbols with final schematic symbols.
- Select final critical MPNs and at least two alternatives for each critical
  component family.
- Recheck JLCPCB/PCBWay assembly availability and package suitability.
- Resolve the TVS active-MPN blocker: MCC `SM8S33A` is EOL evidence only and
  Vishay `SM8S33AHE3_A/I` is NFD evidence only, so schematic freeze must select
  `SM8S33AHM3/I` or an equivalent active load-dump TVS and validate clamp
  margin.
- TVS/load-dump margin now has a downstream voltage-class trace for the active
  `SM8S33AHM3/I` branch and its 53.3 V clamp point; schematic freeze must still
  close 60 V overshoot margin, DO-218AC assembly handling, and any lower-clamp
  future path through a review or ADR.
- OUT5, OUT8, and OUT9 now have a low-current baseline trace enforcing the
  ADR-0011 external-controller plus external 60 V MOSFET architecture and
  blocking any direct 40 V smart-switch rail without a future ADR.
- OUT2 and medium-current outputs now have a baseline trace tying their fuse
  classes, configured current limits, TPS48110 external-MOSFET architecture,
  telemetry nets, and SOA/fuse/inductive-clamp freeze blockers together.
- Current telemetry now has a trace tying per-output IMON ranges, total
  `IIN_SENSE`, 0.5 mΩ shunt measurement, 40 A budget enforcement, and
  stale-telemetry safe-off behavior together.
- Factory-vs-garage assembly ownership now has a dedicated trace for critical
  PB-100 symbol keys; schematic freeze must still recheck JLCPCB/PCBWay
  assembly class, distributor continuity, garage connector derating, crimp
  tooling, and service access.
- Thermal telemetry now has a TDK `NTCGS103JF103FT8`-class 10 kΩ 150 °C
  AEC-Q200 NTC candidate for all three thermal points; schematic freeze must
  still close divider values, ADC scaling, placement, assembly class, and
  calibration.
- JPB1 board-to-board planning now has a Hirose `FX18-100P-0.8SV10` plus
  `FX18-100S-0.8SV20` candidate pair; schematic freeze must still close stack
  height, footprint drawing, vibration retention, assembly handling, and LB-100
  MCU resource binding.
- Q1 input reverse MOSFET pin evidence is captured from the Infineon
  `IAUTN06S5N008` data sheet; schematic freeze must still close TOLL footprint,
  40 A copper/thermal review, assembly handling, and gate clamp behavior.
- The PB-100 board-current budget now has a cross-artifact trace tying the
  50 A main fuse target, 40 A board/configuration limit, 0-60 A total-current
  telemetry range, and 0.5 mΩ shunt operating point together; schematic freeze
  must still close connector derating, shunt copper, calibration, and thermal
  evidence.
- Close PB-100 CAN1 TX-disable schematic evidence using the `JP_CAN1`
  DNP/open link plus `U_CAN1` default-disabled/readback contract.
- Close current and thermal telemetry scaling, filtering, and calibration notes.
- Close OUT2 SOA extraction and input reverse-protection thermal review.
- Synchronize factory and garage BOM drafts with final selections.
- Run `make check` with local `kicad-cli` available, zero ERC violations, and a
  successful KiCad S-expression netlist export.

## Required before PCB layout

- `hardware/power-board/PB-100/PB-100-schematic-freeze-checklist.md` status
  changed to closed with evidence for every conditional gate.
- No open ADR requirement change touching PB-100 output count, protection model,
  role mapping, current budget, or CAN1 safety behavior.
- Final schematic review packet archived in the repository.

## Required before prototype bring-up

- PB-100 layout, fabrication outputs, assembly outputs, and inspection files.
- Bench test procedure for first power, current telemetry, thermal telemetry,
  short-circuit handling, CAN1 listen-only behavior, and output load tests.
- Firmware hardware-abstraction layer for the selected LB-100 MCU and PB-100
  telemetry paths.
- Reference vehicle harness and connector assembly notes.

## No-go conditions

- Any `PB-100.kicad_pcb` or manufacturing output before schematic freeze.
- Any vehicle CAN1 TX enable path without a new ADR and explicit hardware action.
- Any hard-coded accessory role to physical output mapping in hardware or
  firmware.
- Any firmware path that bypasses Output Manager for physical output state.
