# Final Readiness

Status: In progress  
Last updated: 2026-07-16

This document defines what “ready” means for the current repository state. It
does not authorize PB-100 PCB layout.

## Automated gate

Run from the repository root:

```bash
make check
```

For board-order status, run:

```bash
make pb100-release-status
```

For a release job that must fail while PB-100 is not printable, run:

```bash
make pb100-release-gate
```

Current coverage:

- PB-100 CSV and KiCad scaffold validation.
- Required PB-100 KiCad schematic ERC and netlist export with `kicad-cli`
  10.0.4.
- PB-100 sheet-placeholder blocker plus minimum exported netlist thresholds of
  20 components and 20 electrical nets.
- PB-100 KiCad role-token guard for generic `OUT1`..`OUT10` naming.
- PB-100 layout/manufacturing artifact blocker.
- Firmware config JSON/schema validation.
- Firmware host-test suite.
- Firmware hardware-capability, config-store, config-update, and runtime-boot
  startup safety validation.
- PB-100 board-print release-status reporting from the schematic-freeze
  checklist, board-release blocker register, KiCad PCB presence, and
  manufacturing output presence.

## Current readiness

| Area | Status | Notes |
|---|---|---|
| Architecture v1.0 | Ready | Frozen by ADR; PB-100 requirement changes still need ADR |
| PB-100 requirements | Ready for schematic planning | Baseline is frozen; schematic freeze remains open |
| PB-100 KiCad scaffold | Preliminary capture | Child sheets now contain ERC-clean preliminary capture content and exported netlist coverage; schematic freeze remains open |
| PB-100 PCB/layout | Blocked | Layout, Gerber, drill, placement, and manufacturing zips are blocked by the board-release blocker register |
| Firmware safety core | Host-test ready | Output, delayed battery cutoff, runtime load shedding, thermal derate/cutoff, CAN, telemetry, events, logging, config, runtime boot, CAN-to-rule bridge, ambient-light rule conditions, ordered rule sets, multi-action rule compilation, rule runtime, and rule paths covered |
| Configuration format | Host-test ready | JSON schema, rule grammar, rule-action mapping, PB-100 capability manifest, compiled capability baseline, config store, config update, and examples are validated |
| Production package | Draft | BOMs and component families need final sourcing and schematic evidence |

## Required before schematic freeze

- Replace preliminary abstract/class KiCad instances with final schematic
  symbols, reviewed electrical pin types, values, footprints, and MPN-specific
  package evidence.
- Close every row in
  `hardware/power-board/PB-100/PB-100-board-release-blocker-register.csv`; any
  remaining row blocks PCB layout and board release.
- Keep all child sheets free of `sheet-placeholder` markers, ERC-clean, and
  covered by exported KiCad netlist component/net thresholds.
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
- TVS/load-dump freeze review now ties the active SM8S33AHM3/I branch,
  100 V pass-with-margin paths, 60 V overshoot dependencies, 40 V smart-switch
  ADR boundary, sourcing gate, and no-layout boundary into
  `hardware/power-board/PB-100/PB-100-tvs-load-dump-freeze-review.csv`.
- TVS/load-dump overshoot closure now has
  `hardware/power-board/PB-100/PB-100-tvs-overshoot-escape-checklist.csv`,
  which keeps the active HM3 MPN evidence, 60 V overshoot acceptance criteria,
  80 V MOSFET escape path, 100 V downstream default, and no-layout boundary in
  one machine-checked artifact.
- MOSFET voltage-margin review now makes the 80 V review escape path explicit
  for 60 V output and input-reverse MOSFET paths unless overshoot evidence
  accepts the active TVS clamp margin.
- OUT5, OUT8, and OUT9 now have a low-current baseline trace enforcing the
  ADR-0011 external-controller plus external 60 V MOSFET architecture and
  blocking any direct 40 V smart-switch rail without a future ADR.
- OUT2 and medium-current outputs now have a baseline trace tying their fuse
  classes, configured current limits, TPS48110 external-MOSFET architecture,
  telemetry nets, and SOA/fuse/inductive-clamp freeze blockers together.
- High/medium output freeze review now ties TPS48110 baseline, OUT2 SOA,
  medium fuse paths, gate-drive default-off behavior, sense/telemetry,
  thresholds, clamp strategy, thermal review, and no-layout boundary into
  `hardware/power-board/PB-100/PB-100-high-medium-output-freeze-review.csv`.
- Low-current output freeze review now ties OUT5/OUT8/OUT9 5 A/4 A class,
  ADR-0011 external-controller baseline, no direct 40 V smart-switch rail,
  gate-drive defaults, telemetry, fault timing, clamp strategy, sourcing,
  and configuration separation into
  `hardware/power-board/PB-100/PB-100-low-current-output-freeze-review.csv`.
- Output-stage value freeze checklist now ties controller baseline, OUT2
  SOA/fuse energy, medium fuse paths, low-current ADR-0011 boundary,
  threshold/timer networks, gate default-off behavior, sense/ADC scaling,
  inductive clamp, MOSFET voltage margin, and no-layout boundary into
  `hardware/power-board/PB-100/PB-100-output-stage-value-freeze-checklist.csv`.
- Current telemetry now has a trace tying per-output IMON ranges, total
  `IIN_SENSE`, 0.5 mΩ shunt measurement, 40 A budget enforcement, and
  stale-telemetry safe-off behavior together.
- Current telemetry freeze review now ties the 0.5 mΩ shunt range,
  INA228-class monitor headroom, Kelvin sense, ADC/I2C ownership, calibration
  configuration, stale-telemetry safe faults, and bench validation IDs into
  `hardware/power-board/PB-100/PB-100-current-telemetry-freeze-review.csv`.
- Current telemetry candidate values now document the 0.5 mΩ shunt operating
  points, INA228-class ±40.96 mV range, candidate `0x40` address straps,
  LB-owned pull-up boundary, input/VBUS filters, and calibration boundary in
  `hardware/power-board/PB-100/PB-100-current-telemetry-design-calculation.md`.
- Total-current and per-output IMON calibration now have a firmware
  configuration contract in `firmware/configs/config-example.json`,
  `firmware/configs/svc-config.schema.json`, and `firmware/core/svc_config.h`;
  ADC scaling and bench calibration evidence remain schematic-freeze blockers.
- Thermal telemetry now has a trace tying `TEMP_PCB`, `TEMP_PWR_A`, and
  `TEMP_PWR_B` to the TDK NTC candidate, default 85/105/75 °C thresholds,
  configuration-owned calibration, and firmware thermal fail-safe behavior.
- Thermal telemetry freeze review now ties NTC sensor class, divider/ADC
  scaling, placement zones, threshold ownership, stale-telemetry cutoff,
  assembly alternates, and bench validation into
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-freeze-review.csv`.
- Logic power now has a trace tying the LM5164-Q1-class 100 V 1 A default,
  LM5013-Q1-class 100 V fallback, protected `PB_5V_OUT`, `PB_PWR_GOOD`, and
  rail-invalid default-off behavior together.
- Logic power freeze review now ties LM5164/LM5013/TPS54360B regulator
  boundaries, protected `VBAT_PROT` sequencing, 1000 mA `PB_5V_OUT` budget,
  UVLO safe-off behavior, PGOOD, inductor/capacitor classes, sourcing, and
  no-layout boundary into
  `hardware/power-board/PB-100/PB-100-logic-power-freeze-review.csv`.
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
  height, footprint drawing, vibration retention, assembly handling, and exact
  LB-100 MCU pin binding.
- JPB1 now has a B2B interface trace and LB-100 resource-class binding tying
  the FX18 candidate pair, 100-pin map, output controls/fault/current telemetry,
  board telemetry, CAN1 safety crossing, and exact MCU pin-binding blockers
  together.
- B2B/LB-100 pin binding now has a resource-budget precheck for STM32H563
  LQFP-100 schematic review, covering 10 PWM-capable controls, 16 ADC-class
  measurements, fault/wake inputs, `PB_I2C`, CAN1 safety, and reserved
  expansion without assigning exact STM32 pins.
- B2B/LB-100 pin binding now has an audit checklist covering the exact
  STM32H563 LQFP-100 pinout audit, 16 ADC-capable measurement inputs or reviewed
  mux strategy, output default-low PWM routing, CAN1 DNP/open crossing, FX18
  footprint drawing, stack height, vibration retention, assembly handling, and
  no-layout boundary in
  `hardware/power-board/PB-100/PB-100-b2b-lb100-pin-audit-checklist.csv`.
- Q1 input reverse MOSFET pin evidence is captured from the Infineon
  `IAUTN06S5N008` data sheet; schematic freeze must still close TOLL footprint,
  40 A copper/thermal review, assembly handling, and gate clamp behavior.
- Q1 input reverse planning now has a package/thermal trace tying
  `IAUTN06S5N008ATMA1`, `BUK7S1R2-80M`, dual `SIDR626LDP`, the 40 A board
  budget, shunt measurement boundary, and assembly-source blockers together.
- Q1 input reverse freeze review now ties LM74700 default-off behavior,
  TOLL/LFPAK/PowerPAK alternates, protected measurement sequence, HM3 TVS
  dependency, sourcing gate, and no-layout boundary into
  `hardware/power-board/PB-100/PB-100-input-reverse-freeze-review.csv`.
- Q1 input reverse freeze checklist now ties gate clamp/discharge timing,
  TOLL/LFPAK/PowerPAK package paths, protected measurement sequence, 40 A
  thermal/copper/SOA audit, assembly sourcing, and no-layout boundary into
  `hardware/power-board/PB-100/PB-100-input-reverse-q1-freeze-checklist.csv`.
- The PB-100 board-current budget now has a cross-artifact trace tying the
  50 A main fuse target, 40 A board/configuration limit, 0-60 A total-current
  telemetry range, and 0.5 mΩ shunt operating point together; schematic freeze
  must still close connector derating, shunt copper, calibration, and thermal
  evidence.
- The 40 A board-current freeze review now ties connector derating, Q1 thermal
  path, shunt Kelvin path, protected copper distribution, firmware config,
  telemetry enforcement, and the no-layout boundary into
  `hardware/power-board/PB-100/PB-100-board-current-budget-freeze-review.csv`.
- The board-current design calculation now computes the 0.5 mΩ shunt operating
  points, Q1 candidate dissipation, and copper loss boundary for the 50 A fuse,
  40 A continuous budget, and 0-60 A telemetry range in
  `hardware/power-board/PB-100/PB-100-board-current-budget-design-calculation.md`.
- Close PB-100 CAN1 TX-disable schematic evidence using the `JP_CAN1`
  DNP/open link plus `U_CAN1` default-disabled/readback contract.
- CAN1 TX-disable now has a trace tying `JP_CAN1`, `U_CAN1`,
  `CAN1_TX_ROUTE`, `CAN1_TX_DISABLED_STATUS`, firmware listen-only behavior,
  DNP BOM ownership, the production DNP review, and the future-ADR
  hardware-action boundary together.
- CAN1 TX-disable candidate values now document the 0 Ω DNP/open link,
  `SN74LVC1G125-Q1`-class default-disabled gate, 47 kΩ pulls, physical
  `OE`-node status readback, and reset/unpowered bench checks in
  `hardware/power-board/PB-100/PB-100-can1-tx-disable-design-calculation.md`.
- CAN1 reset and DNP bench evidence now has a checklist covering LB-100 reset,
  LB-100 unpowered, production DNP/open inspection, physical disabled-status
  readback, RX listen-only independence, and future-ADR hardware-action checks
  in `hardware/power-board/PB-100/PB-100-can1-reset-bench-checklist.csv`.
- Close current and thermal telemetry scaling, filtering, and calibration notes.
- Close OUT2 SOA extraction and input reverse-protection thermal review.
- Synchronize factory and garage BOM drafts with final selections.
- Keep `make check` passing with local `kicad-cli` available, zero ERC
  violations, and a successful KiCad S-expression netlist export.
- Logic power now has candidate LM5164 values in
  `hardware/power-board/PB-100/PB-100-logic-power-design-calculation.md`, but
  those values remain not final until load budget, sourcing, EMI, and stability
  review close.
- LB-100 now has a `PB_5V_OUT` load-budget precheck with a 500 mA sustained
  allocation; exceeding it keeps the PB-100 LM5013-Q1-class fallback active.
- Thermal telemetry now has candidate NTC divider values in
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-design-calculation.md`,
  but placement, ADC settling, calibration, and assembly review remain open.
- Thermal telemetry divider calibration now has a firmware configuration
  contract in `firmware/configs/config-example.json`,
  `firmware/configs/svc-config.schema.json`, and `firmware/core/svc_config.h`;
  ADC settling, placement, self-heating, sourcing, and bench calibration remain
  schematic-freeze blockers.

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
