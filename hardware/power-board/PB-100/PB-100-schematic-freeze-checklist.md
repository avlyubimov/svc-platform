# PB-100 Schematic Freeze Checklist

Status: Open

This checklist is the gate between PB-100 schematic planning and PCB layout. It
does not authorize KiCad PCB layout work.

## Completion rule

PB-100 schematic freeze is allowed only when every required gate is `Closed`.
Any change to PB-100 output count, protection model, role-mapping model,
board-level current budget, or CAN1 safety behavior requires a new ADR before
this checklist can close.

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
| CAN1 safety policy | Conditional | `docs/adr/ADR-0002-can-read-only-default.md`, `docs/can/can-safety.md`, `hardware/power-board/PB-100/PB-100-can1-tx-disable.md`, `hardware/power-board/PB-100/PB-100-can1-tx-disable-trace.csv`, `hardware/power-board/PB-100/PB-100-can1-safety-verification.csv`, `hardware/power-board/PB-100/PB-100-can1-production-dnp-review.csv`, `hardware/power-board/PB-100/PB-100-can1-reset-bench-checklist.csv`, `hardware/power-board/PB-100/PB-100-can1-tx-disable-design-calculation.md`, `hardware/power-board/PB-100/PB-100-can1-default-disable-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-can1-default-disable-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-can1-default-disable-closeout-precheck.csv` | Schematic implements DNP/open TX path, default disable state, production DNP ownership, LB-100-visible disabled status, and closeout precheck boundary |
| Board current budget | Conditional | `docs/adr/ADR-0008-pb-100-current-budget.md`, `hardware/power-board/PB-100/PB-100-board-current-budget-trace.csv`, `hardware/power-board/PB-100/PB-100-board-current-budget-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-board-current-budget-design-calculation.md`, `hardware/power-board/PB-100/PB-100-board-current-budget-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-board-current-budget-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-board-current-budget-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-input-power-design-values.csv` | Input measurement, connector ratings, copper/thermal assumptions, closeout precheck, and firmware-visible budget enforcement are all represented in schematic inputs |
| Board-to-board interface | Conditional | `hardware/power-board/PB-100/PB-100-b2b-interface-trace.csv`, `hardware/power-board/PB-100/PB-100-b2b-lb100-resource-binding.csv`, `hardware/power-board/PB-100/PB-100-b2b-lb100-pin-audit-checklist.csv`, `hardware/power-board/PB-100/PB-100-b2b-interface-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-b2b-interface-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-b2b-lb100-pin-binding-precheck.md`, `hardware/power-board/PB-100/PB-100-b2b-pin-budget.csv`, `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv` | Connector MPN, LB-100 resource-class binding, exact LB-100 MCU pin binding, and B2B closeout precheck are reviewed against the pin map |
| High/medium output stage | Conditional | `docs/adr/ADR-0010-pb-100-power-path-candidate-strategy.md`, `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`, `hardware/power-board/PB-100/PB-100-out2-soa.md`, `hardware/power-board/PB-100/PB-100-high-medium-output-baseline-trace.csv`, `hardware/power-board/PB-100/PB-100-high-medium-output-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-output-stage-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-output-stage-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-output-stage-closeout-precheck.csv` | Controller, MOSFET, sense path, fuse, inductive-load protection, and output closeout precheck are validated per output class |
| Low-current output stage | Conditional | `docs/adr/ADR-0011-pb-100-low-current-output-stage.md`, `hardware/power-board/PB-100/PB-100-preliminary-validation.md`, `hardware/power-board/PB-100/PB-100-low-current-output-baseline-trace.csv`, `hardware/power-board/PB-100/PB-100-low-current-output-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-output-stage-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-output-stage-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-output-stage-closeout-precheck.csv` | OUT5/OUT8/OUT9 external-controller implementation and output closeout precheck are validated without a direct 40 V smart-switch rail |
| Input reverse protection | Conditional | `hardware/power-board/PB-100/PB-100-input-reverse-package-trace.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-q1-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-q1-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-q1-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-protection.md`, `hardware/power-board/PB-100/PB-100-thermal-estimates.csv` | Selected input MOSFET package, Q1 closeout precheck, and copper strategy pass 40 A thermal and SOA review |
| TVS/load-dump protection | Conditional | `hardware/power-board/PB-100/PB-100-tvs-load-dump-margin-trace.csv`, `hardware/power-board/PB-100/PB-100-tvs-load-dump-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-tvs-overshoot-escape-checklist.csv`, `hardware/power-board/PB-100/PB-100-tvs-overshoot-validation-precheck.csv`, `hardware/power-board/PB-100/PB-100-tvs-overshoot-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-protection-validation.csv` | Clamp strategy and TVS closeout precheck are compatible with every downstream absolute maximum rating |
| Logic power rails | Conditional | `hardware/power-board/PB-100/PB-100-logic-power-rail-trace.csv`, `hardware/power-board/PB-100/PB-100-logic-power-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-logic-power-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-logic-power-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-logic-power-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`, `hardware/power-board/PB-100/PB-100-logic-power-rails.md`, `hardware/power-board/PB-100/PB-100-logic-power-budget.csv` | Buck and post-regulator strategy plus closeout precheck covers cold crank, load dump, telemetry, and LB-100 supply requirements |
| Current telemetry | Conditional | `docs/requirements/pb-100-requirements.md`, `hardware/power-board/PB-100/PB-100-current-telemetry.md`, `hardware/power-board/PB-100/PB-100-current-telemetry-trace.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-design-calculation.md`, `hardware/power-board/PB-100/PB-100-current-telemetry-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-map.csv` | Per-output current and total input current measurement ranges are selected and closeout precheck is mapped to LB-100 |
| Thermal telemetry | Conditional | `docs/requirements/pb-100-requirements.md`, `hardware/power-board/PB-100/PB-100-thermal-telemetry.md`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-trace.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-design-calculation.md`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-map.csv` | PCB and power-zone temperature sensing strategy plus closeout precheck are selected and mapped to LB-100 |
| Factory assembly readiness | Conditional | `docs/production/component-family-shortlist.md`, `hardware/power-board/PB-100/PB-100-assembly-readiness-trace.csv`, `hardware/power-board/PB-100/PB-100-factory-assembly-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-factory-assembly-sourcing-precheck.csv`, `hardware/power-board/PB-100/PB-100-factory-assembly-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-symbol-mpn-readiness.csv`, `production/bom/factory_bom_draft.csv`, `production/bom/pb100_assembly_sourcing_recheck.csv`, `production/bom/pb100_sourcing_evidence_snapshot.csv` | Critical components have at least two alternatives and assembly-source closeout status is checked |
| Garage assembly readiness | Conditional | `hardware/power-board/PB-100/PB-100-assembly-readiness-trace.csv`, `hardware/power-board/PB-100/PB-100-garage-install-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-garage-install-sourcing-precheck.csv`, `production/bom/garage_bom_draft.csv`, `production/bom/pb100_symbol_bom_map.csv`, `production/bom/pb100_assembly_sourcing_recheck.csv`, `hardware/power-board/PB-100/PB-100-garage-connector-fuse-plan.md` | User-installed items are limited to connectors, fuses, enclosure hardware, and wiring |
| Bench validation plan | Closed | `docs/testing/test-plan.md` | PB-100 bring-up, protection, thermal, current-budget, and CAN1 listen-only tests are explicitly listed |

## Active blockers

No unresolved architecture-planning blockers remain. Board-release blockers are
still active for every `Conditional` gate and are tracked in
`hardware/power-board/PB-100/PB-100-board-release-blocker-register.csv`.
PCB layout and manufacturing output remain blocked until that register is empty
because every required gate has moved to `Closed`.

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
- Bench validation plan for protection, telemetry, current budget, and CAN1
  listen-only behavior.
- Validation traceability register covering every conditional freeze gate.
- Test-point plan covering rails, telemetry, outputs, and CAN1 safety.
- Fault-response matrix covering safe defaults and firmware actions.
- Capture work queue covering every KiCad sheet and planned schematic reference.
- Review release manifest covering every required freeze-packet artifact.
- Hardware capability manifest checked against PB-100 matrix and firmware
  configuration defaults.
