# PB-100 KiCad Project

Status: Schematic scaffold only; no PCB layout

This directory contains the preliminary KiCad project scaffold for PB-100.

## Current boundary

- `PB-100.kicad_pro`: project metadata scaffold.
- `PB-100.kicad_sch`: top-level schematic note sheet.
- `sym-lib-table`: project-local symbol library table.
- `fp-lib-table`: project-local footprint library table.
- `lib/PB100.kicad_sym`: empty preliminary local symbol library.
- `lib/PB100.pretty/`: empty preliminary local footprint library.

There is intentionally no `PB-100.kicad_pcb` file. PCB layout remains blocked
until schematic freeze.

## Source documents

- `../PB-100-schematic-capture-plan.md`
- `../PB-100-net-naming.md`
- `../PB-100-schematic-instance-plan.csv`
- `../PB-100-kicad-prep.md`
- `../PB-100-kicad-footprint-plan.csv`
- `../PB-100-schematic-freeze-checklist.md`

## Next KiCad work

1. Open `PB-100.kicad_pro` in KiCad.
2. Let KiCad normalize project settings if needed.
3. Create child schematic sheets listed in `PB-100-schematic-capture-plan.md`.
4. Add preliminary symbols only after package drawings are checked.
5. Do not create a PCB layout until the freeze checklist is closed.
