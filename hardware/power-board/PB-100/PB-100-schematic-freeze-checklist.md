# PB-100 Schematic Freeze Checklist

Status: Open

This checklist closes PB-100 schematic planning for PCB-layout start. It does
not authorize Gerbers, drills, pick-place, BOM/CPL order packages, manufacturing
ZIP files, fabrication packages, or PCBA orders.

## Completion rule

PB-100 schematic freeze is allowed only when every required gate is `Closed`.
Any change to PB-100 output count, protection model, role-mapping model,
board-level current budget, or CAN1 safety behavior requires a new ADR before
this checklist can close.

ADR-0013 splits pre-layout closure from post-prototype validation. Schematic
freeze and first prototype board-print authorization require calculations,
simulations where applicable, source evidence, schematic hooks, package/footprint
review inputs, and bench procedures. Physical PB-BENCH execution that requires
an assembled PB-100 board is deferred to the post-prototype validation gate and
blocks first motorcycle power, field use, and production release, not the first
prototype PCB fabrication package.

## Status values

- `Closed`: Evidence exists and no schematic blocker remains.
- `Conditional`: Direction is accepted, but schematic-level evidence is still
  required.
- `Open`: Work is not complete.
- `Blocked`: A known conflict must be resolved before schematic freeze.

## Required gates

| Gate | Status | Evidence | Close condition |
|---|---|---|---|
| Architecture baseline | Closed | `docs/architecture/Architecture-Review-v1.0.md`, `docs/adr/ADR-0009-architecture-v1-freeze.md` | Architecture remains frozen and no PB-100 requirement change is pending |
| PB-100 requirements | Closed | `docs/requirements/pb-100-requirements.md`, `docs/adr/ADR-0006-pb-100-baseline-requirements.md` | Requirements changes are handled only through ADR |
| Generic output model | Closed | `docs/adr/ADR-0004-generic-outputs-role-mapping.md`, `hardware/power-board/PB-100/PB-100-output-channel-matrix.csv` | Schematic nets and silkscreen use only neutral `OUT1` through `OUT10` identifiers |
| CAN1 safety policy | Conditional | `docs/adr/ADR-0002-can-read-only-default.md`, `docs/adr/ADR-0015-can1-physical-layer-board-ownership.md`, `docs/can/can-safety.md`, `hardware/power-board/PB-100/PB-100-can1-tx-disable.md`, `hardware/power-board/PB-100/PB-100-can1-tx-disable-trace.csv`, `hardware/power-board/PB-100/PB-100-can1-safety-verification.csv`, `hardware/power-board/PB-100/PB-100-can1-production-dnp-review.csv`, `hardware/power-board/PB-100/PB-100-can1-reset-bench-checklist.csv`, `hardware/power-board/PB-100/PB-100-can1-tx-disable-design-calculation.md`, `hardware/power-board/PB-100/PB-100-can1-default-disable-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-can1-default-disable-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-can1-default-disable-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | PB-side DNP gate pulls and readback topology are netlist-checked; Product Owner must assign CAN1 physical-layer ownership before transceiver TXD and end-to-end no-bypass capture can close |
| Board current budget | Closed | `docs/adr/ADR-0008-pb-100-current-budget.md`, `hardware/power-board/PB-100/PB-100-board-current-budget-trace.csv`, `hardware/power-board/PB-100/PB-100-board-current-budget-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-board-current-budget-design-calculation.md`, `hardware/power-board/PB-100/PB-100-board-current-budget-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-board-current-budget-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-board-current-budget-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-input-power-design-values.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | Input measurement, connector ratings, copper/thermal assumptions, closeout precheck, and firmware-visible budget enforcement are all represented in schematic inputs |
| Board-to-board interface | Conditional | `hardware/power-board/PB-100/PB-100-b2b-interface-trace.csv`, `hardware/power-board/PB-100/PB-100-b2b-lb100-resource-binding.csv`, `hardware/power-board/PB-100/PB-100-b2b-lb100-pin-audit-checklist.csv`, `hardware/power-board/PB-100/PB-100-b2b-interface-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-b2b-interface-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-b2b-lb100-pin-binding-precheck.md`, `hardware/power-board/PB-100/PB-100-b2b-pin-budget.csv`, `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | Connector MPN and electrical pin map are reviewed; official FX18 MF/TH footprint features and mating mechanical audit must close |
| High/medium output stage | Conditional | `docs/adr/ADR-0010-pb-100-power-path-candidate-strategy.md`, `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`, `hardware/power-board/PB-100/PB-100-out2-soa.md`, `hardware/power-board/PB-100/PB-100-high-medium-output-baseline-trace.csv`, `hardware/power-board/PB-100/PB-100-high-medium-output-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-output-stage-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-output-stage-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-output-stage-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | Product Owner selected BUK7S1R2-80M 80 V; OUT2 and per-class transient SOA thermal sourcing fuse and inductive-clamp evidence remain open |
| Low-current output stage | Closed | `docs/adr/ADR-0011-pb-100-low-current-output-stage.md`, `hardware/power-board/PB-100/PB-100-preliminary-validation.md`, `hardware/power-board/PB-100/PB-100-low-current-output-baseline-trace.csv`, `hardware/power-board/PB-100/PB-100-low-current-output-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-output-stage-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-output-stage-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-output-stage-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | OUT5/OUT8/OUT9 external-controller implementation and output closeout precheck are validated without a direct 40 V smart-switch rail |
| Input reverse protection | Conditional | `hardware/power-board/PB-100/PB-100-input-reverse-package-trace.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-q1-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-q1-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-q1-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-protection.md`, `hardware/power-board/PB-100/PB-100-thermal-estimates.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | Product Owner selected BUK7S1R2-80M 80 V LFPAK88; Q1 40 A SOA copper thermal production-source and assembly evidence remain open |
| TVS/load-dump protection | Conditional | `hardware/power-board/PB-100/PB-100-tvs-load-dump-margin-trace.csv`, `hardware/power-board/PB-100/PB-100-tvs-load-dump-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-tvs-overshoot-escape-checklist.csv`, `hardware/power-board/PB-100/PB-100-tvs-overshoot-validation-precheck.csv`, `hardware/power-board/PB-100/PB-100-tvs-overshoot-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-protection-validation.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | Record reproducible clamp-plus-loop peak stress margin waveform temperature and uncertainty below the selected 80 V limit |
| Logic power rails | Closed | `hardware/power-board/PB-100/PB-100-logic-power-rail-trace.csv`, `hardware/power-board/PB-100/PB-100-logic-power-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-logic-power-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-logic-power-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-logic-power-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`, `hardware/power-board/PB-100/PB-100-logic-power-rails.md`, `hardware/power-board/PB-100/PB-100-logic-power-budget.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | Buck and post-regulator strategy plus closeout precheck covers cold crank, load dump, telemetry, and LB-100 supply requirements |
| Current telemetry | Closed | `docs/requirements/pb-100-requirements.md`, `hardware/power-board/PB-100/PB-100-current-telemetry.md`, `hardware/power-board/PB-100/PB-100-current-telemetry-trace.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-design-calculation.md`, `hardware/power-board/PB-100/PB-100-current-telemetry-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-map.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | Per-output current and total input current measurement ranges are selected and closeout precheck is mapped to LB-100 |
| Thermal telemetry | Closed | `docs/requirements/pb-100-requirements.md`, `hardware/power-board/PB-100/PB-100-thermal-telemetry.md`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-trace.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-design-calculation.md`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-map.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | PCB and power-zone temperature sensing strategy plus closeout precheck are selected and mapped to LB-100 |
| Factory assembly readiness | Conditional | `docs/production/component-family-shortlist.md`, `hardware/power-board/PB-100/PB-100-assembly-readiness-trace.csv`, `hardware/power-board/PB-100/PB-100-factory-assembly-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-factory-assembly-sourcing-precheck.csv`, `hardware/power-board/PB-100/PB-100-factory-assembly-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-symbol-mpn-readiness.csv`, `production/bom/factory_bom_draft.csv`, `production/bom/pb100_assembly_sourcing_recheck.csv`, `production/bom/pb100_sourcing_evidence_snapshot.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | Close physical FX18 stack validation BUK7S1R2-80M production status LFPAK88 process and live JLCPCB PCBWay sourcing before final release |
| Garage assembly readiness | Closed | `hardware/power-board/PB-100/PB-100-assembly-readiness-trace.csv`, `hardware/power-board/PB-100/PB-100-garage-install-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-garage-install-sourcing-precheck.csv`, `hardware/power-board/PB-100/PB-100-garage-install-closeout-precheck.csv`, `production/bom/garage_bom_draft.csv`, `production/bom/pb100_symbol_bom_map.csv`, `production/bom/pb100_assembly_sourcing_recheck.csv`, `hardware/power-board/PB-100/PB-100-garage-connector-fuse-plan.md`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | User-installed items are limited to connectors, fuses, enclosure hardware, and wiring with closeout evidence |
| Bench validation plan | Closed | `docs/testing/test-plan.md`, `docs/adr/ADR-0013-pb-100-prelayout-vs-postprototype-validation.md`, `hardware/power-board/PB-100/PB-100-post-prototype-validation-gate.csv` | PB-100 bring-up, protection, thermal, current-budget, and CAN1 listen-only tests are explicitly listed as post-prototype validation gates |

## Active blockers

Architecture remains frozen, but electrical and mechanical implementation gates
are active in `hardware/power-board/PB-100/PB-100-board-release-blocker-register.csv`.
The earlier `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md`
is retracted. The 80 V MOSFET class and official FX18 MF/TH land geometry are
now captured, but actual transient/SOA/thermal evidence, physical stack
validation, factory sourcing, and the other Conditional gates still block PCB
layout.
The LB-100 scaffold also prevents an end-to-end proof that the transceiver TXD
connects only to `CAN1_TXD_SAFE`; proposed ADR-0015 records that this PB-local
net cannot reach the currently LB-owned transceiver through JPB1. PCB layout
and manufacturing output remain blocked pending the ownership decision.

## Resolved blockers

| ID | Resolution | Evidence |
|---|---|---|
| PB-FRZ-001 | OUT5/OUT8/OUT9 moved to external controller plus MOSFET Rev.1 baseline | `docs/adr/ADR-0011-pb-100-low-current-output-stage.md` |
| PB-FRZ-002 | OUT2 startup/inrush SOA envelope and escape strategy defined | `hardware/power-board/PB-100/PB-100-out2-soa.md` |
| PB-FRZ-003 | Dedicated low-Rds input MOSFET strategy selected for 40 A reverse protection | `hardware/power-board/PB-100/PB-100-input-reverse-protection.md` |
| PB-FRZ-004 | `JPB1` board-to-board schematic-planning pin map created | `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv` |
| PB-FRZ-005 | CAN1 TX-disable schematic input created with DNP/open TX default and status readback | `hardware/power-board/PB-100/PB-100-can1-tx-disable.md` |

## Review packet for freeze

Before marking this checklist `Closed`, the review packet must include:

- Updated schematic package.
- Updated review release manifest.
- Updated schematic readiness dashboard.
- Updated board-release blocker register with one row per conditional gate.
- Updated PBREL engineering blocker closeout record.
- Updated schematic capture work queue.
- Updated schematic freeze gap register with one row per conditional gate.
- Updated validation traceability register with one row per conditional gate.
- Final output channel matrix.
- Final output-channel pin contract.
- Final output-controller pin template.
- Final output-net expansion table.
- Final output-stage design value table.
- Final input-protection pin contract.
- Final input-controller pin template.
- Final total-current monitor pin template.
- Final input-power design value table.
- Final logic-buck pin template.
- Final logic-power design value table.
- Final test-point plan with schematic refs, nets, and no footprint/placement
  lock before layout authorization.
- Final fault-response matrix covering safe defaults and firmware responses.
- Final role-free hardware capability manifest aligned with firmware config.
- Final instance-symbol map linking every schematic reference to a symbol key.
- Final sheet-reference map linking every schematic reference to a capture sheet.
- Final schematic net-domain plan with safety rules.
- Final power-path candidate table with selected and alternate MPNs.
- Final symbol/MPN readiness table with concrete symbol and footprint status.
- Final symbol capture worklist with pin evidence and blocked actions.
- Final symbol pin evidence table for created preliminary symbols.
- Final PB-100 symbol-to-BOM map synchronized with factory and garage drafts.
- Thermal and protection validation tables.
- Final PB-100 to LB-100 pin map.
- CAN1 TX-disable schematic input and verification notes.
- CAN1 safety verification matrix and production DNP review.
- Factory and garage BOM drafts synchronized with selected MPNs.
- Assembly sourcing recheck register and sourcing evidence snapshot synchronized
  with critical symbol keys.
- Bench validation plan and post-prototype validation gate for protection,
  telemetry, current budget, and CAN1 listen-only behavior.
- Validation traceability register covering every conditional freeze gate.
- Test-point plan covering rails, telemetry, outputs, and CAN1 safety.
- Fault-response matrix covering safe defaults and firmware actions.
- Capture work queue covering every KiCad sheet and planned schematic reference.
- Review release manifest covering every required freeze-packet artifact.
- Hardware capability manifest checked against PB-100 matrix and firmware
  configuration defaults.
