# LB-100 KiCad Project

Status: Schematic freeze closed; layout-start preparation open; no PCB layout

This directory contains the reviewed value-bearing LB-100 KiCad schematic and
project-local symbol/footprint libraries.

There is intentionally no `LB-100.kicad_pcb` file. Schematic freeze is closed,
but KiCad board import remains blocked until the signal-integrity and safety
layout-model row in `../LB-100-pcb-layout-start-checklist.csv` closes. Gerbers,
drills, pick-place files, BOM/CPL order
packages, and zipped manufacturing outputs remain blocked until layout review
and order evidence close.

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
