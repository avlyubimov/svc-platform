# PB-100 Schematic Package

Status: Schematic planning package ready for review; not frozen

This package converts frozen PB-100 requirements into schematic-planning inputs.
It is not a PCB layout package.

## Governing documents

- `docs/architecture/Architecture-Review-v1.0.md`
- `docs/requirements/pb-100-requirements.md`
- `docs/adr/ADR-0006-pb-100-baseline-requirements.md`
- `docs/adr/ADR-0007-pb-100-high-side-output-switching.md`
- `docs/adr/ADR-0008-pb-100-current-budget.md`
- `docs/adr/ADR-0010-pb-100-power-path-candidate-strategy.md`
- `docs/adr/ADR-0011-pb-100-low-current-output-stage.md`
- `docs/can/can-safety.md`
- `docs/production/component-family-shortlist.md`
- `firmware/configs/hardware/pb-100-capabilities.json`
- `production/bom/pb100_symbol_bom_map.csv`
- `hardware/power-board/PB-100/PB-100-assembly-readiness-trace.csv`
- `hardware/power-board/PB-100/PB-100-factory-assembly-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-factory-assembly-sourcing-precheck.csv`
- `hardware/power-board/PB-100/PB-100-factory-assembly-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-b2b-interface-trace.csv`
- `hardware/power-board/PB-100/PB-100-b2b-lb100-resource-binding.csv`
- `hardware/power-board/PB-100/PB-100-b2b-lb100-pin-audit-checklist.csv`
- `hardware/power-board/PB-100/PB-100-b2b-interface-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-b2b-interface-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-b2b-lb100-pin-binding-precheck.md`
- `production/bom/pb100_assembly_sourcing_recheck.csv`
- `production/bom/pb100_sourcing_evidence_snapshot.csv`
- `hardware/power-board/PB-100/PB-100-garage-install-sourcing-precheck.csv`
- `hardware/power-board/PB-100/PB-100-garage-install-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-can1-tx-disable.md`
- `hardware/power-board/PB-100/PB-100-can1-tx-disable-trace.csv`
- `hardware/power-board/PB-100/PB-100-can1-safety-verification.csv`
- `hardware/power-board/PB-100/PB-100-can1-production-dnp-review.csv`
- `hardware/power-board/PB-100/PB-100-can1-reset-bench-checklist.csv`
- `hardware/power-board/PB-100/PB-100-can1-tx-disable-design-calculation.md`
- `hardware/power-board/PB-100/PB-100-can1-default-disable-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-can1-default-disable-derivation-precheck.csv`
- `hardware/power-board/PB-100/PB-100-can1-default-disable-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-input-power-design-values.csv`
- `hardware/power-board/PB-100/PB-100-tvs-load-dump-margin-trace.csv`
- `hardware/power-board/PB-100/PB-100-tvs-load-dump-freeze-review.csv`
- `hardware/power-board/PB-100/PB-100-tvs-overshoot-escape-checklist.csv`
- `hardware/power-board/PB-100/PB-100-tvs-overshoot-validation-precheck.csv`
- `hardware/power-board/PB-100/PB-100-tvs-overshoot-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-mosfet-voltage-margin-review.md`
- `hardware/power-board/PB-100/PB-100-board-current-budget-trace.csv`
- `hardware/power-board/PB-100/PB-100-board-current-budget-freeze-review.csv`
- `hardware/power-board/PB-100/PB-100-board-current-budget-design-calculation.md`
- `hardware/power-board/PB-100/PB-100-board-current-budget-value-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-board-current-budget-value-derivation-precheck.csv`
- `hardware/power-board/PB-100/PB-100-board-current-budget-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry.md`
- `hardware/power-board/PB-100/PB-100-current-telemetry-trace.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry-freeze-review.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry-design-calculation.md`
- `hardware/power-board/PB-100/PB-100-current-telemetry-value-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry-value-derivation-precheck.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-current-monitor-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-garage-connector-fuse-plan.md`
- `hardware/power-board/PB-100/PB-100-garage-install-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-garage-install-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-input-controller-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-input-protection-pin-contract.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-package-trace.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-freeze-review.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-q1-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-q1-derivation-precheck.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-q1-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-protection.md`
- `hardware/power-board/PB-100/PB-100-kicad-prep.md`
- `hardware/power-board/PB-100/kicad/PB-100.kicad_sch`
- `hardware/power-board/PB-100/kicad/lib/PB100.kicad_sym`
- `hardware/power-board/PB-100/PB-100-logic-buck-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-design-calculation.md`
- `hardware/power-board/PB-100/PB-100-logic-power-design-values.csv`
- `hardware/logic-board/LB-100/LB-100-power-budget-precheck.md`
- `hardware/power-board/PB-100/PB-100-logic-power-rail-trace.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-freeze-review.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-value-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-value-derivation-precheck.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-design-placeholders.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-rails.md`
- `hardware/power-board/PB-100/PB-100-out2-soa.md`
- `hardware/power-board/PB-100/PB-100-output-channel-pin-contract.csv`
- `hardware/power-board/PB-100/PB-100-low-current-output-baseline-trace.csv`
- `hardware/power-board/PB-100/PB-100-low-current-output-freeze-review.csv`
- `hardware/power-board/PB-100/PB-100-high-medium-output-baseline-trace.csv`
- `hardware/power-board/PB-100/PB-100-high-medium-output-freeze-review.csv`
- `hardware/power-board/PB-100/PB-100-output-stage-value-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-output-stage-value-derivation-precheck.csv`
- `hardware/power-board/PB-100/PB-100-output-stage-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-output-controller-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-output-net-expansion.csv`
- `hardware/power-board/PB-100/PB-100-output-stage-design-values.csv`
- `hardware/power-board/PB-100/PB-100-preliminary-validation.md`
- `hardware/power-board/PB-100/PB-100-net-naming.md`
- `hardware/power-board/PB-100/PB-100-schematic-readiness-dashboard.csv`
- `hardware/power-board/PB-100/PB-100-schematic-freeze-gap-register.csv`
- `hardware/power-board/PB-100/PB-100-board-release-blocker-register.csv`
- `hardware/power-board/PB-100/PB-100-validation-traceability.csv`
- `hardware/power-board/PB-100/PB-100-test-point-plan.csv`
- `hardware/power-board/PB-100/PB-100-fault-response-matrix.csv`
- `hardware/power-board/PB-100/PB-100-schematic-net-domain-plan.csv`
- `hardware/power-board/PB-100/PB-100-schematic-capture-plan.md`
- `hardware/power-board/PB-100/PB-100-schematic-capture-work-queue.csv`
- `hardware/power-board/PB-100/PB-100-schematic-freeze-checklist.md`
- `hardware/power-board/PB-100/PB-100-schematic-readiness-review.md`
- `hardware/power-board/PB-100/PB-100-review-release-manifest.csv`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry.md`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry-trace.csv`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry-freeze-review.csv`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry-design-calculation.md`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-derivation-precheck.csv`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry-closeout-precheck.csv`

## Electrical baseline

- Battery input: 6-18 V normal target.
- Main harness fuse target: 50 A.
- Board continuous-current target: at least 40 A after thermal validation.
- Default configuration total-current limit: 40 A.
- 40 A freeze review: connector derating, Q1 thermal path, shunt Kelvin path,
  protected copper distribution, firmware config, telemetry enforcement, and
  no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-board-current-budget-freeze-review.csv`.
- 40 A board-current value checklist: current-budget contract, path sequence,
  connector and wire derating, Q1 thermal path, shunt/Kelvin path, copper
  pre-layout boundary, firmware enforcement, telemetry enforcement, bench
  validation, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-board-current-budget-value-freeze-checklist.csv`.
- 40 A board-current value derivation precheck: current-budget contract,
  protected current path, shunt and Q1 formulas, copper pre-layout loss, garage
  fuse/wire derating, firmware and telemetry enforcement, BOM sourcing, and
  no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-board-current-budget-value-derivation-precheck.csv`.
- 40 A board-current closeout precheck: requirement/configuration boundary,
  protected high-current path, main fuse and wire derating, Q1 thermal path,
  shunt/Kelvin telemetry, copper pre-layout boundary, firmware enforcement,
  bench telemetry evidence, BOM owner split, and no-layout manufacturing
  boundary are tracked in
  `hardware/power-board/PB-100/PB-100-board-current-budget-closeout-precheck.csv`.
- Current telemetry freeze review: 0.5 mΩ shunt range, INA228-class monitor
  headroom, Kelvin sense, ADC/I2C ownership, per-output IMON scaling,
  calibration configuration, and stale-telemetry safe faults are tracked in
  `hardware/power-board/PB-100/PB-100-current-telemetry-freeze-review.csv`.
- Current telemetry candidate values: 0.5 mΩ shunt operating points,
  INA228-class ±40.96 mV range, candidate `0x40` address straps, LB-owned
  pull-up boundary, input filter, VBUS filter, and calibration boundary are
  tracked in
  `hardware/power-board/PB-100/PB-100-current-telemetry-design-calculation.md`.
- Current telemetry value checklist: shunt range, monitor family, Kelvin and
  input filter, I2C ownership, alert behavior, VBUS stress, per-output IMON
  scaling, configuration calibration, stale safe-fault tests, sourcing, and
  no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-current-telemetry-value-freeze-checklist.csv`.
- Current telemetry value derivation precheck: shunt voltage and power formulas,
  INA228/INA229 range, Kelvin/filter network, I2C ownership, alert boundary,
  VBUS stress, per-output IMON scaling, configuration calibration, bench
  safe-fault path, sourcing, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-current-telemetry-value-derivation-precheck.csv`.
- Current telemetry closeout precheck: shunt formulas, monitor family, Kelvin
  and filter network, I2C/interrupt ownership, protected VBUS stress,
  per-output IMON scaling, configuration-owned calibration, bench safe-fault
  evidence, sourcing/symbol synchronization, and no-layout manufacturing
  boundary are tracked in
  `hardware/power-board/PB-100/PB-100-current-telemetry-closeout-precheck.csv`.
- Input reverse freeze review: LM74700 gate/default-off behavior, TOLL/LFPAK88
  and PowerPAK alternates, protected measurement sequence, HM3 TVS dependency,
  sourcing gate, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-input-reverse-freeze-review.csv`.
- Input reverse Q1 freeze checklist: gate clamp/discharge timing, package
  alternates, protected measurement sequence, 40 A thermal/copper/SOA audit,
  assembly sourcing, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-input-reverse-q1-freeze-checklist.csv`.
- Input reverse Q1 derivation precheck: LM74700-Q1 VCAP/gate-driver behavior,
  ideal-diode thresholds, MOSFET RDS(on) window, TVS stress, protected
  measurement sequence, assembly alternates, and no-layout boundary are tracked
  in
  `hardware/power-board/PB-100/PB-100-input-reverse-q1-derivation-precheck.csv`.
- Input reverse Q1 closeout precheck: controller source boundary, VCAP/gate
  default-off behavior, ideal-diode reverse-current behavior, RDS(on) thermal
  window, TOLL/LFPAK88/PowerPAK alternatives, TVS overshoot dependency,
  protected measurement sequence, assembly sourcing, input capture sync, and
  no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-input-reverse-q1-closeout-precheck.csv`.
- TVS/load-dump freeze review: active SM8S33AHM3/I HM3 branch, 100 V device
  margin, 60 V MOSFET overshoot dependency, 80 V Q1 alternate, 40 V
  smart-switch ADR boundary, sourcing gate, and no-layout boundary are tracked
  in `hardware/power-board/PB-100/PB-100-tvs-load-dump-freeze-review.csv`.
- TVS overshoot escape checklist: active HM3 source snapshot, 60 V headroom,
  80 V MOSFET escape decision, 100 V downstream boundary, 40 V ADR boundary,
  schematic-value dependencies, sourcing, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-tvs-overshoot-escape-checklist.csv`.
- TVS overshoot validation precheck: waveform/source impedance,
  `Vstress = Vclamp + Lloop * di/dt`, bench probe and simulation parasitic
  setup, 60 V acceptance versus 80 V escape, factory alternates, and no-layout
  boundary are tracked in
  `hardware/power-board/PB-100/PB-100-tvs-overshoot-validation-precheck.csv`.
- TVS overshoot closeout precheck: active source, overshoot method, 60 V
  acceptance, 80 V escape, 100 V downstream defaults, 40 V ADR boundary,
  schematic-value dependencies, sourcing, validation sync, and no-layout
  boundary are tracked in
  `hardware/power-board/PB-100/PB-100-tvs-overshoot-closeout-precheck.csv`.
- MOSFET voltage-margin review: 60 V MOSFET paths behind the active HM3 TVS
  branch need explicit overshoot evidence or migration to the 80 V review
  escape path before schematic freeze. See
  `hardware/power-board/PB-100/PB-100-mosfet-voltage-margin-review.md`.
- Logic power freeze review: LM5164/LM5013/TPS54360B regulator boundaries,
  protected `VBAT_PROT` sequencing, 1000 mA `PB_5V_OUT` budget, UVLO safe-off,
  PGOOD, inductor/capacitor classes, sourcing, and no-layout boundary are
  tracked in
  `hardware/power-board/PB-100/PB-100-logic-power-freeze-review.csv`.
- Logic power value checklist: LM5164/LM5013 selection, load budget, UVLO,
  RON, feedback, bootstrap, L1/COUT, `PB_PWR_GOOD`, switch-node EMI, sourcing,
  and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-logic-power-value-freeze-checklist.csv`.
- Logic power value derivation precheck: LM5164/LM5013/TPS54360 source
  boundaries, `PB_5V_OUT` budget, UVLO, RON, feedback, bootstrap, PGOOD,
  inductor/capacitor, EMI, sourcing, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-logic-power-value-derivation-precheck.csv`.
- Logic power closeout precheck: regulator family source boundary,
  `PB_5V_OUT` budget, protected input/transient stress, UVLO/default-off,
  RON/feedback/bootstrap, inductor/COUT stability, PGOOD interface,
  switch-node EMI, sourcing, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-logic-power-closeout-precheck.csv`.
- LB-100 power budget precheck: LB-100 has a 500 mA sustained allocation from
  `PB_5V_OUT`; exceeding it keeps the LM5013-Q1-class fallback active before
  PB-100 schematic freeze.
- Thermal telemetry freeze review: NTC sensor class, divider/ADC scaling,
  placement zones, 85/105/75 °C thresholds, firmware fail-safe behavior,
  calibration, assembly alternates, and bench validation are tracked in
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-freeze-review.csv`.
- Thermal telemetry value checklist: sensor class, placement zones,
  divider/ADC scaling, self-heating, ADC settling, configuration calibration,
  firmware fail-safe, bench validation, sourcing, and no-layout boundary are
  tracked in
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-freeze-checklist.csv`.
- Thermal telemetry value derivation precheck: NTC source boundary, beta and
  divider equations, self-heating estimate, ADC settling, placement zones,
  configuration calibration, firmware fail-safe, sourcing, and no-layout
  boundary are tracked in
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-derivation-precheck.csv`.
- Thermal telemetry closeout precheck: NTC source class, divider equations and
  values, placement zones, self-heating, ADC settling, configuration-owned
  calibration, firmware fail-safe, bench validation, sourcing/symbol
  synchronization, and no-layout manufacturing boundary are tracked in
  `hardware/power-board/PB-100/PB-100-thermal-telemetry-closeout-precheck.csv`.
- Factory assembly freeze checklist: factory-owned critical keys, alternate
  coverage, JLCPCB/PCBWay assembly class, date-stamped distributor continuity,
  package handling, TVS source hygiene, B2B/CAN1 production notes, BOM evidence
  synchronization, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-factory-assembly-freeze-checklist.csv`.
- Factory assembly sourcing precheck: factory-owned critical keys, BOM/evidence
  register alignment, JLCPCB/PCBWay assembly-platform recheck, alternate
  coverage, package handling, TVS source hygiene, logic/current/thermal sourcing,
  B2B/CAN1 production handling, date-stamped sourcing evidence, and no-layout
  boundary are tracked in
  `hardware/power-board/PB-100/PB-100-factory-assembly-sourcing-precheck.csv`.
- Factory assembly closeout precheck: factory-owned critical key ownership,
  critical alternatives, factory assembly-platform handling, power-path package
  handling, TVS source hygiene, logic/current/thermal sourcing, B2B/CAN1
  production handling, BOM evidence synchronization, inspection/rework evidence,
  and no-layout manufacturing boundary are tracked in
  `hardware/power-board/PB-100/PB-100-factory-assembly-closeout-precheck.csv`.
- Garage install freeze checklist: user-installed connector/fuse scope, 50 A
  battery/MAXI path, DTP/DT/DTM connector classes, MINI/ATO fuse access,
  purchase-ready connector kit evidence, wire gauges, enclosure service access,
  BOM synchronization, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-garage-install-freeze-checklist.csv`.
- Garage install sourcing precheck: garage-owned symbol keys, 50 A battery/MAXI
  path, DTP/DT/DTM connector class boundaries, user-serviceable fuses,
  purchase-ready kit evidence, wire/harness derating, enclosure/service review,
  BOM/source synchronization, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-garage-install-sourcing-precheck.csv`.
- Garage install closeout precheck: user-installed critical key ownership,
  battery/MAXI path, output/signal connector classes, user-serviceable fuses,
  purchase-ready kits, wire/harness derating, enclosure/service/vibration
  evidence, BOM/source synchronization, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-garage-install-closeout-precheck.csv`.
- Output freeze reviews: high/medium and low-current stages keep TPS48110 plus
  external MOSFET boundaries, OUT2 SOA, gate-drive defaults, sense/telemetry,
  fault thresholds, clamp strategy, low-current ADR-0011 no-smart-switch
  boundary, and no-layout constraints in dedicated review artifacts.
- Output value freeze checklist: controller baseline, OUT2 SOA/fuse energy,
  medium fuse paths, low-current ADR-0011 boundary, threshold/timer networks,
  gate default-off behavior, sense/ADC scaling, inductive clamp, MOSFET voltage
  margin, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-output-stage-value-freeze-checklist.csv`.
- Output value derivation precheck: TI TPS4811-Q1 equations and TPS48110Q1EVM
  reference positions are mapped to PB-100 high, medium, and low current
  value derivation in
  `hardware/power-board/PB-100/PB-100-output-stage-value-derivation-precheck.csv`.
- Output-stage closeout precheck: source formulas, class maps, design-item
  completeness, thresholds/timers, bootstrap/default-off behavior, telemetry
  scaling, SOA/fuse/clamp evidence, low-current ADR-0011 boundary, instance
  synchronization, and no-layout boundary are bridged in
  `hardware/power-board/PB-100/PB-100-output-stage-closeout-precheck.csv`.
- Outputs: 10 generic high-side protected channels.
- CAN1: read-only by default; TX physically disabled.

## Output classes

| Class | Outputs | Target fuse | Target current limit | Initial implementation direction |
|---|---|---:|---:|---|
| High current | OUT2 | 20 A | 18 A | TPS48110AQDGXRQ1-class controller plus external 60 V N-MOSFET |
| Medium current | OUT1, OUT3, OUT4, OUT6, OUT7, OUT10 | 10-15 A | 8-12 A | TPS48110AQDGXRQ1-class controller plus external 60 V N-MOSFET |
| Low current | OUT5, OUT8, OUT9 | 5 A | 4 A | TPS48110AQDGXRQ1-class controller plus external 60 V N-MOSFET |

## Required schematic blocks

- Battery input protection: main input connector, reverse protection, TVS/load
  dump clamp, input current measurement, battery voltage measurement.
- Board-current budget calculation: 50 A main fuse, 40 A continuous budget,
  0-60 A telemetry range, 0.5 mΩ shunt dissipation, Q1 candidate dissipation,
  and no-layout copper boundary are tracked in
  `hardware/power-board/PB-100/PB-100-board-current-budget-design-calculation.md`.
- Logic power: protected 5 V/3.3 V rails for LB-100 interface and telemetry.
- Output channels: fuse, high-side switch/controller, current sense, fault
  signal, flyback/inductive-load handling where required.
- Thermal sensing: PCB sensor and power-zone sensor.
- Board identity: revision or resistor-coded identity where practical.
- Board-to-board interface: stable PB-100 to LB-100 connector.
- Safety interlocks: CAN1 TX disable status/control if CAN1 routing crosses
  PB-100.
- CAN1 production DNP review: `JP_CAN1` remains DNP/open, `U_CAN1` defaults
  disabled, `CAN1_TX_DISABLED_STATUS` reports physical disabled state, and
  future CAN1 TX requires ADR plus hardware action.
- CAN1 TX-disable candidate values: 0 Ω DNP/open `JP_CAN1`, 47 kΩ default
  disable pull, `SN74LVC1G125-Q1`-class `U_CAN1`, 47 kΩ downstream recessive
  bias, and 1 kΩ/100 kΩ physical-status readback are tracked in
  `hardware/power-board/PB-100/PB-100-can1-tx-disable-design-calculation.md`.
- CAN1 reset and DNP bench checklist: LB-100 reset, LB-100 unpowered,
  production DNP/open inspection, physical disabled-status readback, RX
  listen-only independence, and future-ADR hardware-action checks are tracked in
  `hardware/power-board/PB-100/PB-100-can1-reset-bench-checklist.csv`.
- CAN1 default-disable freeze checklist: policy boundary, `JP_CAN1` DNP/open
  missing link, `U_CAN1` disabled default, TXD recessive bias, physical
  disabled-status readback, DNP-link detect boundary, RX independence, firmware
  and capability boundary, bench path, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-can1-default-disable-freeze-checklist.csv`.
- CAN1 default-disable derivation precheck: policy/configuration boundary,
  physical missing-link barrier, default-disabled gate polarity, TXD recessive
  bias, physical disabled-status readback, optional DNP link detect,
  listen-only RX independence, firmware/capability/bench evidence, factory DNP
  sourcing bridge, and no-layout boundary are tracked in
  `hardware/power-board/PB-100/PB-100-can1-default-disable-derivation-precheck.csv`.
- CAN1 default-disable closeout precheck: policy/hardware boundary, DNP/open
  missing link, default-disabled gate, TXD recessive bias, physical
  disabled-status readback, DNP link-detect boundary, listen-only RX
  independence, firmware/capability/bench evidence, factory DNP sourcing, and
  no-layout manufacturing boundary are tracked in
  `hardware/power-board/PB-100/PB-100-can1-default-disable-closeout-precheck.csv`.

## Board-to-board signal budget

Logical pin-budget CSV:
`hardware/power-board/PB-100/PB-100-b2b-pin-budget.csv`.

Schematic-planning pin map CSV:
`hardware/power-board/PB-100/PB-100-b2b-pin-map.csv`.

B2B interface trace CSV:
`hardware/power-board/PB-100/PB-100-b2b-interface-trace.csv`.

LB-100 resource-class binding CSV:
`hardware/power-board/PB-100/PB-100-b2b-lb100-resource-binding.csv`.

LB-100 pin audit and FX18 checklist:
`hardware/power-board/PB-100/PB-100-b2b-lb100-pin-audit-checklist.csv`.

B2B interface freeze checklist:
`hardware/power-board/PB-100/PB-100-b2b-interface-freeze-checklist.csv`.

B2B interface closeout precheck:
`hardware/power-board/PB-100/PB-100-b2b-interface-closeout-precheck.csv`.

LB-100 pin-binding precheck:
`hardware/power-board/PB-100/PB-100-b2b-lb100-pin-binding-precheck.md`.

| Signal group | Count target | Direction | Notes |
|---|---:|---|---|
| Power and grounds | 20-30 pins | PB-100/LB-100 | Multiple grounds and supply pins for current return and signal integrity |
| Output enable/PWM | 10 pins | LB-100 to PB-100 | One control signal per output minimum |
| Output fault/status | 10 pins | PB-100 to LB-100 | Can be direct or multiplexed if diagnostic latency is acceptable |
| Current telemetry | 10 signals | PB-100 to LB-100 | Analog, I2C/SPI monitors, or high-side IMON strategy |
| Board telemetry | 4-8 signals | PB-100 to LB-100 | Input voltage/current, PCB temp, power-zone temp, power-good |
| Configuration/ID | 2-4 signals | PB-100 to LB-100 | Revision ID, EEPROM, or resistor-coded identity |
| Expansion reserve | 10-20 pins | Mixed | Spare GPIO/ADC/I2C/SPI/UART capacity |

The initial 100-pin mezzanine target is now a Hirose FX18 candidate pair:
`FX18-100P-0.8SV10` plus `FX18-100S-0.8SV20`. `JPB1` pin assignment is captured
as a schematic-planning input, but stack height, vendor footprint drawing,
vibration retention, PCBA handling, and LB-100 MCU pin binding remain
schematic-review items. The B2B interface trace ties the candidate pair,
power/status pins, output controls/faults/current telemetry, board telemetry,
CAN1 safety crossing, and reserve pins back to the LB-100 resource-class
binding review. Exact STM32H5 package pins remain a LB-100 schematic-review
item.

The pin-binding precheck defines the LB-100 resource budget that must be proven
before exact STM32H563 LQFP-100 package pins can close.
The pin audit checklist keeps the exact STM32H563 LQFP-100 pinout audit, ADC
capacity, output PWM default-low behavior, fault/wake routing, CAN1 read-only
crossing, FX18 footprint drawing, stack height, vibration retention, assembly
handling, and no-layout boundary visible before connector placement.
The B2B interface freeze checklist ties that audit to power/status pins,
role-free output signals, board telemetry, `PB_I2C`, CAN1 read-only crossing,
resource-class reservations, cross-artifact synchronization, and the no-layout
boundary for PBREL-003.
The B2B interface closeout precheck bridges that freeze checklist to the JPB1
100-pin map, FX18 footprint/stack/vibration evidence, exact STM32H563 LQFP-100
pinout audit, ADC/PWM/resource limits, CAN1 DNP/open crossing, and the explicit
no-layout/manufacturing-output boundary.

## Output channel matrix

Output matrix CSV:
`hardware/power-board/PB-100/PB-100-output-channel-matrix.csv`.

The matrix keeps hardware outputs generic while carrying the BMW K25 reference
defaults needed for sizing and bench tests.

Schematic instance plan CSV:
`hardware/power-board/PB-100/PB-100-schematic-instance-plan.csv`.

Schematic instance-symbol map CSV:
`hardware/power-board/PB-100/PB-100-schematic-instance-symbol-map.csv`.

Schematic sheet-reference map CSV:
`hardware/power-board/PB-100/PB-100-schematic-sheet-reference-map.csv`.

## Power-path candidates

Candidate MPN CSV:
`hardware/power-board/PB-100/PB-100-power-path-candidates.csv`.

These candidates are allowed for schematic planning only. Final MPN lock still
requires SOA, thermal, clamp-voltage, and assembly-class validation.

Preliminary validation tables:

- `hardware/power-board/PB-100/PB-100-kicad-prep.md`
- `hardware/power-board/PB-100/PB-100-kicad-sheet-manifest.csv`
- `hardware/power-board/PB-100/PB-100-kicad-footprint-plan.csv`
- `hardware/power-board/PB-100/PB-100-schematic-capture-work-queue.csv`
- `hardware/power-board/PB-100/PB-100-symbol-mpn-readiness.csv`
- `hardware/power-board/PB-100/PB-100-symbol-capture-worklist.csv`
- `hardware/power-board/PB-100/PB-100-symbol-pin-evidence.csv`
- `hardware/power-board/PB-100/PB-100-symbol-open-items.md`
- `hardware/power-board/PB-100/PB-100-factory-assembly-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-factory-assembly-sourcing-precheck.csv`
- `hardware/power-board/PB-100/PB-100-factory-assembly-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-garage-connector-fuse-plan.md`
- `hardware/power-board/PB-100/PB-100-garage-connector-fuse-plan.csv`
- `hardware/power-board/PB-100/PB-100-garage-install-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-garage-install-sourcing-precheck.csv`
- `hardware/power-board/PB-100/PB-100-garage-install-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-freeze-review.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-q1-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-q1-derivation-precheck.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-q1-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-protection.md`
- `hardware/power-board/PB-100/PB-100-input-controller-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-input-protection-pin-contract.csv`
- `hardware/power-board/PB-100/PB-100-input-power-design-values.csv`
- `hardware/power-board/PB-100/PB-100-logic-buck-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-rails.md`
- `hardware/power-board/PB-100/PB-100-logic-power-rail-trace.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-freeze-review.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-value-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-value-derivation-precheck.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-budget.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-design-placeholders.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-design-values.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry.md`
- `hardware/power-board/PB-100/PB-100-board-current-budget-trace.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry-trace.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry-map.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry-value-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry-value-derivation-precheck.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-current-monitor-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-output-channel-pin-contract.csv`
- `hardware/power-board/PB-100/PB-100-low-current-output-baseline-trace.csv`
- `hardware/power-board/PB-100/PB-100-high-medium-output-baseline-trace.csv`
- `hardware/power-board/PB-100/PB-100-output-controller-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-output-net-expansion.csv`
- `hardware/power-board/PB-100/PB-100-output-stage-design-values.csv`
- `hardware/power-board/PB-100/PB-100-tvs-load-dump-margin-trace.csv`
- `hardware/power-board/PB-100/PB-100-tvs-load-dump-freeze-review.csv`
- `hardware/power-board/PB-100/PB-100-tvs-overshoot-escape-checklist.csv`
- `hardware/power-board/PB-100/PB-100-tvs-overshoot-validation-precheck.csv`
- `hardware/power-board/PB-100/PB-100-tvs-overshoot-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-mosfet-voltage-margin-review.md`
- `hardware/power-board/PB-100/PB-100-out2-soa.md`
- `hardware/power-board/PB-100/PB-100-out2-soa-envelope.csv`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry.md`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry-trace.csv`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-freeze-checklist.csv`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-derivation-precheck.csv`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry-closeout-precheck.csv`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry-map.csv`
- `hardware/power-board/PB-100/PB-100-thermal-estimates.csv`
- `hardware/power-board/PB-100/PB-100-protection-validation.csv`
- `hardware/power-board/PB-100/PB-100-test-point-plan.csv`
- `hardware/power-board/PB-100/PB-100-fault-response-matrix.csv`
- `hardware/power-board/PB-100/PB-100-review-release-manifest.csv`
- `firmware/configs/hardware/pb-100-capabilities.json`

## Net naming rules

- Follow `hardware/power-board/PB-100/PB-100-net-naming.md`.

## Schematic freeze blockers

- Track schematic-freeze readiness in
  `hardware/power-board/PB-100/PB-100-schematic-freeze-checklist.md`.
- Track cross-artifact review status in
  `hardware/power-board/PB-100/PB-100-schematic-readiness-dashboard.csv`.
- Track every conditional freeze gap in
  `hardware/power-board/PB-100/PB-100-schematic-freeze-gap-register.csv`.
- Track validation coverage for every conditional gate in
  `hardware/power-board/PB-100/PB-100-validation-traceability.csv`.
- Track sheet-level capture execution in
  `hardware/power-board/PB-100/PB-100-schematic-capture-work-queue.csv`.
- Track freeze packet contents in
  `hardware/power-board/PB-100/PB-100-review-release-manifest.csv`.
- Track board-print blocker closure state in
  `hardware/power-board/PB-100/PB-100-board-print-closure-matrix.csv`.
- Validate candidate MPNs in `PB-100-power-path-candidates.csv`.
- Validate ADR-0011 low-current external-controller implementation.
- Confirm high-side switch/controller thermal limits.
- Confirm detailed MOSFET SOA for OUT2 against
  `hardware/power-board/PB-100/PB-100-out2-soa.md`.
- Confirm TVS clamp voltage against high-side controller, MOSFET, and buck
  absolute maximum ratings.
- Confirm connector current ratings and derating.
- Confirm JLCPCB/PCBWay assembly class for selected MPNs.
- Review `hardware/power-board/PB-100/PB-100-board-print-closure-matrix.csv`
  against all active PBREL blockers before any board-print package work.
- Review `hardware/power-board/PB-100/PB-100-factory-assembly-sourcing-precheck.csv`
  against current factory assembly and distributor evidence.
- Review `hardware/power-board/PB-100/PB-100-factory-assembly-closeout-precheck.csv`
  against current factory assembly, inspection, rework, and distributor evidence.
- Review `hardware/power-board/PB-100/PB-100-factory-assembly-freeze-checklist.csv`
  against current factory assembly and distributor evidence.
- Review `hardware/power-board/PB-100/PB-100-garage-install-freeze-checklist.csv`
  against purchase-ready connector, fuse, wire, crimp-tooling, seal, and
  service-access evidence.
- Review `hardware/power-board/PB-100/PB-100-garage-install-sourcing-precheck.csv`
  against purchase-ready connector, fuse, wire, crimp-tooling, seal, enclosure,
  and service-access evidence.
- Review `hardware/power-board/PB-100/PB-100-garage-install-closeout-precheck.csv`
  against purchase-ready connector, fuse, wire, crimp-tooling, seal, enclosure,
  vibration, and service-access evidence.
- Close `production/bom/pb100_assembly_sourcing_recheck.csv` and
  `production/bom/pb100_sourcing_evidence_snapshot.csv` rows before schematic
  freeze.
- Keep `hardware/power-board/PB-100/PB-100-assembly-readiness-trace.csv`
  synchronized with factory and garage ownership before schematic freeze.
