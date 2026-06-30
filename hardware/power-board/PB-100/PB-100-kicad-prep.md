# PB-100 KiCad Preparation Plan

Status: Preliminary symbol/footprint planning; no PCB layout

This plan identifies schematic-symbol and footprint preparation work that can
start before PCB layout. It does not authorize placement, routing, board outline,
Gerber generation, or footprint use without package drawing verification.

## Rules

- Do not start PCB layout from this file.
- Use KiCad stock footprints only when package dimensions match the vendor data
  sheet.
- Create custom footprints for power packages, exposed pads, or non-standard pin
  counts.
- Keep DNP/default-open CAN1 TX hardware visible in the schematic.
- Keep output names generic: `OUT1` through `OUT10`.
- Recheck JLCPCB/PCBWay assembly class before locking final footprints.

## Footprint inventory

Detailed inventory CSV:
`hardware/power-board/PB-100/PB-100-kicad-footprint-plan.csv`.

Symbol/MPN readiness CSV:
`hardware/power-board/PB-100/PB-100-symbol-mpn-readiness.csv`.

The inventories are package-focused and source-aware, but they are not final MPN
locks.

KiCad scaffold directory:
`hardware/power-board/PB-100/kicad/`.

## Allowed prep work

- Create schematic symbols for selected candidate families.
- Convert each `PB-100-symbol-mpn-readiness.csv` row marked `Critical=yes` into
  a concrete schematic symbol or documented class symbol before schematic
  freeze.
- Collect package drawings and courtyard requirements.
- Create draft footprints in a separate library branch or clearly marked
  preliminary library.
- Add 3D model placeholders only after footprint dimensions are verified.
- Use `PB100_*_PRELIM` symbols only as abstract schematic-capture scaffolding;
  replace them before schematic freeze.

## Blocked work

- PCB layout.
- Copper pours and current-carrying trace geometry.
- Connector placement.
- Board outline.
- Gerber, Pick&Place, or assembly output generation.
