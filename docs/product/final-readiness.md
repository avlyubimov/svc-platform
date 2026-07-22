# Final Readiness

Status: In progress  
Last updated: 2026-07-22

This document defines what “ready” means for the current repository state. It
authorizes controlled PB-100 and LB-100 Rev.1 EVT board import/layout and
continued FB-100 EVT routing. It does not authorize fabrication/assembly
outputs for any board.

All three boards use the ADR-0020 lifecycle: `EVT-LAYOUT-AUTHORIZED`,
`EVT-FAB-REVIEW`, `EVT-FAB-AUTHORIZED`, `BENCH-VALIDATION`,
`MOTORCYCLE-VALIDATION`, `PRODUCTION-BLOCKED`, and `PRODUCTION-RELEASE`. Rev.1 remains
`NOT FOR PRODUCTION`; production and general field use remain `NO-GO` until
bench and motorcycle evidence is incorporated into reviewed Rev.2.

Current top- and bottom-side PCB review renders are tracked in
[`docs/assets/pcb-renders`](../assets/pcb-renders/README.md). They are
documentation-only snapshots of the current EVT layout and do not change any
board-order gate.

## Automated gate

Run from the repository root:

```bash
make check
```

For board-order status, run:

```bash
make board-order-status
```

For PB-100-only detail, run:

```bash
make pb100-release-status
```

For a release job that must fail while any board is not printable, run:

```bash
make board-order-gate
```

For a PB-100-only release job that must fail while PB-100 is not printable, run:

```bash
make pb100-release-gate
```

Current coverage:

- PB-100 validation is decomposed under `tools/pb100_validation/` by KiCad,
  symbols, release gates, power, CAN, telemetry, sourcing, protection,
  interface, and review-packet ownership; `tools/validate_pb100.py` remains the
  stable CLI entrypoint.
- PB-100 CSV and preliminary KiCad capture validation.
- Required PB-100 KiCad schematic ERC and netlist export with `kicad-cli`
  10.0.4.
- PB-100 sheet-placeholder blocker plus minimum exported netlist thresholds of
  20 components and 20 electrical nets.
- PB-100 KiCad role-token guard for generic `OUT1`..`OUT10` naming.
- PB-100 layout/manufacturing artifact blocker.
- Three-board board-order gate for PB-100, LB-100, and FB-100.
- Deterministic LB-100 and FB-100 schematic generation plus focused exported-
  netlist topology, symbol-to-footprint pad-contract, and ERC validation under
  `tools/board_schematic_validation/`.
- Deterministic FB-100 connectivity-routing generation plus KiCad DRC,
  schematic-parity, mounting-hole, route-manifest, and zero-unconnected validation in
  `tools/validate_fb100_layout.py`.
- LB-100 and FB-100 baseline freeze manifests and release-blocker registers.
- Firmware config JSON/schema validation.
- Firmware host-test suite.
- Firmware hardware-capability, config-store, config-update, and runtime-boot
  startup safety validation.
- PB-100 board-print release-status reporting from the schematic-freeze
  checklist, board-release blocker register, KiCad PCB presence, and
  manufacturing output presence.
- PB-100 staged-release consistency across the unified seven stages, with
  PBREL-007 blocking only production qualification.
- Generated LB-100/FB-100 powered-off evidence recalculating E73 leakage and
  USB VBUS threshold/removal margins in CI.

## Current readiness

| Area | Status | Notes |
|---|---|---|
| Architecture v1.0 | Ready | Frozen by ADR; PB-100 requirement changes still need ADR |
| PB-100 requirements | Ready for controlled schematic completion | Baseline plus ADR-0016/ADR-0018 active-cutoff and passive-thermal requirements are frozen; schematic freeze remains open |
| PB-100 KiCad scaffold | Preliminary capture | Child sheets now contain ERC-clean preliminary capture content and exported netlist coverage; schematic freeze remains open |
| PB-100 PCB/layout | EVT-LAYOUT-AUTHORIZED | There is 1 active blocker: `PBREL-007`; ADR-0020 makes it a production-only blocker. The controlled four-layer 150 mm x 90 mm partial import places all 33 currently footprint-bound schematic components plus eight holes. The complete CAN1 safety island and ADR-0021 protected three-wire FOG cable entry are routed (110 segments, 14 vias), with no shorts/crossings/clearance findings. `SW_COMMON` selects default dry-contact GND or DNP fused 12 V common without simultaneous assembly, and D_FOG1 is adjacent to the PB entry. It is explicitly not fabricable: 46 missing footprints, six U1 parity findings, 127 unconnected items, all 40 A/power copper and the complete diagnostic population remain open. The aggregate authorization remains `EVT-LAYOUT-AUTHORIZED`. Q2-C100 is paused and optional. `EVT-FAB-AUTHORIZED` still requires the separate PB EVT-fab checklist, zero DRC/unconnected/parity findings, routed 40 A electrothermal and clamp-loop estimates, connector fit, DFM and laboratory safety evidence. Production remains `NO-GO` |
| LB-100 requirements | Frozen | Baseline is frozen by ADR-0014 and the schematic freeze is Closed |
| LB-100 KiCad schematic | Reviewed | Deterministic 104-component, 199-net, footprint-bound capture adds five E73 SWDIO/SWDCLK/reset/target-reference/GND recovery pads and independent PA8 `FOG_A_SW_IN` and PA9 `FOG_B_SW_IN` secondary-conditioning chains with mutually exclusive dry-contact/12 V populations while ADR-0021 moves primary cable-entry suppression to PB-100; typed IC pins/ERC, sourced and decoupled ADC_REF, one-point AGND return, digital USB VBUS detection, direct STM32-to-LTC3212 drive, back-power-safe sensors, and E73 UART/reset isolation remain; exported-netlist audit and ERC pass with only the two reviewed cross-board USB CC single-pin warnings |
| LB-100 PCB/layout | EVT-LAYOUT-AUTHORIZED | There are 0 active blockers in the release register (0 active LBREL blockers), but EVT-FAB gates remain open. The controlled four-layer 100 mm x 70 mm board places all 104 schematic components plus eight holes and currently carries 1,844 deterministic segments and 188 vias. All five E73 recovery pads are routed. Four GND-zone intents and an exact F.Cu/In1.Cu/In2.Cu/B.Cu antenna rule area now forbid tracks, vias, pads and pours beyond the E73 terminal edge. Source DRC reports 63 open connections before refill and 53 after refill; the refilled result has no shorts, crossings, copper-clearance or keepout violations. VEML7700 remains on LB Rev.1 and does not block EVT; external optical placement is production/Rev.2. Critical-interface fan-out, ADC/I2C/fog/USB/SI/RF review and footprint/silkscreen cleanup remain open; manufacturing outputs remain blocked |
| FB-100 requirements | Frozen | Baseline is frozen by ADR-0014 and the schematic freeze is Closed |
| FB-100 KiCad schematic | Reviewed | Deterministic 44-component, 46-net, footprint-bound capture covers USB-C/ESD/no-back-power VBUS presence with R13 3.9k current limit, R14 15k defined pulldown and C1 100nF, JFB1, ten role-free indicators, direct one-wire RGB, service/reset buttons, and DNP OLED; exported-netlist audit and ERC pass with zero findings |
| FB-100 PCB/layout | EVT-LAYOUT-AUTHORIZED | There are 0 active blockers in the release register (0 active FBREL blockers), but EVT-FAB gates remain open. The controlled 80 mm x 35 mm board contains all 44 frozen schematic footprints plus four mounting holes and a deterministic connectivity-complete route with 457 segments, 48 vias and four GND zones. Refilled KiCad DRC and unconnected counts are both zero. The selected 1.6 mm/3313 stack model, 0.154 mm width, 0.2032 mm gap, 0.0151 mm skew, approximately 91.5 ohm analytical precheck and GND transition-via proximity are validator-covered. Supplier field-solver confirmation, physical JFB1 cable/latch orientation, enclosure/USB shell fit, optional FOG-button fit and assembly DFM remain open. No Gerber, drill, BOM/CPL, pick-place, manufacturing ZIP, or PCBA order exists |
| Firmware safety core | Host-test ready | Output, overflow-safe delayed battery cutoff, runtime load shedding, stale-current safe-off, thermal derate/cutoff, CAN dropped-edge retry, telemetry, events, saturating diagnostic counters, config, runtime boot, CAN-to-rule bridge, ambient-light rule conditions, ordered rule sets, multi-action rule compilation, rule runtime, and rule paths are covered. CAN1 persistence uses a separate lock-free ISR-to-logger queue plus 44-byte v2 CRC records with 64-bit microsecond timestamps, identity-bearing 128-byte session headers, independent sync/close, card restart/reopen, directory-based latest-session recovery, preallocation, rotation and torn-tail truncation; the STM32 SDMMC/SPI FatFs `diskio` binding remains mandatory before motorcycle logging tests |
| Configuration format | Host-test ready | JSON schema, canonical rule grammar, rule-action mapping, buffer-atomic rule compilation, PB-100 capability manifest, compiled capability baseline, config store reserved/sequence-wrap handling, config update, and examples are validated |
| Production package | Draft | `production/board-order/three_board_jlcpcb_order_readiness.csv` tracks all three boards as NO-GO until their layout, fabrication, review, and assembly-output gates close |

## Required during EVT layout and before EVT fabrication

- Replace preliminary abstract/class KiCad instances with final schematic
  symbols, reviewed electrical pin types, values, footprints, and MPN-specific
  package evidence.
- Close every pre-layout stage in
  `hardware/power-board/PB-100/PB-100-staged-release-readiness.csv`; overall
  PBREL rows may remain active for post-layout or prototype evidence without
  blocking controlled layout.
- Keep `hardware/power-board/PB-100/PB-100-board-release-local-evidence-closeout.csv`
  synchronized with the latest `make check` result so locally verified
  firmware/schematic evidence is not confused with external bench or sourcing
  closeout.
- Keep all child sheets free of `sheet-placeholder` markers, ERC-clean, and
  covered by exported KiCad netlist component/net thresholds.
- Select final critical MPNs and at least two alternatives for each critical
  component family.
- Recheck JLCPCB/PCBWay assembly availability and package suitability.
- The planning baseline selects `LM74930QRGERQ1` with 150 V
  `IAUTN15S6N025ATMA1` Q2 and protected-side 80 V
  `IAUT300N08S5N012ATMA2` Q1. `SM8S33AHM3/I` is retained DNP only.
- TVS/load-dump evidence now covers the ADR-0016 `79-101 V`, `0.5-4 ohm`, and
  `40-400 ms` envelope with current, energy, transient thermal impedance,
  tolerance, and self-heating calculations. Those rows preserve the rejected
  single-TVS failure; ADR-0018 instead selects hard cutoff at `48.99-54.89 V`.
- ADR-0020 establishes the unified seven-state lifecycle for all main boards.
  PBREL-007 remains Conditional only for production pending qualified
  maximum-bound Q2 evidence; it does not block PB layout, five-board EVT
  fabrication after fab review, bench validation or motorcycle validation.
- Infineon email response `IFX-260721-2228076` / `CRM0032570008656` supplied no
  technical trajectory, model, or FAE statement. It is recorded as
  `RECEIVED NON-QUALIFYING`; the request must be rerouted through MyCases in
  parallel. The replacement audit found no automotive 150 V candidate whose
  public evidence closes Q2Q-010 through Q2Q-015, so
  `IAUTN15S6N025ATMA1` is retained for a dedicated empirical program: five
  characterization DUTs followed by 30 new qualification DUTs from at least
  three lots. Q2-C100 now commits the exact-device/controller schematic,
  preliminary four-layer PCB, critical high-current and gate routing, BOM,
  variants and probe/safety boundaries. Its pad-to-pad routing is complete with
  zero unconnected items, and exact Molex board-interface kits plus Harwin
  board test points are selected. The open `FAB-REVIEW`, 2.0 mm header fit,
  rated instrument/probe, remaining fixture-source and safety gates prohibit
  fabrication and energized use.
  ADR-0019 pauses further Q2-C100 work and retains the routed coupon only as a
  diagnostic option. It does not block PB-100 Rev.1 EVT layout or a separately
  reviewed five-board EVT package.
- Load-dump freeze review now ties LM74930-Q1 hard cutoff, selected 150 V Q2,
  protected-side 80 V Q1, rejected single-TVS history, 40 V smart-switch ADR boundary, sourcing gate, and
  no-layout boundary into
  `hardware/power-board/PB-100/PB-100-tvs-load-dump-freeze-review.csv`.
- TVS/load-dump overshoot closure now has
  `hardware/power-board/PB-100/PB-100-tvs-overshoot-escape-checklist.csv`,
  which keeps the active HM3 MPN evidence, 60 V MOSFET exclusion, selected
  80 V stress validation, 100 V downstream default, and no-layout boundary in
  one machine-checked artifact.
- TVS overshoot validation precheck now ties the active HM3 clamp source,
  selected 80 V overshoot method, measurement/simulation setup, factory
  alternatives, and no-layout boundary into
  `hardware/power-board/PB-100/PB-100-tvs-overshoot-validation-precheck.csv`.
- TVS overshoot closeout precheck now ties active source, overshoot method,
  rejected 60 V path exclusion, selected 80 V baseline, 100 V downstream
  defaults, 40 V ADR boundary, schematic-value dependencies, sourcing,
  validation sync, and no-layout boundary to
  `hardware/power-board/PB-100/PB-100-tvs-overshoot-closeout-precheck.csv`.
- MOSFET voltage-margin review selects active/preferred
  `IAUT300N08S5N012ATMA2` 80 V TOLL for Q1 and Q101-Q110.
  `IAUT300N08S5N014ATMA1` is the controlled same-footprint alternative and
  `BUK7J2R4-80MX` is a non-drop-in LFPAK56E alternative; preliminary LFPAK88
  and former 60 V paths are rejected for Rev.1 assembly.
- OUT5, OUT8, and OUT9 now have a low-current baseline trace enforcing the
  ADR-0011 external-controller plus selected external 80 V MOSFET architecture
  and blocking any direct 40 V smart-switch rail without a future ADR.
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
- Output-stage value derivation precheck now ties TI TPS4811-Q1 datasheet
  equations and TPS48110Q1EVM reference positions to PB-100 high, medium, and
  low current value derivation in
  `hardware/power-board/PB-100/PB-100-output-stage-value-derivation-precheck.csv`.
- Output-stage closeout precheck now bridges source formulas, class maps,
  design-item completeness, thresholds/timers, bootstrap/default-off behavior,
  telemetry scaling, SOA/fuse/clamp evidence, low-current ADR-0011 boundary,
  instance synchronization, and no-layout boundary in
  `hardware/power-board/PB-100/PB-100-output-stage-closeout-precheck.csv`.
- Current telemetry now has a trace tying per-output IMON ranges, total
  `IIN_SENSE`, 0.5 mΩ shunt measurement, 40 A budget enforcement, and
  stale-telemetry safe-off behavior together.
- Current telemetry freeze review now ties the 0.5 mΩ shunt range,
  INA228-class monitor headroom, Kelvin sense, ADC/I2C ownership, calibration
  configuration, stale-telemetry safe faults, and post-prototype bench IDs into
  `hardware/power-board/PB-100/PB-100-current-telemetry-freeze-review.csv`.
- Current telemetry candidate values now document the 0.5 mΩ shunt operating
  points, INA228-class ±40.96 mV range, candidate `0x40` address straps,
  LB-owned pull-up boundary, input/VBUS filters, and calibration boundary in
  `hardware/power-board/PB-100/PB-100-current-telemetry-design-calculation.md`.
- Current telemetry value closure now has
  `hardware/power-board/PB-100/PB-100-current-telemetry-value-freeze-checklist.csv`,
  tying shunt range, monitor family, Kelvin/filter network, I2C ownership,
  alert behavior, VBUS stress, per-output IMON scaling, configuration
  calibration, stale safe-fault tests, sourcing, and no-layout boundary.
- Current telemetry value derivation precheck now ties shunt voltage/power
  formulas, INA228/INA229 monitor ranges, Kelvin/filter network, I2C ownership,
  VBUS stress, per-output IMON scaling, configuration calibration, bench
  safe-fault procedure, post-prototype validation, sourcing, and no-layout
  boundary into
  `hardware/power-board/PB-100/PB-100-current-telemetry-value-derivation-precheck.csv`.
- Current telemetry closeout precheck now bridges the shunt formulas, monitor
  family, Kelvin/filter network, I2C/interrupt ownership, protected VBUS
  stress, per-output IMON ADC scaling, configuration-owned calibration, bench
  safe-fault hooks, post-prototype evidence gate, sourcing/symbol
  synchronization, and no-layout boundary into
  `hardware/power-board/PB-100/PB-100-current-telemetry-closeout-precheck.csv`.
- Total-current and per-output IMON calibration now have a firmware
  configuration contract in `firmware/configs/config-example.json`,
  `firmware/configs/svc-config.schema.json`, and `firmware/core/svc_config.h`;
  ADC scaling and calibration hooks remain schematic-freeze blockers, while
  physical bench calibration is a post-prototype validation gate.
- Thermal telemetry now has a trace tying `TEMP_PCB`, `TEMP_PWR_A`, and
  `TEMP_PWR_B` to the TDK NTC candidate, default 85/105/75 °C thresholds,
  configuration-owned calibration, and firmware thermal fail-safe behavior.
- Thermal telemetry freeze review now ties NTC sensor class, divider/ADC
  scaling, placement zones, threshold ownership, stale-telemetry cutoff,
  assembly alternates, and post-prototype bench validation into
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-freeze-review.csv`.
- Thermal telemetry value closure now has
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-freeze-checklist.csv`,
  tying sensor class, placement zones, divider/ADC scaling, self-heating,
  ADC settling, configuration calibration, firmware fail-safe, bench procedure,
  post-prototype validation, sourcing, and no-layout boundary.
- Thermal telemetry value derivation precheck now ties the NTC source boundary,
  beta/divider formulas, self-heating estimate, ADC settling, placement zones,
  configuration calibration, firmware fail-safe, sourcing, and no-layout
  boundary into
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-derivation-precheck.csv`.
- Thermal telemetry closeout precheck now bridges the NTC source class, divider
  equations and values, placement zones, self-heating, ADC settling,
  configuration-owned calibration, firmware fail-safe behavior, bench
  validation, sourcing/symbol synchronization, and no-layout boundary into
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-closeout-precheck.csv`.
- Logic power now has a trace tying the LM5164-Q1-class 100 V 1 A default,
  LM5013-Q1-class 100 V fallback, protected `PB_5V_OUT`, `PB_PWR_GOOD`, and
  rail-invalid default-off behavior together.
- Logic power freeze review now ties LM5164/LM5013/TPS54360B regulator
  boundaries, protected `VBAT_PROT` sequencing, 1000 mA `PB_5V_OUT` budget,
  UVLO safe-off behavior, PGOOD, inductor/capacitor classes, sourcing, and
  no-layout boundary into
  `hardware/power-board/PB-100/PB-100-logic-power-freeze-review.csv`.
- Logic power value closure now has
  `hardware/power-board/PB-100/PB-100-logic-power-value-freeze-checklist.csv`,
  tying LM5164/LM5013 family selection, `PB_5V_OUT` budget, UVLO, RON,
  feedback, bootstrap, L1/COUT, `PB_PWR_GOOD`, switch-node EMI, sourcing, and
  no-layout boundaries into one machine-checked artifact.
- Logic power value derivation precheck now ties official TI buck-family source
  boundaries, `PB_5V_OUT` load budget, UVLO/RON/feedback formulas, bootstrap
  and PGOOD interface, magnetics/capacitor review, sourcing, and no-layout
  boundary into
  `hardware/power-board/PB-100/PB-100-logic-power-value-derivation-precheck.csv`.
- Logic power closeout precheck now ties regulator family source boundary,
  `PB_5V_OUT` budget, protected input/transient stress, UVLO/default-off,
  RON/feedback/bootstrap, inductor/COUT stability, PGOOD interface,
  switch-node EMI, sourcing, and no-layout boundary into
  `hardware/power-board/PB-100/PB-100-logic-power-closeout-precheck.csv`.
- Factory-vs-garage assembly ownership now has a dedicated trace for critical
  PB-100 symbol keys plus
  `hardware/power-board/PB-100/PB-100-factory-assembly-freeze-checklist.csv`;
  `hardware/power-board/PB-100/PB-100-factory-assembly-sourcing-precheck.csv`
  now ties factory-owned critical keys, BOM/evidence alignment, assembly-platform
  recheck, alternates, package handling, sourcing evidence, and no-layout
  boundary. `hardware/power-board/PB-100/PB-100-factory-assembly-closeout-precheck.csv`
  adds the closeout bridge for critical-key ownership, alternates,
  assembly-platform handling, inspection/rework evidence, BOM synchronization,
  and no-layout manufacturing boundary. Schematic freeze must still recheck
  JLCPCB/PCBWay exact suffixes, distributor continuity, garage connector
  derating, crimp tooling, and service access. The 2026-07-20
  `hardware/power-board/PB-100/PB-100-factory-assembly-platform-evidence.csv`
  refresh records PCBWay generic SMT process and sourcing-mode evidence; it
  does not lock package-specific handling, inspection/rework, or orderable
  suffixes.
- Garage install closure now has
  `hardware/power-board/PB-100/PB-100-garage-install-freeze-checklist.csv`,
  tying the 50 A battery/MAXI path, DTP/DT/DTM connector classes, MINI/ATO fuse
  access, wire gauges, crimp tooling, seals, enclosure service access, BOM
  synchronization, and no-layout boundaries into one machine-checked artifact.
  `hardware/power-board/PB-100/PB-100-garage-install-sourcing-precheck.csv`
  now adds the closeable sourcing/install bridge for garage-owned keys, wire and
  harness derating, purchase kits, service access, and no-PCB-migration rules.
  `hardware/power-board/PB-100/PB-100-garage-install-closeout-precheck.csv`
  adds the closeout bridge for user-installed ownership, 50 A input path,
  connector/fuse kits, wire/harness derating, enclosure service/vibration, BOM
  synchronization, and no-layout manufacturing boundary. The 2026-07-20
  `hardware/power-board/PB-100/PB-100-garage-purchase-kit-candidates.csv`
  refresh now records candidate DTP06/DTP04, DT06/DT04, DTM06/DTM04 housings,
  contacts, wedgelocks, Littelfuse fuse-holder classes, and HDT-48-00-class
  tooling; final purchase lock still needs supplier stock, exact quantities,
  boots/backshells, insertion/removal tools, enclosure entry, heat/service, and
  vibration evidence.
- Thermal telemetry now has a TDK `NTCGS103JF103FT8`-class 10 kΩ 150 °C
  AEC-Q200 NTC candidate for all three thermal points; schematic freeze must
  still close divider values, ADC scaling, placement, assembly class, and
  calibration.
- JPB1 uses the reviewed Hirose `FX18-100P-0.8SV10` plus
  `FX18-100S-0.8SV10` pair. Both footprints contain exactly six plated TH
  lands for four logical MF circuits, all assigned to GND with mirrored
  plug/socket geometry. Schematic freeze must still close paired 20 mm stack
  fit, vibration retention, fixture/enclosure, and assembly handling.
- JPB1 now has a B2B interface trace and LB-100 resource-class binding tying
  the selected FX18 pair, 100-pin map, output controls/fault/current telemetry,
  board telemetry, CAN1 safety crossing, and exact MCU pin-binding evidence
  together.
- B2B/LB-100 pin binding now has a resource-budget precheck for STM32H563
  LQFP-100 schematic review, covering 10 PWM-capable controls, 16 ADC-class
  measurements, fault/wake inputs, `PB_I2C`, CAN1 safety, and reserved
  expansion. The exact STM32 binding remains synchronized through the LB-100
  pin-binding precheck rather than inferred from resource counts alone.
- B2B/LB-100 pin binding now has an audit checklist covering the exact
  STM32H563 LQFP-100 pinout audit, 16 ADC-capable measurement inputs or reviewed
  mux strategy, output default-low PWM routing, CAN1 DNP/open crossing, FX18
  footprint drawing, stack height, vibration retention, assembly handling, and
  no-layout boundary in
  `hardware/power-board/PB-100/PB-100-b2b-lb100-pin-audit-checklist.csv`.
- B2B/LB-100 review now has a freeze checklist tying the FX18 connector pair,
  power/status pins, role-free OUTn signals, board telemetry, `PB_I2C`, CAN1
  read-only crossing, STM32H563 LQFP-100 audit, cross-artifact synchronization,
  and no-layout boundary to
  `hardware/power-board/PB-100/PB-100-b2b-interface-freeze-checklist.csv`.
- B2B/LB-100 review now has a closeout precheck bridging the JPB1 100-pin map,
  FX18 footprint/stack/vibration evidence, exact STM32H563 LQFP-100 pinout
  audit, ADC/PWM/resource limits, CAN1 DNP/open crossing, and no-layout
  manufacturing boundary to
  `hardware/power-board/PB-100/PB-100-b2b-interface-closeout-precheck.csv`.
- Q1 input reverse MOSFET pin evidence and schematic capture use selected
  `IAUT300N08S5N012ATMA2` 80 V TOLL with pins 1, 2-8, and `Tab`. Generated
  40 A evidence closes the pre-layout SOA/thermal blocker; exact gate passives,
  reviewed plane/polygon/bus current path, and PB-BENCH-010 remain later gates.
- Q1 input reverse planning now has a package/thermal trace tying
  selected `IAUT300N08S5N012ATMA2`, the two controlled non-drop-in 80 V alternatives,
  the 40 A board budget, shunt measurement boundary, and assembly-source
  blockers together. Former 60 V calculations are history only.
- Q1 input reverse freeze review now ties LM74930-Q1 DGATE/default-off behavior,
  selected TOLL and controlled non-drop-in 80 V alternatives, protected
  measurement sequence, active-cutoff dependency, sourcing gate, and no-layout
  boundary into
  `hardware/power-board/PB-100/PB-100-input-reverse-freeze-review.csv`.
- Q1 input reverse freeze checklist now ties gate clamp/discharge timing,
  selected TOLL and controlled 80 V package alternatives, protected
  measurement sequence, 40 A thermal/copper/SOA audit, assembly sourcing, and
  no-layout boundary into
  `hardware/power-board/PB-100/PB-100-input-reverse-q1-freeze-checklist.csv`.
- Q1 input reverse derivation precheck now ties LM74930-Q1 CAP/DGATE behavior,
  ideal-diode thresholds, MOSFET RDS(on) window, passive thermal-path limit,
  protected measurement sequence, assembly alternates, and no-layout boundary
  to
  `hardware/power-board/PB-100/PB-100-input-reverse-q1-derivation-precheck.csv`.
- Q1 input reverse closeout precheck now bridges LM74930-Q1 source boundary,
  CAP/DGATE default-off behavior, ideal-diode reverse-current behavior,
  RDS(on) thermal window, TOLL/LFPAK88/PowerPAK alternatives, TVS overshoot
  active-cutoff dependency, protected measurement sequence, assembly sourcing, capture sync,
  and no-layout boundary to
  `hardware/power-board/PB-100/PB-100-input-reverse-q1-closeout-precheck.csv`.
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
- Board-current value closure now has
  `hardware/power-board/PB-100/PB-100-board-current-budget-value-freeze-checklist.csv`,
  tying the current-budget contract, high-current path sequence, connector and
  wire derating, Q1/shunt operating points, copper pre-layout loss boundary,
  firmware enforcement, telemetry enforcement, bench path, and no-layout
  boundary into one machine-checked artifact.
- Board-current value derivation now has
  `hardware/power-board/PB-100/PB-100-board-current-budget-value-derivation-precheck.csv`,
  tying shunt/Q1 formulas, connector/wire derating, firmware enforcement,
  telemetry enforcement, sourcing ownership, and no-layout boundary into one
  machine-checked artifact.
- Board-current closeout precheck now has
  `hardware/power-board/PB-100/PB-100-board-current-budget-closeout-precheck.csv`,
  bridging the 50 A fuse path, 40 A budget, protected high-current path,
  selected Q1 thermal path and controlled alternatives, shunt/Kelvin telemetry,
  copper pre-layout boundary,
  firmware enforcement, bench telemetry evidence, BOM owner split, and
  no-layout boundary to PBREL-002.
- ADR-0015 candidate A is accepted: PB-100 owns the CAN1 transceiver, ESD/TVS,
  optional termination/CMC, CANH/CANL, and harness physical layer; LB-100 owns
  STM32 FDCAN, protocol, and read-only firmware policy.
- Exported-netlist validation enforces `CAN1_TX_ROUTE -> U_CAN1 ->
  CAN1_TX_GATE_OUT -> JP_CAN1 (DNP/open) -> CAN1_TXD_SAFE -> U_CAN1_PHY TXD`,
  while `U_CAN1_PHY RXD` connects only to `CAN1_RX_ROUTE`.
- CAN1 TX-disable now has a trace tying `JP_CAN1`, `U_CAN1`,
  `CAN1_TX_ROUTE`, `CAN1_TX_DISABLED_STATUS`, firmware listen-only behavior,
  DNP BOM ownership, the production DNP review, and the future-ADR
  hardware-action boundary together.
- CAN1 TX-disable design values document the 0 Ω DNP/open link,
  `SN74LVC1G125-Q1`-class default-disabled gate, 47 kΩ pulls, physical
  `OE`-node status readback, and reset/unpowered bench checks in
  `hardware/power-board/PB-100/PB-100-can1-tx-disable-design-calculation.md`.
- CAN1 reset and DNP bench procedure now has a checklist covering LB-100 reset,
  LB-100 unpowered, production DNP/open inspection, physical disabled-status
  readback, RX listen-only independence, and future-ADR hardware-action checks;
  physical observations remain post-prototype in
  `hardware/power-board/PB-100/PB-100-can1-reset-bench-checklist.csv`.
- CAN1 default-disable closure now has
  `hardware/power-board/PB-100/PB-100-can1-default-disable-freeze-checklist.csv`,
  tying the DNP/open missing link, default-disabled gate values, TXD recessive
  bias, physical status readback, firmware/capability boundary, bench path, and
  no-layout boundary into one machine-checked artifact.
- CAN1 default-disable derivation now has
  `hardware/power-board/PB-100/PB-100-can1-default-disable-derivation-precheck.csv`,
  tying policy/configuration, physical missing-link, gate polarity, status
  readback, firmware/capability evidence, bench procedure, factory DNP
  sourcing, and no-layout boundary into one machine-checked artifact.
- CAN1 default-disable closeout precheck now has
  `hardware/power-board/PB-100/PB-100-can1-default-disable-closeout-precheck.csv`,
  bridging policy, DNP/open missing-link evidence, default-disabled gate,
  physical status readback, RX independence, firmware/capability evidence,
  bench procedure, factory DNP sourcing, and no-layout boundary to PBREL-001.
- CAN1 physical closeout additionally freezes the exact DTM04-4P/DTM06-4S
  garage harness kit and records PB-BENCH-012 as a post-prototype first-power
  gate in `hardware/power-board/PB-100/PB-100-can1-physical-closeout.md`.
- Close current and thermal telemetry scaling, filtering, and calibration notes.
- Promote the accepted output-controller passives, local clamp diodes, and Q1
  gate network into reviewed value-bearing sheets; keep generated SOA/thermal
  evidence synchronized and preserve its hard escape conditions.
- Synchronize factory and garage BOM drafts with final selections.
- Keep `make check` passing with local `kicad-cli` available, zero ERC
  violations, and a successful KiCad S-expression netlist export.
- Logic power now has candidate LM5164 values in
  `hardware/power-board/PB-100/PB-100-logic-power-design-calculation.md`, but
  those values remain not final until load budget, sourcing, EMI, and stability
  review close; the close-work list is tracked in
  `hardware/power-board/PB-100/PB-100-logic-power-value-freeze-checklist.csv`
  plus
  `hardware/power-board/PB-100/PB-100-logic-power-value-derivation-precheck.csv`.
- LB-100 now has a `PB_5V_OUT` load-budget precheck with a 500 mA sustained
  allocation; exceeding it keeps the PB-100 LM5013-Q1-class fallback active.
- Thermal telemetry now has candidate NTC divider values in
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-design-calculation.md`,
  but placement, ADC settling, calibration, and assembly review remain open and
  tracked in
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-freeze-checklist.csv`
  plus
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-derivation-precheck.csv`.
- Thermal telemetry closeout precheck now adds a machine-checked bridge in
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-closeout-precheck.csv`.
- Thermal telemetry divider calibration now has a firmware configuration
  contract in `firmware/configs/config-example.json`,
  `firmware/configs/svc-config.schema.json`, and `firmware/core/svc_config.h`;
  ADC settling, placement, self-heating, sourcing, and calibration hooks remain
  schematic-freeze blockers, while physical bench calibration is a
  post-prototype validation gate.

## Required during PB-100 EVT layout

- Preserve the accepted architecture and role-free generic output mapping.
- Add every diagnostic and isolation provision required by ADR-0019 and
  `hardware/power-board/PB-100/PB-100-evt-prototype-plan.md`.
- Promote preliminary schematic symbols and values in controlled iterations and
  keep schematic-to-board parity visible.
- Keep manufacturing artifacts absent while the aggregate state is
  `EVT-LAYOUT-AUTHORIZED`.

## Required before five-board EVT fabrication

- Final EVT schematic review plus zero DRC, parity and unconnected findings.
- Reviewed PB-100 40 A copper/via/connector electrothermal and clamp-loop
  extraction advances aggregate authorization to `EVT-FAB-AUTHORIZED`.
- Supplier DFM, stackup, connector fit, laboratory safety controls and the
  segregated five-board release package are accepted.
- Gerber, drill, BOM/CPL, placement and assembly outputs state
  `PB-100 REV.1 EVT — NOT FOR PRODUCTION` and are never reused as production
  release artifacts without a new review.

## Required before prototype bring-up

- PB-100 layout, fabrication outputs, assembly outputs, and inspection files.
- Bench test procedure for first power, current telemetry, thermal telemetry,
  short-circuit handling, CAN1 listen-only behavior, and output load tests.
- Firmware hardware-abstraction layer for the selected LB-100 MCU and PB-100
  telemetry paths.
- Reference vehicle harness and connector assembly notes.

## No-go conditions

- Any PB-100 manufacturing output before `EVT-FAB-AUTHORIZED`.
- Any energized EVT board before build inspection advances the state to
  `BENCH-VALIDATION`.
- Any motorcycle installation before mandatory bench evidence advances the
  state to `MOTORCYCLE-VALIDATION`.
- Any destructively or abnormally stressed EVT board installed on the
  motorcycle.
- Any production or general field use of Rev.1 or before
  `PRODUCTION-RELEASE`, accepted PBREL-007 evidence, reviewed Rev.2 and the
  normal production package gates are closed.
- Any vehicle CAN1 TX enable path without a new ADR and explicit hardware action.
- Any hard-coded accessory role to physical output mapping in hardware or
  firmware.
- Any firmware path that bypasses Output Manager for physical output state.
