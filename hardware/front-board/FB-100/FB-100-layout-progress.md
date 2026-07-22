# FB-100 Controlled Layout Progress

Status: `EVT-LAYOUT-AUTHORIZED` — connectivity routing complete; fab review open

## Completed Milestone

- Created the deterministic `kicad/FB-100.kicad_pcb` board import from the
  frozen 44-component schematic and project-local footprints.
- Applied the reviewed 80.0 mm x 35.0 mm outline and four 2.7 mm NPTH M2.5
  holes at `(5,5)`, `(75,5)`, `(5,30)`, and `(75,30)`.
- Placed the USB-C receptacle at the X=0 service edge and kept USB ESD plus CC,
  shield, and defined-low VBUS-detect passives in the connector-side zone.
- Placed the rear/internal JFB1 FFC connector on the back side at the X=80
  cable edge and retained pins 4/5 for `USB_D_P` / `USB_D_N`.
- Applied the role-free STATUS and CH1..CH10 optical grid, SERVICE/RESET
  actuator targets, optional OLED DNP window, panel openings, and cable-bend
  review graphics.
- Added board-specific minimum clearance, track-width, and USB differential-
  pair rules in `kicad/FB-100.kicad_dru`.
- Repositioned the USB ESD/passive cluster and RGB driver support parts to
  provide manufacturable fan-out without changing the outline, optical grid,
  USB panel datum, FFC datum, or mounting holes.
- Routed every electrical connection with 438 straight segments and 39
  through vias. The routing is stored in `kicad/FB-100-routing.csv` and remains
  deterministic under CI regeneration.
- KiCad 10.0.4 reports zero unconnected items, shorts, track crossings, and
  copper-clearance violations. The remaining findings are explicitly open
  fab-review work: USB differential gap/uncoupled length, five courtyard
  overlaps, three silkscreen clips, the USB shell/route edge-entry exceptions,
  and generated local connector overrides.
- Schematic parity is exact apart from H1-H4, which are board-only mechanical
  mounting holes.

## Open Layout Work

- Review JFB1 mating-side/reverse FFC orientation against the future LB-100
  placement before any prototype package is authorized.
- Route USB-C to D1 and D1 to JFB1 as a continuous referenced differential
  pair with no avoidable stubs, at most 1.0 mm length mismatch, and stackup-
  derived impedance confirmation.
- Tune the routed USB pair for the selected stackup, continuous reference,
  gap, impedance and length match; the current autorouted pair is connectivity
  complete but intentionally not impedance-qualified.
- Resolve the five courtyard overlaps and three silkscreen clips without
  changing the frozen mechanical datums.
- Review the routed CC, VBUS detect-only, RGB, buttons, OLED-DNP, indicator,
  power, ground, shield and ESD return paths before pours are added.
- Add ground pours only after the USB return paths and no-back-power topology
  have been reviewed in the routed board.
- Complete placement clearance, silkscreen, courtyard, assembly-orientation,
  DFM, and final DRC review.

## Release Boundary

This milestone is a controlled layout artifact only. It does not authorize or
create Gerbers, drill files, BOM/CPL, pick-and-place, panel files,
manufacturing ZIPs, fabrication packages, PCBA orders, production release, or
field use. FB-100 remains `EVT-LAYOUT-AUTHORIZED` and order state remains
`NO-GO` until a separate `EVT-FAB-REVIEW` closes.
