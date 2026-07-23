# LB-100 KiCad Project

Status: `EVT-FAB-AUTHORIZED`; connectivity-complete six-layer Rev.1 EVT layout

This directory contains the reviewed value-bearing LB-100 schematic,
project-local libraries and deterministically generated PCB.

The controlled `LB-100.kicad_pcb` contains all 104 schematic footprints, eight mounting
holes, the 100 mm x 70 mm outline, 2,274 routed segments, 409 standard
0.50/0.30 mm through vias and four GND zones. KiCad 10.0.4 refill DRC reports
zero errors and zero unconnected items; parity contains only H1-H8. Five
non-assembly pads provide E73 SWDIO, SWDCLK, reset, switched target reference
and GND recovery access.

The six-layer stack model is JLCPCB `JLC06161H-3313`. In2.Cu and In4.Cu are
solid GND reference planes, In1.Cu and In3.Cu carry signals, and the E73 rule
area covers every copper layer. The routing manifest is the source for board
generation; do not hand-edit generated copper.

Validation with KiCad 10.0.4:

```sh
python3 tools/validate_lb100_layout.py
```

The validator checks deterministic generation, schematic parity, route/via
counts, standard through-via construction, reference-plane exclusivity, USB
geometry and analytical impedance regression, VEML7700 disposition, the
six-layer E73 keepout and the exact reviewed non-electrical warning set.

Any EVT fabrication package must remain LB-only, marked
`LB-100 REV.1 EVT - NOT FOR PRODUCTION`, and must pass the supplier stackup,
impedance and DFM preflight before payment. PB-100 and the combined three-board
order remain `NO-GO`. Authorized LB manufacturing outputs are segregated under
`../manufacturing/evt-rev1/`; no assembly outputs are authorized.

## Source documents

- `../LB-100-layout-progress.md`
- `../LB-100-evt-fab-review-2026-07-22.md`
- `../LB-100-e73-antenna-keepout.md`
- `../LB-100-pcb-layout-start-checklist.csv`
- `../../../../production/board-order/three_board_layout_rules.md`
- `../../../../docs/adr/ADR-0014-lb-fb-baseline-requirements.md`
