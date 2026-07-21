# FB-100 KiCad Project

Status: Schematic freeze closed; controlled placement in progress; routing open

This directory contains the reviewed value-bearing FB-100 KiCad schematic and
project-local symbol/footprint libraries.

The controlled `FB-100.kicad_pcb` placement is generated from the frozen
44-component schematic and project-local footprints. Mechanical-envelope and
USB/no-back-power inputs are applied, while routing, copper pours, stackup-
specific USB impedance work, and final silkscreen remain open. There are no
manufacturing outputs: Gerbers, drills, pick-place files, BOM/CPL order
packages, zipped fabrication packages, and board orders remain blocked until
the later prototype/production gates close.

Release boundary: no manufacturing outputs are authorized.

## Source Documents

- `../FB-100-requirements.md`
- `../FB-100-schematic-freeze-checklist.md`
- `../FB-100-pcb-layout-start-checklist.csv`
- `../FB-100-footprint-binding-inventory.csv`
- `../FB-100-footprint-binding-closeout.csv`
- `../FB-100-footprint-binding-closeout.md`
- `../FB-100-mechanical-envelope-inventory.csv`
- `../FB-100-mechanical-layout-inputs.csv`
- `../FB-100-usb-no-back-power-layout-rules.csv`
- `../FB-100-board-release-blocker-register.csv`
- `../../../../production/board-order/three_board_footprint_binding_status.csv`
- `../../../../production/board-order/three_board_mechanical_envelope_status.csv`
- `../../../logic-board/LB-100/LB-100-requirements.md`
- `../../../../docs/adr/ADR-0014-lb-fb-baseline-requirements.md`
