# PB-100 Schematic Capture Plan

Status: Schematic-capture input; no PCB layout

This plan converts the PB-100 schematic-planning package into concrete schematic
capture tasks. It does not freeze the schematic and does not authorize PCB
layout.

## Capture structure

KiCad scaffold directory:
`hardware/power-board/PB-100/kicad/`.

| Sheet | Purpose | Primary artifacts |
|---|---|---|
| `PB-100.kicad_sch` | Top-level sheet, title block, review notes, sheet links | This file plus all child sheets |
| `input-protection.kicad_sch` | Battery input, reverse protection, TVS, input current/voltage sense | `PB-100-input-reverse-protection.md`, `PB-100-protection-validation.csv` |
| `logic-power.kicad_sch` | Protected `PB_5V_OUT`, power-good, UVLO, local filters | `PB-100-logic-power-rails.md`, `PB-100-logic-power-budget.csv` |
| `output-channel-template.kicad_sch` | Generic high-side output channel pattern | `PB-100-output-channel-matrix.csv`, `PB-100-current-telemetry.md` |
| `outputs-1-10.kicad_sch` | Ten instantiated generic outputs | `PB-100-schematic-instance-plan.csv` |
| `telemetry.kicad_sch` | Total input current, voltage, thermal sensors, board ID | `PB-100-current-telemetry-map.csv`, `PB-100-thermal-telemetry-map.csv` |
| `b2b-interface.kicad_sch` | `JPB1` PB-100 to LB-100 interface | `PB-100-b2b-pin-map.csv` |
| `can1-safety.kicad_sch` | CAN1 TX disable/readback and DNP/open TX path | `PB-100-can1-tx-disable.md` |

Placeholder child sheets are tracked in
`hardware/power-board/PB-100/kicad/sheets/`.

KiCad sheet manifest:
`hardware/power-board/PB-100/PB-100-kicad-sheet-manifest.csv`.

Reference-to-sheet assignment is tracked in
`hardware/power-board/PB-100/PB-100-schematic-sheet-reference-map.csv`.

Schematic net-domain rules are tracked in
`hardware/power-board/PB-100/PB-100-schematic-net-domain-plan.csv`.

## Capture order

1. Open `hardware/power-board/PB-100/kicad/PB-100.kicad_pro`.
2. Let KiCad normalize project metadata if needed.
3. Create local symbols and footprint aliases for candidate packages.
4. Check every critical row in `PB-100-symbol-mpn-readiness.csv` has a matching
   work item in `PB-100-symbol-capture-worklist.csv`.
5. Capture `b2b-interface.kicad_sch` from the `JPB1` pin map.
6. Capture `input-protection.kicad_sch` and `logic-power.kicad_sch`.
7. Capture one generic output template and copy it to OUT1 through OUT10.
8. Capture current and thermal telemetry sheets.
9. Add CAN1 TX-disable hardware with Rev.1 TX route DNP/open.
10. Run schematic ERC and update the freeze checklist with evidence.

## Schematic rules

- Use only neutral output names: `OUT1` through `OUT10`.
- Do not place accessory role names in net names, symbols, or silkscreen fields.
- Keep configuration defaults in configuration and vehicle-profile files only.
- Add explicit schematic notes for DNP/open CAN1 TX path.
- Mark all conditional MPN choices as `Candidate` or `DNP alternate`.
- Do not create `PB-100.kicad_pcb` until schematic freeze is closed.

## Required review outputs

- ERC report.
- Updated instance table with final references.
- Updated instance-symbol map linking every reference to a symbol key.
- Updated sheet-reference map linking every reference to a capture sheet.
- Updated symbol/MPN readiness table with concrete symbol and footprint status.
- Updated symbol capture worklist with pin evidence and blocked actions.
- Updated symbol pin evidence table for created preliminary symbols.
- Updated BOM draft synchronized with chosen schematic symbols.
- Updated freeze checklist evidence for all conditional gates.
