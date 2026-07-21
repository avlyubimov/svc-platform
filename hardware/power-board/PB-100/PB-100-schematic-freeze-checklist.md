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

ADR-0013 and ADR-0017 split pre-layout, post-layout, and prototype validation.
Schematic freeze and `LAYOUT-ONLY` require calculations, simulations where
applicable, source evidence, schematic hooks, package/footprint review inputs,
and bench procedures. Reviewed copper/current/thermal/clamp-loop extraction is
then required for `PROTO-ONLY`. Physical PB-BENCH execution that requires an
assembled PB-100 board blocks first motorcycle power, field use, and production
release, not controlled layout or the engineering-prototype fabrication step.

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
| PB-100 requirements | Closed | `docs/requirements/pb-100-requirements.md`, `docs/adr/ADR-0006-pb-100-baseline-requirements.md`, `docs/adr/ADR-0016-pb-100-load-dump-design-requirement.md` | Requirements changes are handled only through ADR |
| Generic output model | Closed | `docs/adr/ADR-0004-generic-outputs-role-mapping.md`, `hardware/power-board/PB-100/PB-100-output-channel-matrix.csv` | Schematic nets and silkscreen use only neutral `OUT1` through `OUT10` identifiers |
| CAN1 safety policy | Closed | `docs/adr/ADR-0002-can-read-only-default.md`, `docs/adr/ADR-0015-can1-physical-layer-board-ownership.md`, `hardware/power-board/PB-100/PB-100-can1-tx-disable-trace.csv`, `hardware/power-board/PB-100/PB-100-can1-safety-verification.csv`, `hardware/power-board/PB-100/PB-100-can1-production-dnp-review.csv`, `hardware/power-board/PB-100/PB-100-can1-default-disable-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-can1-default-disable-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-can1-default-disable-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-can1-physical-closeout.md`, `hardware/power-board/PB-100/PB-100-can1-reset-bench-checklist.csv` | Exported netlist proves the dual-DNP no-bypass TX chain, physical pulls/readback, silent default and RX-only return; exact DTM04-4P/DTM06-4S harness is frozen and PB-BENCH-012 remains post-prototype |
| Board current budget | Closed | `docs/adr/ADR-0008-pb-100-current-budget.md`, `hardware/power-board/PB-100/PB-100-board-current-budget-trace.csv`, `hardware/power-board/PB-100/PB-100-board-current-budget-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-board-current-budget-design-calculation.md`, `hardware/power-board/PB-100/PB-100-board-current-budget-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-board-current-budget-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-board-current-budget-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-input-power-design-values.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | Input measurement, connector ratings, copper/thermal assumptions, closeout precheck, and firmware-visible budget enforcement are all represented in schematic inputs |
| Board-to-board interface | Closed | `hardware/power-board/PB-100/PB-100-fx18-paired-stack-closeout.md`, `hardware/power-board/PB-100/PB-100-b2b-interface-trace.csv`, `hardware/power-board/PB-100/PB-100-b2b-interface-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-b2b-interface-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-b2b-lb100-resource-binding.csv`, `hardware/power-board/PB-100/PB-100-b2b-lb100-pin-audit-checklist.csv`, `hardware/power-board/PB-100/PB-100-b2b-lb100-pin-binding-precheck.md`, `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv`, `hardware/logic-board/LB-100/kicad/LB-100.kicad_sch` | Corrected P-SV10 plus S-SV10 pair closes the official 20 mm stack, four 20.3 +/-0.127 mm spacers, six official plated lands, four GND MF circuits, shared holes, mirrored pin-1 fixture, and inspection plan; PB-BENCH-014/015 remain post-prototype per ADR-0013 |
| High/medium output stage | Conditional | `docs/adr/ADR-0010-pb-100-power-path-candidate-strategy.md`, `hardware/power-board/PB-100/PB-100-high-medium-output-baseline-trace.csv`, `hardware/power-board/PB-100/PB-100-high-medium-output-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-output-stage-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-output-stage-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-output-stage-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-output-soa-evidence.csv`, `hardware/power-board/PB-100/PB-100-output-stage-design-values.csv`, `hardware/power-board/PB-100/PB-100-out2-soa.md` | Generated thresholds, fuse-compatible SOA, exact 80 V TOLL and local clamp selection pass; promote the accepted passives and DCL101-DCL110 into the value-bearing sheets before freeze |
| Low-current output stage | Closed | `docs/adr/ADR-0011-pb-100-low-current-output-stage.md`, `hardware/power-board/PB-100/PB-100-preliminary-validation.md`, `hardware/power-board/PB-100/PB-100-low-current-output-baseline-trace.csv`, `hardware/power-board/PB-100/PB-100-low-current-output-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-output-stage-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-output-stage-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-output-stage-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | OUT5/OUT8/OUT9 external-controller implementation and output closeout precheck are validated without a direct 40 V smart-switch rail |
| Input reverse protection | Conditional | `docs/adr/ADR-0018-pb-100-active-surge-stopper-and-passive-q1-cooling.md`, `hardware/power-board/PB-100/PB-100-input-reverse-package-trace.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-q1-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-q1-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-q1-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-input-reverse-protection.md`, `hardware/power-board/PB-100/PB-100-input-q1-evidence.csv`, `hardware/power-board/PB-100/PB-100-staged-release-readiness.csv`, `hardware/power-board/PB-100/kicad/sheets/input-protection.kicad_sch` | PBREL-006 design selection is Closed for IAUT300N08S5N012ATMA2 and passive <=6.20 K/W thermal target; close this schematic gate after LM74930-Q1 gate/peripheral values are promoted and reviewed. Extraction and PB-BENCH-010 remain later gates |
| TVS/load-dump protection | Conditional | `docs/adr/ADR-0016-pb-100-load-dump-design-requirement.md`, `docs/adr/ADR-0018-pb-100-active-surge-stopper-and-passive-q1-cooling.md`, `hardware/power-board/PB-100/PB-100-tvs-load-dump-margin-trace.csv`, `hardware/power-board/PB-100/PB-100-tvs-load-dump-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-tvs-overshoot-escape-checklist.csv`, `hardware/power-board/PB-100/PB-100-tvs-overshoot-validation-precheck.csv`, `hardware/power-board/PB-100/PB-100-tvs-overshoot-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-surge-stopper-evidence.csv`, `hardware/power-board/PB-100/PB-100-input-q2-evidence.csv`, `hardware/power-board/PB-100/PB-100-protection-validation.csv`, `hardware/power-board/PB-100/PB-100-staged-release-readiness.csv`, `hardware/power-board/PB-100/kicad/sheets/input-protection.kicad_sch` | PBREL-007 pre-layout remains Conditional for LM74930-Q1 hard cutoff <=55 V and 150 V Q2; 24 rows include 150 C initial Tj and separate 7 us fully-enhanced deglitch from the provisional 0.31 us Qgd transition. The 2.08x graph-derived screen does not authorize layout until a qualified maximum-bound trajectory exists; extracted-loop review and PB-BENCH-004 remain later gates |
| Logic power rails | Closed | `hardware/power-board/PB-100/PB-100-logic-power-rail-trace.csv`, `hardware/power-board/PB-100/PB-100-logic-power-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-logic-power-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-logic-power-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-logic-power-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`, `hardware/power-board/PB-100/PB-100-logic-power-rails.md`, `hardware/power-board/PB-100/PB-100-logic-power-budget.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | Buck and post-regulator strategy plus closeout precheck covers cold crank, load dump, telemetry, and LB-100 supply requirements |
| Current telemetry | Closed | `docs/requirements/pb-100-requirements.md`, `hardware/power-board/PB-100/PB-100-current-telemetry.md`, `hardware/power-board/PB-100/PB-100-current-telemetry-trace.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-design-calculation.md`, `hardware/power-board/PB-100/PB-100-current-telemetry-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-current-telemetry-map.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | Per-output current and total input current measurement ranges are selected and closeout precheck is mapped to LB-100 |
| Thermal telemetry | Closed | `docs/requirements/pb-100-requirements.md`, `hardware/power-board/PB-100/PB-100-thermal-telemetry.md`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-trace.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-freeze-review.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-design-calculation.md`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-value-derivation-precheck.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-thermal-telemetry-map.csv`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | PCB and power-zone temperature sensing strategy plus closeout precheck are selected and mapped to LB-100 |
| Factory assembly readiness | Conditional | `hardware/power-board/PB-100/PB-100-assembly-readiness-trace.csv`, `hardware/power-board/PB-100/PB-100-factory-assembly-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-factory-assembly-sourcing-precheck.csv`, `hardware/power-board/PB-100/PB-100-factory-assembly-closeout-precheck.csv`, `hardware/power-board/PB-100/PB-100-factory-production-evidence.csv`, `production/bom/factory_bom_draft.csv`, `production/bom/pb100_assembly_sourcing_recheck.csv`, `production/bom/pb100_sourcing_evidence_snapshot.csv` | Exact active TOLL source route, alternatives, paste/DNP/inspection controls and honest consignment path close PBREL-011; synchronize the final passive/clamp BOM before schematic freeze, with quote/DFM/FAI retained as later production gates |
| Garage assembly readiness | Closed | `hardware/power-board/PB-100/PB-100-assembly-readiness-trace.csv`, `hardware/power-board/PB-100/PB-100-garage-install-freeze-checklist.csv`, `hardware/power-board/PB-100/PB-100-garage-install-sourcing-precheck.csv`, `hardware/power-board/PB-100/PB-100-garage-install-closeout-precheck.csv`, `production/bom/garage_bom_draft.csv`, `production/bom/pb100_symbol_bom_map.csv`, `production/bom/pb100_assembly_sourcing_recheck.csv`, `hardware/power-board/PB-100/PB-100-garage-connector-fuse-plan.md`, `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md` | User-installed items are limited to connectors, fuses, enclosure hardware, and wiring with closeout evidence |
| Bench validation plan | Closed | `docs/testing/test-plan.md`, `docs/adr/ADR-0013-pb-100-prelayout-vs-postprototype-validation.md`, `hardware/power-board/PB-100/PB-100-post-prototype-validation-gate.csv` | PB-100 bring-up, protection, thermal, current-budget, and CAN1 listen-only tests are explicitly listed as post-prototype validation gates |

## Active blockers

Architecture remains frozen and the PBREL register has zero active design
blockers. PBREL-006 is `LAYOUT-ONLY`, but PBREL-007 pre-layout is Conditional
and aggregate authorization is `BLOCKED`, while
separate schematic implementation gates remain active in this checklist.
The earlier `hardware/power-board/PB-100/PB-100-schematic-review-closeout.md`
is retracted. The 80 V MOSFET class and official FX18 MF/TH land geometry are
now captured and the corrected FX18 input is closed. ADR-0018 fixes passive Q1
cooling and replaces the rejected single-SM8S33AHM3/I branch with LM74930-Q1
hard cutoff and a 150 V raw-side Q2.
ADR-0015 Accepted assigns the CAN1 physical layer to PB-100, and the exported
PB netlist proves that transceiver TXD is driven only by `CAN1_TXD_SAFE` while
RXD returns only on `CAN1_RX_ROUTE`. PCB layout and manufacturing output remain
blocked in the current state by controlled surge-stopper/passive promotion,
final value-bearing schematic review,
Product Owner freeze approval, and the layout-start checklist—not by
post-layout extraction or pre-hardware bench prerequisites.

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
- Updated staged release readiness ledger with ordered PBREL-006/PBREL-007
  pre-layout, post-layout, and prototype-qualification evidence.
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
