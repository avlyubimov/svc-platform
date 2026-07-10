# PB-100 Schematic Readiness Review

Status: Ready for schematic review; not frozen

Review date: 2026-06-30

This snapshot summarizes the PB-100 schematic-planning package after resolving
all active planning blockers. It does not authorize PCB layout.

## Outcome

- Architecture v1.0 and PB-100 baseline requirements are frozen by ADR.
- No active PB-100 planning blockers remain in the freeze checklist.
- All formerly open schematic-readiness gates now have evidence.
- Remaining gates are conditional because they need schematic-level evidence,
  final component sourcing checks, SOA extraction, connector derating, and
  thermal/copper review.

## Review packet

The schematic review packet consists of:

- `hardware/power-board/PB-100/PB-100-schematic-package.md`
- `hardware/power-board/PB-100/PB-100-review-release-manifest.csv`
- `hardware/power-board/PB-100/PB-100-schematic-readiness-dashboard.csv`
- `hardware/power-board/PB-100/PB-100-schematic-freeze-checklist.md`
- `hardware/power-board/PB-100/PB-100-schematic-freeze-gap-register.csv`
- `hardware/power-board/PB-100/PB-100-validation-traceability.csv`
- `hardware/power-board/PB-100/PB-100-schematic-capture-work-queue.csv`
- `hardware/power-board/PB-100/PB-100-test-point-plan.csv`
- `hardware/power-board/PB-100/PB-100-fault-response-matrix.csv`
- `firmware/configs/hardware/pb-100-capabilities.json`
- `hardware/power-board/PB-100/PB-100-output-channel-matrix.csv`
- `hardware/power-board/PB-100/PB-100-output-channel-pin-contract.csv`
- `hardware/power-board/PB-100/PB-100-output-controller-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-output-net-expansion.csv`
- `hardware/power-board/PB-100/PB-100-output-stage-design-values.csv`
- `hardware/power-board/PB-100/PB-100-low-current-output-baseline-trace.csv`
- `hardware/power-board/PB-100/PB-100-high-medium-output-baseline-trace.csv`
- `hardware/power-board/PB-100/PB-100-schematic-instance-plan.csv`
- `hardware/power-board/PB-100/PB-100-schematic-instance-symbol-map.csv`
- `hardware/power-board/PB-100/PB-100-schematic-sheet-reference-map.csv`
- `hardware/power-board/PB-100/PB-100-net-naming.md`
- `hardware/power-board/PB-100/PB-100-schematic-net-domain-plan.csv`
- `hardware/power-board/PB-100/PB-100-schematic-capture-plan.md`
- `hardware/power-board/PB-100/kicad/`
- `hardware/power-board/PB-100/kicad/PB-100.kicad_sch`
- `hardware/power-board/PB-100/kicad/lib/PB100.kicad_sym`
- `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`
- `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv`
- `hardware/power-board/PB-100/PB-100-b2b-interface-trace.csv`
- `hardware/power-board/PB-100/PB-100-b2b-lb100-resource-binding.csv`
- `hardware/power-board/PB-100/PB-100-can1-tx-disable.md`
- `hardware/power-board/PB-100/PB-100-can1-tx-disable-trace.csv`
- `hardware/power-board/PB-100/PB-100-can1-safety-verification.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry.md`
- `hardware/power-board/PB-100/PB-100-board-current-budget-trace.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry-trace.csv`
- `hardware/power-board/PB-100/PB-100-current-monitor-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry.md`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry-trace.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-rails.md`
- `hardware/power-board/PB-100/PB-100-logic-power-rail-trace.csv`
- `hardware/power-board/PB-100/PB-100-logic-buck-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-design-values.csv`
- `hardware/power-board/PB-100/PB-100-kicad-prep.md`
- `hardware/power-board/PB-100/PB-100-kicad-sheet-manifest.csv`
- `hardware/power-board/PB-100/PB-100-symbol-mpn-readiness.csv`
- `hardware/power-board/PB-100/PB-100-symbol-capture-worklist.csv`
- `hardware/power-board/PB-100/PB-100-symbol-pin-evidence.csv`
- `hardware/power-board/PB-100/PB-100-input-controller-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-input-protection-pin-contract.csv`
- `hardware/power-board/PB-100/PB-100-input-power-design-values.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-package-trace.csv`
- `hardware/power-board/PB-100/PB-100-input-reverse-protection.md`
- `hardware/power-board/PB-100/PB-100-tvs-load-dump-margin-trace.csv`
- `hardware/power-board/PB-100/PB-100-logic-power-design-placeholders.csv`
- `hardware/power-board/PB-100/PB-100-out2-soa.md`
- `hardware/power-board/PB-100/PB-100-garage-connector-fuse-plan.md`
- `docs/testing/test-plan.md`
- `production/bom/factory_bom_draft.csv`
- `production/bom/garage_bom_draft.csv`
- `production/bom/pb100_symbol_bom_map.csv`
- `production/bom/pb100_assembly_sourcing_recheck.csv`
- `production/bom/pb100_sourcing_evidence_snapshot.csv`
- `hardware/power-board/PB-100/PB-100-assembly-readiness-trace.csv`

## Conditional work before schematic freeze

| Area | Required closure evidence |
|---|---|
| High-side output stages | Final controller/FET/sense schematic values and fault timing |
| Output pin contract | OUT1..OUT10 control, fault, telemetry, load, fuse, and connector nets captured without role-specific names |
| Output controller template | TPS48110 threshold, timing, bootstrap, gate-drive, and current-sense values reviewed per channel class |
| Output net expansion | Every `OUTn_*` template net expanded to `OUT1_*` through `OUT10_*`, with JPB1-facing control/fault/current nets checked |
| Output stage design values | High, medium, and low class threshold, timing, gate-drive, sense, and clamp values selected without role-specific names |
| High/medium baseline trace | OUT2 and medium-current groups are machine-checked against matrix, config, telemetry, contracts, SOA, and per-class design values |
| Low-current baseline trace | OUT5/OUT8/OUT9 are machine-checked against ADR-0011, capabilities, matrix, config, and output contracts |
| Capture work queue | Every KiCad sheet has source artifacts, refs, blockers, freeze evidence, and explicit no-layout boundary |
| Review release manifest | Every required freeze-packet artifact exists and remains synchronized with validation hooks |
| OUT2 SOA | Data-sheet SOA extraction against `PB-100-out2-soa-envelope.csv` |
| Input reverse protection | Input reverse package trace, input power values, Q1 pin evidence, and 40 A copper/thermal review |
| TVS/load dump | Clamp and overshoot margin trace against every selected downstream voltage class |
| Logic power | Logic power rail trace, LM5164 pin template, logic power design values, final buck current budget, EMI parts, UVLO, feedback, and power-good implementation |
| Current telemetry | Current telemetry trace, INA228 pin template, board-current budget trace, ADC scaling, filtering, calibration plan, and total-current monitor choice |
| Thermal telemetry | Thermal telemetry trace, final sensor values, divider values, placement notes, calibration, and derating thresholds |
| Test points | Bring-up, telemetry, output, fused-output, and CAN1 safety test points are defined without footprint or placement lock |
| Fault response | Input, logic, B2B, output, thermal, current-budget, CAN1, and identity faults have safe hardware defaults and firmware responses |
| Hardware capabilities | Role-free PB-100 capabilities align with output matrix, telemetry maps, config defaults, and CAN1 read-only policy |
| B2B interface | JPB1 connector trace, pin assignment review, CAN1 safety crossing, LB-100 resource-class binding, and exact LB-100 MCU pin binding |
| CAN1 safety | CAN1 TX-disable trace, DNP/open TX path, default disable state, status readback, DNP BOM ownership, firmware listen-only behavior, and future ADR hardware-action process |
| Factory assembly | JLCPCB/PCBWay assembly class, distributor continuity, and alternates for critical MPNs; ownership is traced in `PB-100-assembly-readiness-trace.csv`, `PB-100-symbol-mpn-readiness.csv`, `pb100_assembly_sourcing_recheck.csv`, and `pb100_sourcing_evidence_snapshot.csv` |
| Garage assembly | Connector, fuse, enclosure, harness items, current derating, wire gauge, crimp tooling, and service access remain user-installable per `PB-100-assembly-readiness-trace.csv` |

Each conditional area must also have a matching row in
`hardware/power-board/PB-100/PB-100-validation-traceability.csv` before the
freeze checklist can close.

## Allowed next work

- Prepare schematic capture.
- Prepare or review preliminary KiCad symbols/footprints for selected candidate
  packages.
- Recheck assembly availability for selected and alternate MPNs.
- Build schematic review notes and calculations.

## Still blocked

- PCB layout.
- Gerber generation.
- PB-100 requirement changes without ADR.
- Any vehicle-CAN TX enable path without a new ADR and explicit hardware action.
