# FB-100 KiCad Project

Status: Schematic freeze closed; layout-start preparation open; no PCB layout

This directory contains a non-layout KiCad project for FB-100 schematic
planning.

There is intentionally no `FB-100.kicad_pcb` file. Schematic freeze is closed,
but KiCad board import remains blocked until
`../FB-100-pcb-layout-start-checklist.csv` closes footprint binding and
mechanical envelope gates. Gerbers, drills, pick-place files, BOM/CPL order
packages, and zipped manufacturing outputs remain blocked until layout review
and order evidence close.

## Source Documents

- `../FB-100-requirements.md`
- `../FB-100-schematic-freeze-checklist.md`
- `../FB-100-pcb-layout-start-checklist.csv`
- `../FB-100-footprint-binding-inventory.csv`
- `../FB-100-mechanical-envelope-inventory.csv`
- `../FB-100-board-release-blocker-register.csv`
- `../../../../production/board-order/three_board_footprint_binding_status.csv`
- `../../../../production/board-order/three_board_mechanical_envelope_status.csv`
- `../../../logic-board/LB-100/LB-100-requirements.md`
- `../../../../docs/adr/ADR-0014-lb-fb-baseline-requirements.md`
