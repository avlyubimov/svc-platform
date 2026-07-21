# FB-100 Controlled Layout Progress

Status: `LAYOUT-ONLY` — board import and constrained placement started

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
- Added deterministic generation and CI validation. KiCad 10.0.4 reports no
  placement shorts, accidental clearance violations, or courtyard overlaps.
- The placement milestone intentionally retains 103 unrouted connectivity
  findings. The only accepted DRC geometry exceptions are the two USB-C shell
  stakes entering the X=0 board edge; the only connector-library warnings are
  the generated local overrides for J1, J2, and JFB1.
- Schematic parity is exact apart from H1-H4, which are board-only mechanical
  mounting holes.

## Open Layout Work

- Review JFB1 mating-side/reverse FFC orientation against the future LB-100
  placement before any prototype package is authorized.
- Route USB-C to D1 and D1 to JFB1 as a continuous referenced differential
  pair with no avoidable stubs, at most 1.0 mm length mismatch, and stackup-
  derived impedance confirmation.
- Route CC, VBUS detect-only, RGB, buttons, OLED-DNP, indicators, power, and
  ground; add the reviewed shield/ESD return and ground reference strategy.
- Add ground pours only after the USB return paths and no-back-power topology
  have been reviewed in the routed board.
- Complete placement clearance, silkscreen, courtyard, assembly-orientation,
  DFM, and final DRC review.

## Release Boundary

This milestone is a controlled layout artifact only. It does not authorize or
create Gerbers, drill files, BOM/CPL, pick-and-place, panel files,
manufacturing ZIPs, fabrication packages, PCBA orders, production release, or
field use. FB-100 remains `LAYOUT-ONLY` and order state remains `NO-GO`.
