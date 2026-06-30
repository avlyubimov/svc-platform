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
- `hardware/power-board/PB-100/PB-100-schematic-readiness-dashboard.csv`
- `hardware/power-board/PB-100/PB-100-schematic-freeze-checklist.md`
- `hardware/power-board/PB-100/PB-100-schematic-freeze-gap-register.csv`
- `hardware/power-board/PB-100/PB-100-validation-traceability.csv`
- `hardware/power-board/PB-100/PB-100-output-channel-matrix.csv`
- `hardware/power-board/PB-100/PB-100-output-channel-pin-contract.csv`
- `hardware/power-board/PB-100/PB-100-output-controller-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-output-net-expansion.csv`
- `hardware/power-board/PB-100/PB-100-output-stage-design-values.csv`
- `hardware/power-board/PB-100/PB-100-schematic-instance-plan.csv`
- `hardware/power-board/PB-100/PB-100-schematic-instance-symbol-map.csv`
- `hardware/power-board/PB-100/PB-100-schematic-sheet-reference-map.csv`
- `hardware/power-board/PB-100/PB-100-net-naming.md`
- `hardware/power-board/PB-100/PB-100-schematic-net-domain-plan.csv`
- `hardware/power-board/PB-100/PB-100-schematic-capture-plan.md`
- `hardware/power-board/PB-100/kicad/`
- `hardware/power-board/PB-100/PB-100-power-path-candidates.csv`
- `hardware/power-board/PB-100/PB-100-b2b-pin-map.csv`
- `hardware/power-board/PB-100/PB-100-can1-tx-disable.md`
- `hardware/power-board/PB-100/PB-100-can1-safety-verification.csv`
- `hardware/power-board/PB-100/PB-100-current-telemetry.md`
- `hardware/power-board/PB-100/PB-100-current-monitor-pin-template.csv`
- `hardware/power-board/PB-100/PB-100-thermal-telemetry.md`
- `hardware/power-board/PB-100/PB-100-logic-power-rails.md`
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
- `hardware/power-board/PB-100/PB-100-input-reverse-protection.md`
- `hardware/power-board/PB-100/PB-100-logic-power-design-placeholders.csv`
- `hardware/power-board/PB-100/PB-100-out2-soa.md`
- `hardware/power-board/PB-100/PB-100-garage-connector-fuse-plan.md`
- `docs/testing/test-plan.md`
- `production/bom/factory_bom_draft.csv`
- `production/bom/garage_bom_draft.csv`
- `production/bom/pb100_symbol_bom_map.csv`
- `production/bom/pb100_assembly_sourcing_recheck.csv`

## Conditional work before schematic freeze

| Area | Required closure evidence |
|---|---|
| High-side output stages | Final controller/FET/sense schematic values and fault timing |
| Output pin contract | OUT1..OUT10 control, fault, telemetry, load, fuse, and connector nets captured without role-specific names |
| Output controller template | TPS48110 threshold, timing, bootstrap, gate-drive, and current-sense values reviewed per channel class |
| Output net expansion | Every `OUTn_*` template net expanded to `OUT1_*` through `OUT10_*`, with JPB1-facing control/fault/current nets checked |
| Output stage design values | High, medium, and low class threshold, timing, gate-drive, sense, and clamp values selected without role-specific names |
| OUT2 SOA | Data-sheet SOA extraction against `PB-100-out2-soa-envelope.csv` |
| Input reverse protection | Input power values, final MOSFET package choice, Q1 pin evidence, and 40 A copper/thermal review |
| TVS/load dump | Clamp and overshoot margin against every selected downstream device |
| Logic power | LM5164 pin template, logic power design values, final buck current budget, EMI parts, UVLO, feedback, and power-good implementation |
| Current telemetry | INA228 pin template, ADC scaling, filtering, calibration plan, and total-current monitor choice |
| Thermal telemetry | Final sensor values, placement notes, and derating thresholds |
| B2B interface | Connector MPN, pin assignment review, and LB-100 MCU resource binding |
| CAN1 safety | DNP/open TX path, default disable state, status readback, DNP BOM ownership, firmware listen-only behavior, and future ADR hardware-action process |
| Factory assembly | JLCPCB/PCBWay assembly class, distributor continuity, and alternates for critical MPNs; concrete symbol/footprint status from `PB-100-symbol-mpn-readiness.csv` and `pb100_assembly_sourcing_recheck.csv` |
| Garage assembly | Connector, fuse, enclosure, harness items, current derating, wire gauge, crimp tooling, and service access remain user-installable |

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
