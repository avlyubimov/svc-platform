# LB-100 KiCad Project

Status: `EVT-LAYOUT-AUTHORIZED`; controlled placement exists; routing open

This directory contains the reviewed value-bearing LB-100 KiCad schematic and
project-local symbol/footprint libraries.

The controlled `LB-100.kicad_pcb` contains all 83 value-bearing schematic
footprints, four shared stack holes, four local mounting holes, the reviewed
100 mm x 70 mm outline and functional placement zones. It is a deterministic
placement milestone, not a routed or fabrication-ready board. ADR-0020 authorizes
continued placement and routing. Signal-integrity and safety constraints in
`../LB-100-pcb-layout-start-checklist.csv` must close during
`EVT-FAB-REVIEW`. There are no manufacturing outputs; Gerbers, drills,
pick-place files, BOM/CPL order packages and
zipped manufacturing outputs remain blocked until `EVT-FAB-AUTHORIZED`.

Validation: `python3 tools/validate_lb100_layout.py` checks deterministic
generation, exact schematic parity, four-layer placement, the 83+8 footprint
count, absence of routing and absence of copper/clearance/courtyard collisions.

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
