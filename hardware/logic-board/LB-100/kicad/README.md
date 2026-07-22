# LB-100 KiCad Project

Status: `EVT-LAYOUT-AUTHORIZED`; no PCB layout exists yet

This directory contains the reviewed value-bearing LB-100 KiCad schematic and
project-local symbol/footprint libraries.

There is currently no `LB-100.kicad_pcb` file. ADR-0020 authorizes its controlled
creation, placement and routing. Signal-integrity and safety constraints in
`../LB-100-pcb-layout-start-checklist.csv` must close during
`EVT-FAB-REVIEW`. Gerbers, drills, pick-place files, BOM/CPL order packages and
zipped manufacturing outputs remain blocked until `EVT-FAB-AUTHORIZED`.

## Source Documents

- `../LB-100-requirements.md`
- `../LB-100-power-budget-precheck.md`
- `../LB-100-schematic-freeze-checklist.md`
- `../LB-100-pcb-layout-start-checklist.csv`
- `../LB-100-footprint-binding-inventory.csv`
- `../LB-100-mechanical-envelope-inventory.csv`
- `../LB-100-board-release-blocker-register.csv`
- `../../../../production/board-order/three_board_footprint_binding_status.csv`
- `../../../../production/board-order/three_board_mechanical_envelope_status.csv`
- `../../../power-board/PB-100/PB-100-b2b-pin-map.csv`
- `../../../../docs/adr/ADR-0014-lb-fb-baseline-requirements.md`
