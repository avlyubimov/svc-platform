# LB-100 KiCad Project

Status: `EVT-LAYOUT-AUTHORIZED`; controlled placement and first routing iteration exist

This directory contains the reviewed value-bearing LB-100 KiCad schematic and
project-local symbol/footprint libraries.

The controlled `LB-100.kicad_pcb` contains all 104 value-bearing schematic
footprints, four shared stack holes, four local mounting holes, the reviewed
100 mm x 70 mm outline and functional placement zones. The deterministic route
manifest currently contains 1,844 segments and 188 vias, leaving 63 source
connections open before refill and 53 after refill with no shorts, crossings,
copper-clearance or E73 keepout violations. Four GND-zone intents and the exact
four-copper-layer antenna rule area are present. It is not a
fabrication-ready board. Five non-assembly top-side pads provide E73 SWDIO,
SWDCLK, reset, switched target reference and GND recovery access. ADR-0020
authorizes continued routing. Signal-integrity and safety constraints in
`../LB-100-pcb-layout-start-checklist.csv` must close during
`EVT-FAB-REVIEW`. There are no manufacturing outputs; Gerbers, drills,
pick-place files, BOM/CPL order packages and
zipped manufacturing outputs remain blocked until `EVT-FAB-AUTHORIZED`.

Validation: `python3 tools/validate_lb100_layout.py` checks deterministic
generation, exact schematic parity, four-layer placement, the 104+8 footprint
count, both pre/post-refill routing facts, VEML7700 Rev.1 disposition, E73 rule
geometry and absence of unsafe copper/clearance/keepout collisions.

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
